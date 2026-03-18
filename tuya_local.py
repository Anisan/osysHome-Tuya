"""
Tuya Local LAN control client
Uses tinytuya for direct device communication without cloud
"""

import logging
import time
import tinytuya
from typing import Dict, Optional, List, Any


class TuyaLocalClient:
    """Wrapper for tinytuya local LAN control"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize Tuya Local client
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.devices: Dict[str, tinytuya.Device] = {}
        self._device_configs: Dict[str, Dict] = {}
        self.socket_timeout = 8
        self.retryable_errors = {"904", "905", "914"}
        # Some Tuya firmwares return stale DPS over long-lived sockets.
        # Default to non-persistent sockets for fresher status reads.
        self.socket_persistent = False
        # Heuristic: if the full DPS dict repeats N times, force a reconnect and retry once.
        self.stale_repeat_threshold = 3
        self._last_dps: Dict[str, Dict[str, Any]] = {}
        self._repeat_count: Dict[str, int] = {}

    def _create_device(self, device_id: str, ip: str, local_key: str, version: str) -> tinytuya.Device:
        """Create a configured tinytuya device instance."""
        device = tinytuya.Device(device_id, ip, local_key, version=version)
        device.set_socketPersistent(bool(self.socket_persistent))
        device.set_socketTimeout(self.socket_timeout)
        return device

    def _close_device(self, device_id: str):
        """Close active socket for a device if present."""
        device = self.devices.get(device_id)
        if not device:
            return
        try:
            device.close()
        except Exception:
            pass

    def _is_retryable_error(self, result: Any) -> bool:
        """Return True for transient tinytuya errors that benefit from reconnect."""
        if not isinstance(result, dict):
            return False
        err = str(result.get("Err") or "").strip()
        if err in self.retryable_errors:
            return True
        error_text = str(result.get("Error") or "").lower()
        return any(code in error_text for code in ("unexpected payload", "device unreachable", "check device key or version"))

    def _log_device_failure(self, action: str, device_id: str, detail: Any, *, retryable: bool = False):
        """Log transient device failures as debug and unexpected ones as warning."""
        log_fn = self.logger.debug if retryable else self.logger.warning
        log_fn("%s %s failed: %s", action, device_id, detail)

    def _reconnect_device(self, device_id: str) -> Optional[tinytuya.Device]:
        """Recreate the tinytuya device to recover from stale/broken sockets."""
        config = self._device_configs.get(device_id)
        if not config:
            return None
        self._close_device(device_id)
        try:
            device = self._create_device(
                device_id,
                config["ip"],
                config["local_key"],
                config["version"],
            )
            self.devices[device_id] = device
            self.logger.debug(
                "Reconnected local device %s at %s (protocol=%s)",
                device_id,
                config["ip"],
                config["version"],
            )
            return device
        except Exception as e:
            self.logger.warning("Failed to reconnect local device %s: %s", device_id, e)
            self.devices.pop(device_id, None)
            return None
        
    def add_device(self, device_id: str, ip: str, local_key: str, version: str = "3.3") -> bool:
        """
        Add a device for local control
        
        Args:
            device_id: Device ID
            ip: Device IP address
            local_key: Device local key
            version: Protocol version (3.1, 3.3, 3.4 or 3.5)
            
        Returns:
            True if device added successfully
        """
        try:
            self._device_configs[device_id] = {
                "ip": ip,
                "local_key": local_key,
                "version": version
            }
            self._close_device(device_id)
            self.devices[device_id] = self._create_device(device_id, ip, local_key, version)
            
            self.logger.info("Added local device %s at %s (protocol=%s)", device_id, ip, version)
            return True
            
        except Exception as e:
            self.logger.error("Failed to add device %s: %s", device_id, e)
            return False
    
    def remove_device(self, device_id: str):
        """Remove device from local control"""
        if device_id in self.devices:
            self._close_device(device_id)
            del self.devices[device_id]
            
        if device_id in self._device_configs:
            del self._device_configs[device_id]
    
    def get_device(self, device_id: str) -> Optional[tinytuya.Device]:
        """Get device instance"""
        return self.devices.get(device_id)
    
    def update_device_ip(self, device_id: str, new_ip: str) -> bool:
        """
        Update device IP address
        
        Args:
            device_id: Device ID
            new_ip: New IP address
            
        Returns:
            True if updated successfully
        """
        if device_id not in self._device_configs:
            return False
        
        config = self._device_configs[device_id]
        self.remove_device(device_id)
        return self.add_device(device_id, new_ip, config["local_key"], config["version"])
    
    def get_status(self, device_id: str) -> Dict[str, Any]:
        """
        Get device status (DPS values)
        
        Args:
            device_id: Device ID
            
        Returns:
            Dictionary of DPS values {dp_id: value}
        """
        device = self.devices.get(device_id)
        if not device:
            self.logger.error("Device %s not found in local client", device_id)
            return {}
        
        started_at = time.monotonic()
        for attempt in range(2):
            attempt_started_at = time.monotonic()
            try:
                status = device.status()
            except Exception as e:
                self._log_device_failure(
                    f"get_status attempt {attempt + 1}",
                    device_id,
                    e,
                    retryable=(attempt == 0),
                )
                status = {"Error": str(e), "Err": "exception", "Payload": None}
            attempt_elapsed = time.monotonic() - attempt_started_at

            if not status or 'dps' not in status:
                retryable = self._is_retryable_error(status)
                if attempt == 0 and retryable:
                    self.logger.debug(
                        "get_status %s: retrying after transient error in %.3fs: %s",
                        device_id,
                        attempt_elapsed,
                        status,
                    )
                    device = self._reconnect_device(device_id)
                    if device:
                        continue
                self._log_device_failure(
                    "get_status",
                    device_id,
                    f"no DPS, raw response: {status}",
                    retryable=retryable,
                )
                self.logger.debug(
                    "get_status %s: finished without DPS in %.3fs after %d attempt(s)",
                    device_id,
                    time.monotonic() - started_at,
                    attempt + 1,
                )
                return {}
            
            dps = status['dps']
            # B) Stale-DPS mitigation: if the device keeps returning the exact same DPS
            # for multiple polls, reconnect and try once to refresh.
            try:
                prev_dps = self._last_dps.get(device_id)
                if prev_dps is not None and dps == prev_dps:
                    self._repeat_count[device_id] = self._repeat_count.get(device_id, 0) + 1
                else:
                    self._repeat_count[device_id] = 0
                self._last_dps[device_id] = dict(dps) if isinstance(dps, dict) else dps

                if self._repeat_count.get(device_id, 0) >= int(self.stale_repeat_threshold):
                    self.logger.debug(
                        "get_status %s: DPS repeated %d times; forcing reconnect to refresh",
                        device_id,
                        self._repeat_count[device_id],
                    )
                    device = self._reconnect_device(device_id)
                    if device:
                        try:
                            refreshed = device.status()
                        except Exception as e:
                            refreshed = {"Error": str(e), "Err": "exception", "Payload": None}
                        if refreshed and isinstance(refreshed, dict) and 'dps' in refreshed:
                            dps2 = refreshed['dps']
                            self.logger.debug(
                                "get_status %s: refreshed DPS after reconnect: %s",
                                device_id,
                                dps2,
                            )
                            dps = dps2
                            self._last_dps[device_id] = dict(dps2) if isinstance(dps2, dict) else dps2
                            self._repeat_count[device_id] = 0
            except Exception:
                # Never break polling because of stale mitigation bookkeeping.
                pass

            self.logger.debug(
                "get_status %s: success in %.3fs on attempt %d, dps=%s (full: %s)",
                device_id,
                time.monotonic() - started_at,
                attempt + 1,
                dps,
                status,
            )
            return dps
        return {}
    
    def _normalize_dp_value(self, value: Any, _dp_id: int = None) -> Any:
        """
        Normalize value for Tuya protocol.
        Switch DPS often expect bool (True/False), not int 0/1 — especially for protocol 3.4+.
        """
        if value in (0, "0", False):
            return False
        if value in (1, "1", True):
            return True
        return value

    def set_dp(self, device_id: str, dp_id: int, value: Any) -> bool:
        """
        Set a single data point value
        
        Args:
            device_id: Device ID
            dp_id: Data point ID (integer)
            value: Value to set
            
        Returns:
            True if command sent successfully
        """
        device = self.devices.get(device_id)
        if not device:
            self.logger.error("Device %s not found in local client", device_id)
            return False
        
        # Normalize switch/boolean values — Tuya 3.4+ often expects bool
        normalized = self._normalize_dp_value(value, dp_id)
        if isinstance(normalized, bool):
            self.logger.debug("set_dp %s dp=%s: normalized value %s -> bool %s",
                              device_id, dp_id, value, normalized)
        
        for attempt in range(2):
            if attempt > 0:
                device = self.devices.get(device_id)
                if not device:
                    return False
            try:
                result = device.set_value(dp_id, normalized)
            except Exception as e:
                self._log_device_failure(
                    f"set_dp {device_id} dp={dp_id} attempt {attempt + 1}",
                    device_id,
                    e,
                    retryable=(attempt == 0),
                )
                result = {"Error": str(e), "Err": "exception", "Payload": None}
            ok = not (isinstance(result, dict) and (result.get("Error") or result.get("Err")))
            err_code = result.get("Error") or result.get("Err") if isinstance(result, dict) else None
            self.logger.debug("set_dp %s dp=%s value=%s -> ok=%s, result=%s",
                              device_id, dp_id, value, ok, result)
            if not ok and err_code is not None:
                self.logger.debug("  device error response: Error=%s Err=%s (full=%s)",
                                  result.get("Error"), result.get("Err"), result)
            if not ok and attempt == 0 and self._is_retryable_error(result):
                self.logger.debug(
                    "set_dp %s dp=%s: reconnecting after transient error",
                    device_id,
                    dp_id,
                )
                if self._reconnect_device(device_id):
                    continue
            if isinstance(result, dict) and (result.get("Error") or result.get("Err")):
                return False
            return True
        return False
    
    def set_multiple_dps(self, device_id: str, dps: Dict[int, Any]) -> bool:
        """
        Set multiple data points at once
        
        Args:
            device_id: Device ID
            dps: Dictionary of {dp_id: value}
            
        Returns:
            True if command sent successfully
        """
        device = self.devices.get(device_id)
        if not device:
            self.logger.error("Device %s not found in local client", device_id)
            return False
        
        for attempt in range(2):
            if attempt > 0:
                device = self.devices.get(device_id)
                if not device:
                    return False
            try:
                result = device.set_multiple_values(dps)
            except Exception as e:
                self._log_device_failure(
                    f"set_multiple_dps attempt {attempt + 1}",
                    device_id,
                    e,
                    retryable=(attempt == 0),
                )
                result = {"Error": str(e), "Err": "exception", "Payload": None}
            ok = not (isinstance(result, dict) and (result.get("Error") or result.get("Err")))
            self.logger.debug("set_multiple_dps %s dps=%s -> ok=%s, result=%s",
                              device_id, dps, ok, result)
            if not ok and isinstance(result, dict):
                self.logger.debug("  device error: Error=%s Err=%s", result.get("Error"), result.get("Err"))
            if not ok and attempt == 0 and self._is_retryable_error(result):
                self.logger.debug(
                    "set_multiple_dps %s: reconnecting after transient error",
                    device_id,
                )
                if self._reconnect_device(device_id):
                    continue
            if isinstance(result, dict) and (result.get("Error") or result.get("Err")):
                return False
            return True
        return False
    
    def scan_local(self, timeout: int = 18) -> List[Dict]:
        """
        Scan local network for Tuya devices
        
        Args:
            timeout: Scan timeout in seconds
            
        Returns:
            List of discovered devices with IP and ID
        """
        try:
            self.logger.info("Scanning local network for Tuya devices (timeout=%ds)...", timeout)
            devices = tinytuya.deviceScan(verbose=False, maxretry=timeout)
            
            result = []
            for _key, device_info in devices.items():
                # tinytuya may use IP as dict key; use id/gwId from response for device_id
                dev_id = device_info.get("id") or device_info.get("gwId") or device_info.get("ip") or _key
                item = {
                    "id": dev_id,
                    "ip": device_info.get("ip"),
                    "version": device_info.get("version", "3.3"),
                    "name": device_info.get("name") or "Unknown"
                }
                result.append(item)
                self.logger.debug("Scan found: id=%s ip=%s version=%s name=%s",
                                  dev_id, item["ip"], item["version"], item["name"])
                self.logger.debug("  device raw response: %s", device_info)
            
            self.logger.info("Scan complete: found %d devices", len(result))
            for d in result:
                self.logger.debug("  - %s ip=%s version=%s name=%s", d["id"], d["ip"], d["version"], d["name"])
            return result
            
        except Exception as e:
            self.logger.error("Error scanning local network: %s", e)
            return []
    
    def detect_device(self, device_id: str) -> Optional[Dict]:
        """
        Detect a specific device on the network by ID
        
        Args:
            device_id: Device ID to find
            
        Returns:
            Device info dict if found
        """
        devices = self.scan_local()
        for device in devices:
            if device["id"] == device_id:
                return device
        return None
    
    def test_connection(self, device_id: str) -> bool:
        """
        Test connection to a device
        
        Args:
            device_id: Device ID
            
        Returns:
            True if device responds
        """
        device = self.devices.get(device_id)
        if not device:
            return False
        
        try:
            status = device.status()
            return status is not None and 'dps' in status
        except Exception:
            return False
    
    def close_all(self):
        """Close all device connections"""
        for _, device in list(self.devices.items()):
            try:
                device.close()
            except Exception:
                pass
        
        self.devices.clear()
        self._device_configs.clear()
        self.logger.info("Closed all local device connections")
