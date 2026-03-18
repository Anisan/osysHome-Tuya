"""
Tuya Plugin for osysHome
Integrates Tuya ecosystem devices with cloud and local control
"""

import threading
import time
import colorsys
from datetime import datetime
from typing import Dict, List, Optional
from flask import request, jsonify

from app.core.MonitoredThreadPool import MonitoredThreadPool
from app.core.main.BasePlugin import BasePlugin
from app.core.lib.object import updateProperty, setLinkToObject
from app.core.lib.constants import PropertyType
from app.authentication.handlers import handle_admin_required
from app.database import session_scope
from plugins.Tuya.models import TuyaDevice, TuyaDeviceProperty
from plugins.Tuya.tuya_cloud import TuyaCloudClient
from plugins.Tuya.tuya_local import TuyaLocalClient
from plugins.Tuya.tuya_uncover import get_devices_with_keys, VENDORS, UncoverAuthError, UncoverError
from plugins.Tuya.tuya_devices import TuyaDPSReference
from plugins.Tuya.forms.SettingForms import SettingsForm, AddDeviceForm


class Tuya(BasePlugin):
    """Tuya smart home integration plugin"""
    
    def __init__(self, app):
        super().__init__(app, __name__)
        
        self.title = "Tuya"
        self.description = "Tuya smart home device integration"
        self.category = "Devices"
        self.author = "Eraser"
        self.version = "0.1-alpha"
        self.actions = ['cycle', 'search', 'widget']
        
        self.cloud_client: Optional[TuyaCloudClient] = None
        self.local_client: Optional[TuyaLocalClient] = None
        self.dps_ref: Optional[TuyaDPSReference] = None
        self._lock = threading.Lock()
        self._cloud_poll_lock = threading.Lock()
        self._poll_workers = max(2, int(self.config.get('poll_workers', 4) or 4))
        self._poll_pool = MonitoredThreadPool(
            max_workers=self._poll_workers,
            thread_name_prefix=f"{self.name}_poll",
        )
        # In-memory DPS cache: {device_id: {str(dp_id): {'value': v, 'updated_at': datetime}}}
        self._dps_cache: Dict[str, Dict[str, dict]] = {}
        # Fail counter for online hysteresis: mark offline only after N consecutive poll failures
        self._online_fail_count: Dict[str, int] = {}
        self._online_fail_threshold = 2  # require 2+ consecutive failures before marking offline
        
    def initialization(self):
        """Initialize plugin and connect to Tuya"""
        self.logger.info("Initializing Tuya plugin")
        
        self.dps_ref = TuyaDPSReference(logger=self.logger)
        
        access_id = self.config.get('access_id')
        access_secret = self.config.get('access_secret')
        region = self.config.get('region', 'eu')
        connection_mode = self.config.get('connection_mode', 'both')
        
        if connection_mode in ['cloud', 'both']:
            if access_id and access_secret:
                linked_uid = self.config.get('linked_uid', '').strip() or None
                self._init_cloud_client(access_id, access_secret, region, linked_uid)
            else:
                self.logger.warning("Cloud mode selected but credentials not configured")
        
        if connection_mode in ['local', 'both']:
            self._init_local_client()
        
        # Load devices from DB and register with local client
        devices = self._db_get_all_devices()
        for dev in devices:
            if dev.get('enabled', True):
                self._register_device_locally(dev)
        
        self.logger.info(f"Tuya plugin initialized with {len(devices)} devices")
    
    # ── DB helpers ──────────────────────────────────────────────────────

    def _db_get_all_devices(self) -> list:
        with session_scope() as session:
            return [d.to_dict() for d in session.query(TuyaDevice).all()]

    def _normalize_protocol_version(self, info: dict) -> Optional[str]:
        """Extract protocol version from device info. Cloud: protocol_version, version; Scan: version."""
        v = info.get('protocol_version') or info.get('version') or info.get('protocol')
        if v is None:
            return None
        v = str(v).strip()
        if v in ('3.1', '3.3', '3.4', '3.5'):
            return v
        return None

    def _db_get_device(self, device_id: str) -> Optional[dict]:
        with session_scope() as session:
            dev = session.query(TuyaDevice).filter_by(device_id=device_id).one_or_none()
            return dev.to_dict() if dev else None

    def _db_upsert_device(self, info: dict) -> dict:
        """Insert or update a device row and return it as dict."""
        device_id = info.get('id') or info.get('device_id')
        if not device_id:
            raise ValueError("Device info must contain 'id' or 'device_id'")
        with session_scope() as session:
            dev = session.query(TuyaDevice).filter_by(device_id=device_id).one_or_none()
            pv = self._normalize_protocol_version(info)
            # Category reported by cloud / scan (may be unknown to our reference table)
            reported_category = info.get('category') or (dev.category if dev else None) or 'unknown'
            from plugins.Tuya.tuya_devices import TuyaDPSReference
            if reported_category not in TuyaDPSReference.CATEGORY_MAPPINGS:
                # Warning: helps to extend TuyaDPSReference with new categories seen from cloud
                self.logger.warning(
                    "Tuya: unknown device category from cloud/scan: device_id=%s category=%s name=%s",
                    device_id,
                    reported_category,
                    info.get('name') or (dev.name if dev else None) or device_id,
                )
            if dev:
                dev.name = info.get('name', dev.name)
                dev.category = info.get('category', dev.category)
                dev.ip = info.get('ip') or dev.ip
                dev.local_key = info.get('local_key') or dev.local_key
                dev.online = info.get('online', dev.online)
                if pv:
                    dev.protocol_version = pv
                dev.last_seen = datetime.utcnow()
            else:
                dev = TuyaDevice(
                    device_id=device_id,
                    name=info.get('name', device_id),
                    category=info.get('category', 'unknown'),
                    ip=info.get('ip'),
                    local_key=info.get('local_key'),
                    protocol_version=pv or info.get('protocol_version', '3.3'),
                    online=info.get('online', False),
                    discovered_at=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                )
                session.add(dev)
            session.flush()
            return dev.to_dict()

    def _db_delete_device(self, device_id: str):
        with session_scope() as session:
            dev = session.query(TuyaDevice).filter_by(device_id=device_id).one_or_none()
            if dev:
                session.delete(dev)

    def _db_get_links(self, device_id: str) -> list:
        with session_scope() as session:
            dev = session.query(TuyaDevice).filter_by(device_id=device_id).one_or_none()
            if dev:
                return [p.to_dict() for p in dev.properties]
            return []

    def _db_set_links(self, device_id: str, links: dict):
        """Save DPS-to-object links for a device.
        links = {dps_code: {dp_id, writable, linked_object, linked_property, linked_method, bidirectional}}
        """
        with session_scope() as session:
            dev = session.query(TuyaDevice).filter_by(device_id=device_id).one_or_none()
            if not dev:
                return

            session.query(TuyaDeviceProperty).filter_by(device_id=dev.id).delete()

            for dps_code, link_info in links.items():
                prop = TuyaDeviceProperty(
                    device_id=dev.id,
                    name=link_info.get('label', dps_code),
                    code=dps_code,
                    dp_id=link_info.get('dp_id'),
                    writable=link_info.get('writable', False),
                    linked_object=link_info.get('linked_object'),
                    linked_property=link_info.get('linked_property'),
                    linked_method=link_info.get('linked_method'),
                    bidirectional=link_info.get('bidirectional', False),
                )
                session.add(prop)

    # ── Client init ─────────────────────────────────────────────────────

    def _init_cloud_client(self, access_id: str, access_secret: str, region: str, linked_uid: str = None):
        """Initialize cloud client and Pulsar messaging"""
        try:
            self.cloud_client = TuyaCloudClient(
                access_id, access_secret, region,
                linked_uid=linked_uid, logger=self.logger
            )
            if self.cloud_client.connect():
                self.logger.info("Connected to Tuya Cloud")
                if self.cloud_client.start_mqtt(self._on_pulsar_message):
                    self.logger.info("Pulsar connection established")
                else:
                    self.logger.warning("Failed to start Pulsar")
            else:
                self.logger.error("Failed to connect to Tuya Cloud")
                self.cloud_client = None
        except Exception as e:
            self.logger.error(f"Error initializing cloud client: {e}")
            self.cloud_client = None
    
    def _init_local_client(self):
        """Initialize local LAN client"""
        try:
            self.local_client = TuyaLocalClient(logger=self.logger)
            self.logger.info("Local client initialized")
        except Exception as e:
            self.logger.error(f"Error initializing local client: {e}")
            self.local_client = None

    def _register_device_locally(self, dev: dict):
        """Register a device with the local tinytuya client if possible."""
        if self.local_client and dev.get('local_key') and dev.get('ip'):
            pv = dev.get('protocol_version', '3.3')
            self.local_client.add_device(dev['id'], dev['ip'], dev['local_key'], pv)
            self.logger.debug("Registered local device %s ip=%s protocol=%s",
                              dev['id'], dev['ip'], pv)

    # ── Pulsar / polling ────────────────────────────────────────────────

    def _on_pulsar_message(self, device_id: str, status: Dict):
        """Handle Pulsar push notification from cloud"""
        self.logger.debug(f"Pulsar update for {device_id}: {status}")
        try:
            self._set_device_online(device_id, True)
            self._apply_status(device_id, status)
        except Exception as e:
            self.logger.error(f"Error processing Pulsar message: {e}")

    def _set_device_online(self, device_id: str, online: bool):
        """Update online flag in DB and notify frontend via WebSocket."""
        with session_scope() as session:
            dev = session.query(TuyaDevice).filter_by(device_id=device_id).one_or_none()
            if dev and dev.online != online:
                dev.online = online
                if online:
                    dev.last_seen = datetime.utcnow()
                self.sendDataToWebsocket('device_update', {
                    'device_id': device_id,
                    'online': online,
                })

    def _update_dps_cache(self, device_id: str, status: dict):
        """Store DPS values in memory. Update timestamp only when value changes."""
        if not status:
            return
        now = datetime.utcnow()
        with self._lock:
            if device_id not in self._dps_cache:
                self._dps_cache[device_id] = {}
            for dp_key, value in status.items():
                k = str(dp_key)
                prev = self._dps_cache[device_id].get(k)
                updated_at = now if prev is None or prev.get('value') != value else prev.get('updated_at', now)
                self._dps_cache[device_id][k] = {'value': value, 'updated_at': updated_at}

    def _update_dps_cache_value(self, device_id: str, dp_id: int, value):
        """Update single DPS in cache (e.g. after optimistic command). Timestamp updates only when value changes."""
        now = datetime.utcnow()
        with self._lock:
            if device_id not in self._dps_cache:
                self._dps_cache[device_id] = {}
            k = str(dp_id)
            prev = self._dps_cache[device_id].get(k)
            updated_at = now if prev is None or prev.get('value') != value else prev.get('updated_at', now)
            self._dps_cache[device_id][k] = {'value': value, 'updated_at': updated_at}

    # ── DPS transformation helpers (protocol ↔ user units) ───────────────

    def _get_dps_meta(self, category: str, code: str) -> dict:
        """Return static metadata for given category/code from TuyaDPSReference."""
        if not self.dps_ref or not category or not code:
            return {}
        mapping = self.dps_ref.CATEGORY_MAPPINGS.get(category, {}).get("dps", {})
        return mapping.get(code, {})

    def _from_tuya_value(self, raw_value, meta: dict):
        """Convert raw DPS value from Tuya to user-facing value using meta (e.g. scale)."""
        if meta is None:
            meta = {}
        # Special converters first (non-numeric formats)
        converter = meta.get("converter")
        if converter == "hsv_v2_rgb_hex" and isinstance(raw_value, str):
            # Expect HHHHSSSSVVVV hex
            try:
                if len(raw_value) == 12:
                    h = int(raw_value[0:4], 16)
                    s = int(raw_value[4:8], 16)
                    v = int(raw_value[8:12], 16)
                    h_f = h / 360.0
                    s_f = s / 1000.0
                    v_f = v / 1000.0
                    r_f, g_f, b_f = colorsys.hsv_to_rgb(h_f, s_f, v_f)
                    r = int(round(r_f * 255))
                    g = int(round(g_f * 255))
                    b = int(round(b_f * 255))
                    return f"{r:02X}{g:02X}{b:02X}"
            except Exception:
                self.logger.debug("Tuya: failed to convert HSV v2 '%s' to RGB hex", raw_value)

        scale = meta.get("scale")
        if not scale:
            return raw_value
        try:
            if isinstance(raw_value, (int, float)):
                return raw_value / scale
            if isinstance(raw_value, str) and raw_value.replace(".", "", 1).isdigit():
                return float(raw_value) / scale
        except Exception:
            self.logger.debug("Tuya: failed to apply from_tuya scale=%s to value=%s", scale, raw_value)
        return raw_value

    def _to_tuya_value(self, user_value, meta: dict):
        """Convert user-facing value back to Tuya raw DPS (inverse of _from_tuya_value)
        and привести тип к тому, что ожидает спецификация (PropertyType)."""
        if meta is None:
            meta = {}
        # Special converters first
        converter = meta.get("converter")
        if converter == "hsv_v2_rgb_hex":
            # Expect user_value as RRGGBB or #RRGGBB; convert to HHHHSSSSVVVV
            try:
                if isinstance(user_value, str):
                    v = user_value.strip()
                    if v.startswith("#"):
                        v = v[1:]
                    if len(v) == 6:
                        r = int(v[0:2], 16)
                        g = int(v[2:4], 16)
                        b = int(v[4:6], 16)
                        r_f = r / 255.0
                        g_f = g / 255.0
                        b_f = b / 255.0
                        h_f, s_f, v_f = colorsys.rgb_to_hsv(r_f, g_f, b_f)
                        h = int(round(h_f * 360.0))
                        s = int(round(s_f * 1000.0))
                        v_int = int(round(v_f * 1000.0))
                        # Clamp to Tuya ranges
                        h = max(0, min(360, h))
                        s = max(0, min(1000, s))
                        v_int = max(0, min(1000, v_int))
                        return f"{h:04X}{s:04X}{v_int:04X}"
            except Exception:
                self.logger.debug("Tuya: failed to convert RGB hex '%s' to HSV v2", user_value)
            # If conversion fails, fall through and return original / scaled value below

        scale = meta.get("scale")
        value = user_value

        # 1) Сначала применяем масштаб, если он есть
        if scale:
            try:
                if isinstance(value, (int, float)):
                    value = value * scale
                elif isinstance(value, str) and value.replace(".", "", 1).isdigit():
                    value = float(value) * scale
            except Exception:
                self.logger.debug("Tuya: failed to apply to_tuya scale=%s to value=%s", scale, user_value)

        # 2) Затем приводим тип к типу из спецификации (PropertyType)
        ptype = meta.get("type")
        try:
            if isinstance(ptype, PropertyType):
                if ptype == PropertyType.Bool:
                    # Любые "0"/"1"/числа → bool
                    if isinstance(value, str) and value.isdigit():
                        value = bool(int(value))
                    else:
                        value = bool(value)
                elif ptype == PropertyType.Integer:
                    if isinstance(value, str) and value.replace(".", "", 1).isdigit():
                        value = int(round(float(value)))
                    else:
                        value = int(round(value))
                elif ptype == PropertyType.Float:
                    if isinstance(value, str) and value.replace(",", ".", 1).replace(".", "", 1).isdigit():
                        value = float(value.replace(",", ".", 1))
                    else:
                        value = float(value)
                elif ptype == PropertyType.String:
                    value = str(value)
                # Остальные типы (Json и т.п.) оставляем как есть
        except Exception:
            self.logger.debug("Tuya: failed to coerce type %s for value=%s", ptype, value)

        return value

    def _get_dps_for_display(self, device_id: str) -> Dict[str, dict]:
        """Get cached DPS for display: {str(dp_id): {value, updated_at}}."""
        with self._lock:
            return dict(self._dps_cache.get(device_id, {}))

    def _apply_status(self, device_id: str, status: dict):
        """Write Tuya DPS values to linked system object properties via DB links."""
        self._update_dps_cache(device_id, status)
        links = self._db_get_links(device_id)
        if not links:
            return
        dev_info = self._db_get_device(device_id)
        category = dev_info.get("category") if dev_info else None
        for link in links:
            code = link.get('code', '')
            target_obj = link.get('linked_object')
            target_prop = link.get('linked_property')
            if not target_obj or not target_prop:
                continue
            value = status.get(code)
            if value is None:
                value = status.get(str(link.get('dp_id', '')))
            if value is not None:
                meta = self._get_dps_meta(category, code)
                user_value = self._from_tuya_value(value, meta)
                self.logger.debug(
                    "_apply_status %s: %s.%s = %s (raw=%s, scale=%s, from DPS %s)",
                    device_id,
                    target_obj,
                    target_prop,
                    user_value,
                    value,
                    meta.get("scale"),
                    code,
                )
                updateProperty(f"{target_obj}.{target_prop}", user_value, source=self.name)

    def cyclic_task(self):
        """Periodically poll device status"""
        poll_interval = self.config.get('poll_interval', 30)
        while not self.event.is_set():
            started_at = time.monotonic()
            polled_devices = 0
            try:
                polled_devices = self._poll_devices()
            except Exception as e:
                self.logger.error(f"Error in cyclic task: {e}")
            elapsed = time.monotonic() - started_at
            self.logger.debug(
                "Poll cycle complete: devices=%d elapsed=%.3fs interval=%.3fs",
                polled_devices,
                elapsed,
                float(poll_interval),
            )
            self.event.wait(max(0.0, poll_interval - elapsed))
    
    def _poll_devices(self):
        started_at = time.monotonic()
        devices = self._db_get_all_devices()
        enabled_devices = [dev for dev in devices if dev.get('enabled', True)]
        if not enabled_devices:
            self.logger.debug("Poll batch: no enabled devices")
            return 0

        if len(enabled_devices) == 1:
            dev = enabled_devices[0]
            try:
                self._poll_device(dev)
            except Exception as e:
                self.logger.error(f"Error polling device {dev['id']}: {e}")
            elapsed = time.monotonic() - started_at
            self.logger.debug("Poll batch: devices=1 mode=serial elapsed=%.3fs", elapsed)
            return 1

        future_to_device = {}
        for dev in enabled_devices:
            try:
                future = self._poll_pool.submit(self._poll_device, f"poll_{dev['id']}", dev)
                future_to_device[future] = dev['id']
            except Exception as e:
                self.logger.error("Failed to submit poll task for %s: %s", dev['id'], e)

        for future, device_id in future_to_device.items():
            try:
                future.result()
            except Exception as e:
                self.logger.error("Error polling device %s: %s", device_id, e)

        self.logger.debug(
            "Poll batch: devices=%d mode=parallel workers=%d elapsed=%.3fs",
            len(enabled_devices),
            self._poll_workers,
            time.monotonic() - started_at,
        )
        return len(enabled_devices)

    def _get_cloud_status(self, device_id: str) -> Dict:
        """Serialize cloud fallback calls because the cloud client is shared across poll workers."""
        if not self.cloud_client:
            return {}
        with self._cloud_poll_lock:
            return self.cloud_client.get_device_status(device_id)

    def _handle_poll_result(self, device_id: str, source: Optional[str], status: Dict):
        """Apply online hysteresis and propagate status after a poll attempt."""
        got_status = bool(status)
        with self._lock:
            if got_status:
                self._online_fail_count[device_id] = 0
                should_show_online = True
            else:
                prev = self._online_fail_count.get(device_id, 0)
                self._online_fail_count[device_id] = prev + 1
                # Mark offline only after threshold consecutive failures; else keep current state
                should_show_online = None if self._online_fail_count[device_id] < self._online_fail_threshold else False
        if should_show_online is not None:
            self._set_device_online(device_id, should_show_online)
        self.logger.debug("Poll %s: source=%s, online=%s, status=%s",
                          device_id, source or "none", bool(status),
                          list(status.keys()) if status else status)

        if status:
            self._apply_status(device_id, status)

    def _poll_device_local(self, device_id: str) -> Dict:
        """Get local device status if local polling is available for this device."""
        if self.local_client and device_id in self.local_client.devices:
            status = self.local_client.get_status(device_id)
            if not status:
                self.logger.debug("Poll %s: local returned empty, trying cloud", device_id)
            return status
        return {}

    def _poll_device_cloud(self, device_id: str) -> Dict:
        """Get cloud status for a device as fallback or primary source."""
        return self._get_cloud_status(device_id) if self.cloud_client else {}

    def _poll_device_status(self, device_id: str) -> tuple[Dict, Optional[str]]:
        """Poll device status and return both payload and source."""
        started_at = time.monotonic()
        local_status = self._poll_device_local(device_id)
        if local_status:
            self.logger.debug(
                "Poll %s: local status ready in %.3fs",
                device_id,
                time.monotonic() - started_at,
            )
            return local_status, "local"

        local_elapsed = time.monotonic() - started_at
        cloud_status = self._poll_device_cloud(device_id)
        if cloud_status:
            self.logger.debug(
                "Poll %s: cloud fallback ready in %.3fs (local_wait=%.3fs)",
                device_id,
                time.monotonic() - started_at,
                local_elapsed,
            )
            return cloud_status, "cloud"
        self.logger.debug(
            "Poll %s: no status after %.3fs (local_wait=%.3fs)",
            device_id,
            time.monotonic() - started_at,
            local_elapsed,
        )
        return {}, None

    def _poll_device_error(self, device_id: str, e: Exception):
        """Log unexpected poll errors and update offline hysteresis."""
        self.logger.error("Error polling device %s: %s", device_id, e)
        self._handle_poll_result(device_id, None, {})

    def _poll_device_wrapper(self, dev: dict):
        """Poll one device and safely apply the result."""
        device_id = dev['id']
        try:
            status, source = self._poll_device_status(device_id)
            self._handle_poll_result(device_id, source, status)
        except Exception as e:
            self._poll_device_error(device_id, e)

    def _poll_device(self, dev: dict):
        self._poll_device_wrapper(dev)

    # ── Linked property handling ────────────────────────────────────────

    def changeLinkedProperty(self, obj, prop, value):
        """Handle property changes from linked system objects → send command to Tuya device.

        The system calls this when any property linked to this plugin changes.
        We look up which Tuya device + DPS code corresponds to this object.property.
        """
        self.logger.debug(f"Property change: {obj}.{prop} = {value}")

        with session_scope() as session:
            link = session.query(TuyaDeviceProperty).filter_by(
                linked_object=obj,
                linked_property=prop,
            ).first()
            if not link:
                self.logger.warning(f"No Tuya link for {obj}.{prop}")
                return

            dev = session.query(TuyaDevice).get(link.device_id)
            if not dev:
                return

            device_id = dev.device_id
            code = link.code
            dp_id = link.dp_id
            writable = link.writable

        if not writable:
            self.logger.debug(f"DPS '{code}' on {device_id} is read-only, ignoring")
            return

        dev_info = self._db_get_device(device_id)
        category = dev_info.get("category") if dev_info else None
        meta = self._get_dps_meta(category, code)
        tuya_value = self._to_tuya_value(value, meta)

        self.logger.debug(
            "Command: device=%s code=%s dp_id=%s value=%s -> tuya_value=%s (scale=%s, local_avail=%s, cloud_avail=%s)",
            device_id,
            code,
            dp_id,
            value,
            tuya_value,
            meta.get("scale"),
            bool(self.local_client and device_id in self.local_client.devices and dp_id is not None),
            bool(self.cloud_client and code),
        )

        success = False
        method_used = None
        if self.local_client and device_id in self.local_client.devices and dp_id is not None:
            self.logger.debug("Trying local set_dp first")
            success = self.local_client.set_dp(device_id, int(dp_id), tuya_value)
            method_used = "local" if success else None
            if not success:
                self.logger.debug("Local set_dp failed (see TuyaLocalClient debug), will try cloud")

        if not success and self.cloud_client and code:
            self.logger.debug("Trying cloud command")
            success = self._send_cloud_command(device_id, code, tuya_value)
            method_used = "cloud" if success else None

        if success:
            self.logger.info("Command sent to %s: %s=%s (method=%s)", device_id, code, value, method_used)
            with self._lock:
                self._online_fail_count[device_id] = 0
            self._set_device_online(device_id, True)
            self._update_dps_cache_value(device_id, int(dp_id), tuya_value)
            # Re-apply status so that linked properties receive normalized value
            self._apply_status(device_id, {code: tuya_value})
        else:
            self.logger.error("Failed to send command to %s: %s=%s (tried local=%s, cloud=%s)",
                              device_id, code, value,
                              bool(self.local_client and device_id in (self.local_client.devices or {})),
                              bool(self.cloud_client and code))

    # ── Command senders ─────────────────────────────────────────────────

    def _normalize_cloud_value(self, value, code: str):
        """Convert value for Tuya Cloud API - switch/boolean DPS expect bool, not 0/1."""
        if value in (0, "0"):
            return False
        if value in (1, "1"):
            return True
        return value

    def _send_cloud_command(self, device_id: str, code: str, value) -> bool:
        if not self.cloud_client:
            return False
        v = self._normalize_cloud_value(value, code)
        ok = self.cloud_client.send_commands(device_id, [{"code": code, "value": v}])
        self.logger.debug("Cloud command %s %s=%s -> %s", device_id, code, v, ok)
        return ok

    # ── Search / widget ─────────────────────────────────────────────────

    def search(self, query: str) -> List[Dict]:
        results = []
        with session_scope() as session:
            devices = session.query(TuyaDevice).filter(
                TuyaDevice.name.contains(query)
            ).all()
            for dev in devices:
                results.append({
                    'url': f'/admin/{self.name}',
                    'title': f"{dev.name} ({dev.category})",
                    'tags': [self.title, dev.category]
                })
        return results

    def widget(self) -> str:
        with session_scope() as session:
            total = session.query(TuyaDevice).count()
            online = session.query(TuyaDevice).filter_by(online=True).count()
        cloud_status = "Connected" if self.cloud_client and self.cloud_client.is_connected() else "Disconnected"
        local_status = "Enabled" if self.local_client else "Disabled"
        return f"""
        <div class="tuya-widget">
            <h4>{self.title}</h4>
            <p>Devices: {total} ({online} online)</p>
            <p>Cloud: {cloud_status}</p>
            <p>Local: {local_status}</p>
        </div>
        """

    # ── Admin page ──────────────────────────────────────────────────────

    def admin(self, request):
        settings_form = SettingsForm()
        add_device_form = AddDeviceForm()

        if request.method == 'GET':
            settings_form.access_id.data = self.config.get('access_id', '')
            settings_form.access_secret.data = self.config.get('access_secret', '')
            settings_form.region.data = self.config.get('region', 'eu')
            settings_form.connection_mode.data = self.config.get('connection_mode', 'both')
            settings_form.poll_interval.data = self.config.get('poll_interval', 30)
            settings_form.linked_uid.data = self.config.get('linked_uid', '')

        with session_scope() as session:
            devices = [d.to_dict() for d in session.query(TuyaDevice).all()]

        categories = self.dps_ref.get_all_categories() if self.dps_ref else {}

        context = {
            'settings_form': settings_form,
            'add_device_form': add_device_form,
            'devices': devices,
            'categories': categories,
            'cloud_connected': self.cloud_client and self.cloud_client.is_connected(),
            'local_enabled': self.local_client is not None,
        }
        return self.render('tuya_admin.html', context)

    # ── Routes ──────────────────────────────────────────────────────────

    def register_routes(self):
        super().register_routes()

        @self.blueprint.route(f"/{self.name}/devices", methods=['GET'])
        @handle_admin_required
        def list_devices():
            devices = self._db_get_all_devices()
            return jsonify({
                'success': True,
                'devices': devices,
                'cloud_connected': self.cloud_client and self.cloud_client.is_connected(),
                'local_enabled': self.local_client is not None,
            })

        @self.blueprint.route(f"/{self.name}/discover", methods=['POST'])
        @handle_admin_required
        def discover_devices():
            if not self.cloud_client:
                return jsonify({'success': False, 'message': 'Cloud not connected'})
            cloud_devices = self.cloud_client.get_devices()
            count = 0
            for cd in cloud_devices:
                device_id = cd.get('id') or cd.get('device_id')
                if not device_id:
                    self.logger.warning(f"Skipping device without id: {list(cd.keys())}")
                    continue
                info = self.cloud_client.get_device_info(device_id)
                if info:
                    dev_dict = self._db_upsert_device(info)
                    self._register_device_locally(dev_dict)
                    count += 1
                else:
                    # Use list item as fallback (often contains id, name, local_key, ip)
                    pv = self._normalize_protocol_version(cd)
                    fallback = {
                        'id': device_id,
                        'name': cd.get('name') or cd.get('device_name') or device_id,
                        'category': cd.get('category', 'unknown'),
                        'ip': cd.get('ip'),
                        'local_key': cd.get('local_key'),
                        'protocol_version': pv or '3.3',
                        'online': cd.get('online', False),
                    }
                    dev_dict = self._db_upsert_device(fallback)
                    self._register_device_locally(dev_dict)
                    count += 1
            if count == 0 and not cloud_devices:
                return jsonify({
                    'success': True,
                    'count': 0,
                    'hint': 'No devices from Cloud. 1) Ensure you linked your Tuya/Smart Life app (iot.tuya.com → Devices → Link Tuya App Account). 2) If already linked, add the linked app user UID in Settings → Linked App User UID (find it in iot.tuya.com → Devices).'
                })
            return jsonify({'success': True, 'count': count})

        @self.blueprint.route(f"/{self.name}/device/add", methods=['POST'])
        @handle_admin_required
        def add_device_manual():
            data = request.get_json()
            info = {
                'id': data.get('device_id'),
                'name': data.get('device_name'),
                'local_key': data.get('local_key'),
                'ip': data.get('ip_address'),
                'category': data.get('category', 'unknown'),
                'protocol_version': data.get('protocol_version', '3.3'),
            }
            dev_dict = self._db_upsert_device(info)
            self._register_device_locally(dev_dict)
            return jsonify({'success': True})

        @self.blueprint.route(f"/{self.name}/device/<device_id>", methods=['PUT'])
        @handle_admin_required
        def update_device(device_id):
            try:
                data = request.get_json()
                info = {
                    'id': device_id,
                    'name': data.get('device_name'),
                    'local_key': data.get('local_key'),
                    'ip': data.get('ip_address'),
                    'category': data.get('category'),
                    'protocol_version': data.get('protocol_version', '3.3'),
                }
                dev_dict = self._db_upsert_device(info)

                enabled = data.get('enabled', True)
                with session_scope() as session:
                    dev = session.query(TuyaDevice).filter_by(device_id=device_id).one_or_none()
                    if dev:
                        dev.enabled = enabled

                if enabled:
                    if self.local_client and device_id in self.local_client.devices:
                        self.local_client.remove_device(device_id)
                    self._register_device_locally(dev_dict)
                elif self.local_client:
                    self.local_client.remove_device(device_id)

                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error updating device {device_id}: {e}")
                return jsonify({'success': False, 'message': str(e)})

        @self.blueprint.route(f"/{self.name}/device/<device_id>", methods=['DELETE'])
        @handle_admin_required
        def delete_device(device_id):
            if self.local_client:
                self.local_client.remove_device(device_id)
            self._db_delete_device(device_id)
            return jsonify({'success': True})

        @self.blueprint.route(f"/{self.name}/scan_local", methods=['POST'])
        @handle_admin_required
        def scan_local_network():
            if not self.local_client:
                return jsonify({'success': False, 'message': 'Local client not initialized'})
            devices = self.local_client.scan_local()
            self.logger.debug("scan_local: found %d devices (ids=%s)",
                              len(devices), [d.get("id") for d in devices])
            return jsonify({'success': True, 'devices': devices})

        @self.blueprint.route(f"/{self.name}/sync_from_scan", methods=['POST'])
        @handle_admin_required
        def sync_from_scan():
            """Update existing devices' IP/protocol from scan, and add newly found devices."""
            if not self.local_client:
                return jsonify({'success': False, 'message': 'Local client not initialized'})
            scanned = self.local_client.scan_local()
            scan_by_id = {d['id']: d for d in scanned}
            db_devices = self._db_get_all_devices()
            db_ids = {d['id'] for d in db_devices}
            self.logger.debug("sync_from_scan: scanned %d devices, db has %d",
                              len(scanned), len(db_devices))
            updated = 0
            added = 0
            # Update existing devices
            for dev in db_devices:
                sid = dev.get('id')
                if sid not in scan_by_id:
                    self.logger.debug("sync_from_scan: %s not in scan, skip update", sid)
                    continue
                sc = scan_by_id[sid]
                pv = self._normalize_protocol_version(sc) or dev.get('protocol_version', '3.3')
                info = {
                    'id': sid,
                    'name': dev.get('name'),
                    'category': dev.get('category'),
                    'ip': sc.get('ip') or dev.get('ip'),
                    'local_key': dev.get('local_key'),
                    'protocol_version': pv,
                }
                self._db_upsert_device(info)
                if self.local_client and sid in self.local_client.devices:
                    self.local_client.remove_device(sid)
                self._register_device_locally(info)
                updated += 1
                self.logger.debug("sync_from_scan: updated %s ip=%s protocol=%s", sid, info['ip'], pv)
            # Add new devices found in scan
            for sid, sc in scan_by_id.items():
                if sid in db_ids:
                    continue
                pv = self._normalize_protocol_version(sc) or '3.3'
                info = {
                    'id': sid,
                    'name': sc.get('name') or sc.get('id', sid),
                    'category': 'unknown',
                    'ip': sc.get('ip'),
                    'local_key': None,
                    'protocol_version': pv,
                }
                self._db_upsert_device(info)
                if self.local_client:
                    self._register_device_locally(info)
                added += 1
                self.logger.debug("sync_from_scan: added %s ip=%s protocol=%s", sid, info['ip'], pv)
            return jsonify({'success': True, 'updated': updated, 'added': added})

        @self.blueprint.route(f"/{self.name}/uncover_keys", methods=['POST'])
        @handle_admin_required
        def uncover_keys():
            """Get local keys via Tuya OEM app credentials (no IoT Cloud). Credentials not stored."""
            try:
                data = request.get_json() or {}
                email = (data.get('email') or '').strip()
                password = data.get('password') or ''
                vendor = (data.get('vendor') or 'smartlife').strip().lower()
                region = (data.get('region') or 'eu').strip().lower()

                if not email or not password:
                    return jsonify({'success': False, 'message': 'Email and password required'})

                devices = get_devices_with_keys(
                    email, password, vendor=vendor, region=region, logger=self.logger
                )
                return jsonify({'success': True, 'devices': devices})
            except UncoverAuthError as e:
                return jsonify({'success': False, 'message': f'Authentication failed: {e}'})
            except UncoverError as e:
                return jsonify({'success': False, 'message': str(e)})
            except Exception as e:
                self.logger.exception("uncover_keys error")
                return jsonify({'success': False, 'message': str(e)})

        @self.blueprint.route(f"/{self.name}/apply_keys", methods=['POST'])
        @handle_admin_required
        def apply_keys():
            """Apply local_key from uncover result to existing devices. Expects {devices: [{id, local_key, ...}]}."""
            try:
                data = request.get_json() or {}
                devices = data.get('devices', [])
                updated = 0
                for d in devices:
                    dev_id = d.get('id')
                    local_key = d.get('local_key')
                    if not dev_id or not local_key:
                        continue
                    dev = self._db_get_device(dev_id)
                    if not dev:
                        continue
                    info = {
                        'id': dev_id,
                        'name': dev.get('name'),
                        'local_key': local_key,
                        'ip': dev.get('ip'),
                        'category': dev.get('category'),
                        'protocol_version': dev.get('protocol_version', '3.3'),
                    }
                    self._db_upsert_device(info)
                    if self.local_client and dev_id in self.local_client.devices:
                        self.local_client.remove_device(dev_id)
                    self._register_device_locally(info)
                    updated += 1
                return jsonify({'success': True, 'updated': updated})
            except Exception as e:
                self.logger.exception("apply_keys error")
                return jsonify({'success': False, 'message': str(e)})

        @self.blueprint.route(f"/{self.name}/uncover_vendors", methods=['GET'])
        @handle_admin_required
        def uncover_vendors():
            """List supported OEM vendors for uncover."""
            return jsonify({
                'success': True,
                'vendors': [{'id': k, 'brand': v['brand']} for k, v in sorted(VENDORS.items())]
            })

        @self.blueprint.route(f"/{self.name}/settings", methods=['POST'])
        @handle_admin_required
        def update_settings():
            try:
                data = request.get_json()
                self.config['access_id'] = data.get('access_id')
                self.config['access_secret'] = data.get('access_secret')
                self.config['region'] = data.get('region', 'eu')
                self.config['connection_mode'] = data.get('connection_mode', 'both')
                self.config['poll_interval'] = int(data.get('poll_interval', 30))
                self.config['linked_uid'] = (data.get('linked_uid') or '').strip() or None
                self.saveConfig()

                mode = self.config['connection_mode']
                if mode in ['cloud', 'both']:
                    if self.cloud_client:
                        self.cloud_client.disconnect()
                    linked_uid = self.config.get('linked_uid') or None
                    self._init_cloud_client(
                        self.config['access_id'],
                        self.config['access_secret'],
                        self.config['region'],
                        linked_uid,
                    )
                if mode in ['local', 'both'] and not self.local_client:
                    self._init_local_client()
                elif mode == 'cloud' and self.local_client:
                    self.local_client.close_all()
                    self.local_client = None
                return jsonify({
                    'success': True,
                    'message': 'Settings applied',
                    'cloud_connected': self.cloud_client and self.cloud_client.is_connected(),
                    'local_enabled': self.local_client is not None,
                })
            except Exception as e:
                self.logger.error(f"Error updating settings: {e}")
                return jsonify({'success': False, 'message': str(e)})

        @self.blueprint.route(f"/{self.name}/device/<device_id>/links", methods=['GET'])
        @handle_admin_required
        def get_device_links(device_id):
            try:
                dev = self._db_get_device(device_id)
                if not dev:
                    return jsonify({'success': False, 'message': 'Device not found'})

                category = dev.get('category', '')

                # Fetch fresh status when opening links (local or cloud)
                status = {}
                if self.local_client and device_id in self.local_client.devices:
                    status = self.local_client.get_status(device_id)
                if not status and self.cloud_client:
                    status = self.cloud_client.get_device_status(device_id)
                if status:
                    self._update_dps_cache(device_id, status)

                saved = {}
                for row in self._db_get_links(device_id):
                    saved[row['code']] = row

                dps_list = []
                dps_source = 'none'

                cloud_spec = None
                if self.cloud_client and self.cloud_client.is_connected():
                    cloud_spec = self.cloud_client.get_device_specification(device_id)

                if cloud_spec:
                    dps_source = 'cloud'
                    seen_codes = set()
                    func_codes = set()
                    for fn in cloud_spec.get('functions', []):
                        code = fn.get('code', '')
                        if code and code not in seen_codes:
                            seen_codes.add(code)
                            func_codes.add(code)
                            dps_list.append({
                                'code': code,
                                'dp_id': fn.get('dp_id'),
                                'type': fn.get('type', ''),
                                'writable': True,
                                'label': code,
                            })
                    for st in cloud_spec.get('status', []):
                        code = st.get('code', '')
                        if code and code not in seen_codes:
                            seen_codes.add(code)
                            dps_list.append({
                                'code': code,
                                'dp_id': st.get('dp_id'),
                                'type': st.get('type', ''),
                                'writable': False,
                                'label': code,
                            })

                    if self.dps_ref:
                        ref_dps = {d['code']: d for d in self.dps_ref.get_dps_for_category(category)}
                        for item in dps_list:
                            ref = ref_dps.get(item['code'])
                            if ref:
                                item['label'] = ref.get('label', item['code'])
                                if not item['dp_id']:
                                    item['dp_id'] = ref.get('dp_id')
                            else:
                                # Cloud reports DPS that we do not have in our local reference
                                # Log only in debug to help extend TuyaDPSReference when needed
                                self.logger.warning(
                                    "Tuya: unknown DPS code from cloud spec: device_id=%s category=%s code=%s dp_id=%s type=%s",
                                    device_id,
                                    category,
                                    item.get('code'),
                                    item.get('dp_id'),
                                    item.get('type'),
                                )

                if not dps_list and self.dps_ref:
                    dps_source = 'reference'
                    dps_list = self.dps_ref.get_dps_for_category(category)

                if not dps_list and saved:
                    dps_source = 'saved'
                    for code, row in saved.items():
                        dps_list.append({
                            'code': code,
                            'dp_id': row.get('dp_id'),
                            'type': '',
                            'writable': row.get('writable', False),
                            'label': row.get('name', code),
                        })

                dps_cache = self._get_dps_for_display(device_id)
                dps_with_links = []
                for dps in dps_list:
                    s = saved.get(dps['code'], {})
                    dps_writable = dps.get('writable', False)
                    saved_writable = s.get('writable', dps_writable)
                    dp_id = dps.get('dp_id')

                    # Try to find current value for this DPS in cache
                    cached = dps_cache.get(str(dp_id)) if dp_id is not None else None
                    if cached is None and dps.get('code'):
                        cached = dps_cache.get(dps['code'])

                    # Показываем только реально поддерживаемые DPS:
                    #  - либо есть в текущем статусе устройства (cached != None),
                    #  - либо уже есть сохранённая ссылка (чтобы не терять существующие бинды).
                    has_saved_link = bool(
                        s.get('linked_object') or s.get('linked_property') or s.get('linked_method')
                    )
                    if cached is None and not has_saved_link:
                        continue

                    current_value = cached.get('value') if cached else None
                    updated_at = cached.get('updated_at') if cached else None
                    last_changed = (
                        updated_at.isoformat() + 'Z'
                        if hasattr(updated_at, 'isoformat')
                        else (str(updated_at) if updated_at else None)
                    )

                    # Предварительный просмотр того, что реально уйдёт в связанное свойство
                    meta = self._get_dps_meta(category, dps['code'])
                    has_transform = bool(meta.get("scale") or meta.get("converter"))
                    if current_value is not None and has_transform:
                        converted_value = self._from_tuya_value(current_value, meta)
                    else:
                        converted_value = None

                    dps_with_links.append({
                        'code': dps['code'],
                        'dp_id': dp_id,
                        'type': dps.get('type', ''),
                        'writable': dps_writable,
                        'label': dps.get('label', dps['code']),
                        'linked_object': s.get('linked_object', ''),
                        'linked_property': s.get('linked_property', ''),
                        'linked_method': s.get('linked_method', ''),
                        'read_only': dps_writable and not saved_writable,
                        'current_value': current_value,
                        'converted_value': converted_value,
                        'last_changed': last_changed,
                    })

                # Если после фильтрации по статусу/ссылкам ничего не осталось,
                # всё равно отдадим все DPS из списка, чтобы можно было создать линк.
                if not dps_with_links and dps_list:
                    for dps in dps_list:
                        s = saved.get(dps['code'], {})
                        dps_writable = dps.get('writable', False)
                        saved_writable = s.get('writable', dps_writable)
                        dp_id = dps.get('dp_id')
                        meta = self._get_dps_meta(category, dps['code'])
                        has_transform = bool(meta.get("scale") or meta.get("converter"))
                        dps_with_links.append({
                            'code': dps['code'],
                            'dp_id': dp_id,
                            'type': dps.get('type', ''),
                            'writable': dps_writable,
                            'label': dps.get('label', dps['code']),
                            'linked_object': s.get('linked_object', ''),
                            'linked_property': s.get('linked_property', ''),
                            'linked_method': s.get('linked_method', ''),
                            'read_only': dps_writable and not saved_writable,
                            'current_value': None,
                            'converted_value': None if not has_transform else '',
                            'last_changed': None,
                        })

                category_label = ''
                if self.dps_ref:
                    category_label = self.dps_ref.get_category_label(category)

                return jsonify({
                    'success': True,
                    'device_name': dev.get('name', device_id),
                    'category': category,
                    'category_label': category_label,
                    'dps_list': dps_with_links,
                    'dps_source': dps_source,
                })
            except Exception as e:
                self.logger.error(f"Error getting device links: {e}")
                return jsonify({'success': False, 'message': str(e)})

        @self.blueprint.route(f"/{self.name}/device/<device_id>/links", methods=['POST'])
        @handle_admin_required
        def set_device_links(device_id):
            try:
                data = request.get_json()
                links = data.get('links', {})

                self._db_set_links(device_id, links)

                # Register system-level links so changeLinkedProperty gets called
                for code, link_info in links.items():
                    target_obj = link_info.get('linked_object')
                    target_prop = link_info.get('linked_property')
                    if target_obj and target_prop and link_info.get('writable'):
                        setLinkToObject(target_obj, target_prop, self.name)

                return jsonify({'success': True, 'message': 'Links saved'})
            except Exception as e:
                self.logger.error(f"Error setting device links: {e}")
                return jsonify({'success': False, 'message': str(e)})

    # ── Helpers ──────────────────────────────────────────────────────────

    def stop_cycle(self):
        super().stop_cycle()
        if self.cloud_client:
            self.cloud_client.disconnect()
        if self.local_client:
            self.local_client.close_all()
        if self._poll_pool:
            self._poll_pool.shutdown(wait=True)
