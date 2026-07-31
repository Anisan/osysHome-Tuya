"""MCP integration helpers for Tuya plugin."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import delete, or_

from app.core.lib.mcp_contract import (
    build_plugin_mcp_descriptors,
    revision_from_datetime,
    revision_from_dict,
    validate_entity_payload,
)
from app.core.lib.plugin_binding import (
    remove_property_link,
    sync_property_link,
    validate_object_exists,
    validate_object_property_exists,
)
from app.core.lib.object import setLinkToObject
from app.core.main.ObjectsStorage import objects_storage
from app.database import session_scope

from plugins.Tuya.models import TuyaDevice, TuyaDeviceProperty

DEVICES = "devices"
PROPERTIES = "properties"
PLUGIN_NAME = "Tuya"

_DEVICE_WRITABLE_FIELDS = (
    "device_id",
    "name",
    "category",
    "ip",
    "local_key",
    "protocol_version",
    "connection_mode",
    "enabled",
)
_PROPERTY_WRITABLE_FIELDS = (
    "device_id",
    "name",
    "code",
    "dp_id",
    "writable",
    "bidirectional",
    "linked_object",
    "linked_property",
    "linked_method",
)
_DEVICE_READONLY_FIELDS = (
    "id",
    "online",
    "has_local_key",
    "discovered_at",
    "last_seen",
)
_PROPERTY_READONLY_FIELDS = ("id",)

_PROTOCOL_VERSIONS = ("3.1", "3.3", "3.4", "3.5")
_CONNECTION_MODES = ("default", "cloud", "local", "both")

_PLUGIN_NOTES = [
    "Prefer discover + scan_local over inventing devices; manual create needs device_id and usually local_key + ip for LAN.",
    "Plugin connection_mode enables cloud/local clients; per-device connection_mode default|cloud|local|both "
    "(default = use module setting) controls poll and commands for that device.",
    "device_id is the Tuya cloud ID (immutable after create). MCP entity id is the internal DB primary key.",
    "local_key and access_secret are write-only: sent on upsert/config, never returned by list/get (see has_local_key).",
    "Properties are DPS bindings: code/dp_id identify the data point; linked_object+linked_property map into osysHome.",
    "writable=true allows outbound commands when the bound property changes; use writable=false for sensors (R/O).",
    "bidirectional marks two-way sync intent; reverse property link is registered when writable and linked.",
    "linked_method is optional and called on DPS updates when set.",
    "After cloud setup: invoke discover, then scan_local to fill IPs, then upsert properties for needed DPS.",
    "If discover returns 0 devices, set config.linked_uid (Smart Life / Tuya app user UID) and retry.",
    "prefer validate_entity before upsert when building property bindings.",
    "Use poll_now to refresh status; get_connection_status to check cloud/local readiness.",
]

_BINDING_PROMPT = "osys_tuya_binding"
_ENTITY_AUTHORING_PROMPT = "osys_tuya_entity_authoring"


def _plugin_instance():
    try:
        from app.core.main.PluginsHelper import plugins
        return plugins.get(PLUGIN_NAME, {}).get("instance")
    except Exception:
        return None


def validate_object_method_exists(object_name: Optional[str], method_name: Optional[str]) -> bool:
    obj_name = str(object_name or "").strip()
    meth_name = str(method_name or "").strip()
    if not obj_name or not meth_name:
        return False
    obj = objects_storage.getObjectByName(obj_name)
    if obj is None:
        return False
    return meth_name in getattr(obj, "methods", {})


def mcp_capabilities() -> dict:
    return {
        "mcp_version": 1,
        "entities": True,
        "config_schema": True,
        "notes": list(_PLUGIN_NOTES),
        "collections": [
            {
                "id": DEVICES,
                "title": "Tuya Devices",
                "binding_mode": "none",
                "writable": True,
                "has_code": False,
                "list_filters": ["query", "enabled", "online"],
                "default_sort": "name asc, id asc",
                "writable_fields": list(_DEVICE_WRITABLE_FIELDS),
                "description": (
                    "Tuya devices (cloud ID + optional LAN IP/local_key). "
                    "Usually discovered via discover/scan_local; enable/disable and local params are editable."
                ),
            },
            {
                "id": PROPERTIES,
                "title": "Tuya Device Properties (DPS)",
                "binding_mode": "property",
                "writable": True,
                "has_code": False,
                "list_filters": ["query", "device_id", "linked_object", "has_linked_object"],
                "default_sort": "name asc, id asc",
                "writable_fields": list(_PROPERTY_WRITABLE_FIELDS),
                "description": (
                    "DPS rows for a device. Bind linked_object/linked_property "
                    "(optional linked_method) for inbound updates and outbound control when writable."
                ),
            },
        ],
        "operations": ["discover", "scan_local", "poll_now", "get_connection_status"],
        "operation_schemas": {
            "discover": {
                "description": "Fetch devices from Tuya Cloud and upsert into DB (requires cloud credentials)",
                "params": {"type": "object", "properties": {}},
            },
            "scan_local": {
                "description": "Scan LAN for Tuya devices (IP / protocol version); does not auto-save",
                "params": {"type": "object", "properties": {}},
            },
            "poll_now": {
                "description": "Force immediate status poll of enabled devices",
                "params": {"type": "object", "properties": {}},
            },
            "get_connection_status": {
                "description": "Report connection_mode and whether cloud/local clients are ready (no secrets)",
                "params": {"type": "object", "properties": {}},
            },
        },
    }


def mcp_config_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "access_id": {
                "type": "string",
                "description": "Tuya IoT Platform Access ID",
            },
            "access_secret": {
                "type": "string",
                "writeOnly": True,
                "description": "Tuya IoT Platform Access Secret (never returned by config get)",
            },
            "region": {
                "type": "string",
                "enum": ["eu", "us", "cn", "in"],
                "default": "eu",
                "description": "Tuya cloud region",
            },
            "connection_mode": {
                "type": "string",
                "enum": ["cloud", "local", "both"],
                "default": "both",
                "description": "cloud / local / both (recommended)",
            },
            "poll_interval": {
                "type": "integer",
                "default": 30,
                "description": "Device status poll interval in seconds",
            },
            "poll_workers": {
                "type": "integer",
                "default": 4,
                "description": "Thread pool size for concurrent device polls",
            },
            "linked_uid": {
                "type": "string",
                "description": "Linked Smart Life / Tuya app user UID (helps when discover returns 0)",
            },
        },
    }


def _collection_meta(collection: str) -> dict:
    for item in mcp_capabilities()["collections"]:
        if item["id"] == collection:
            return item
    raise ValueError(f"Unsupported collection: {collection}")


def _format_dt(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    if isinstance(value, str) and value:
        return value
    return None


def _parse_optional_bool(value) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _readonly_fields(collection: str) -> tuple:
    if collection == DEVICES:
        return _DEVICE_READONLY_FIELDS
    if collection == PROPERTIES:
        return _PROPERTY_READONLY_FIELDS
    return ("id",)


def _writable_fields(collection: str) -> tuple:
    if collection == DEVICES:
        return _DEVICE_WRITABLE_FIELDS
    if collection == PROPERTIES:
        return _PROPERTY_WRITABLE_FIELDS
    return ()


def _device_to_dict(row: TuyaDevice) -> dict:
    return {
        "id": row.id,
        "device_id": row.device_id,
        "name": row.name,
        "category": row.category,
        "ip": row.ip,
        "has_local_key": bool(row.local_key),
        "protocol_version": row.protocol_version or "3.3",
        "connection_mode": row.connection_mode or "default",
        "online": bool(row.online),
        "enabled": bool(row.enabled) if row.enabled is not None else True,
        "discovered_at": _format_dt(row.discovered_at),
        "last_seen": _format_dt(row.last_seen),
    }


def _property_to_dict(row: TuyaDeviceProperty) -> dict:
    return {
        "id": row.id,
        "device_id": row.device_id,
        "name": row.name,
        "code": row.code,
        "dp_id": row.dp_id,
        "writable": bool(row.writable),
        "bidirectional": bool(row.bidirectional),
        "linked_object": row.linked_object,
        "linked_property": row.linked_property,
        "linked_method": row.linked_method,
    }


def _merge_payload(collection: str, payload: dict, entity_id=None) -> dict:
    merged = dict(payload or {})
    if entity_id in (None, ""):
        return merged
    try:
        current = mcp_get_entity(collection, entity_id)
    except ValueError:
        return merged
    for field in _writable_fields(collection):
        if field == "local_key":
            continue
        if field not in merged and field in current:
            merged[field] = current[field]
    return merged


def mcp_entity_schema(collection: str) -> dict:
    _collection_meta(collection)
    if collection == DEVICES:
        return {
            "type": "object",
            "description": "Tuya device with cloud ID and optional LAN credentials.",
            "properties": {
                "id": {"type": "integer", "readOnly": True, "description": "Internal DB id (MCP entity_id)"},
                "device_id": {
                    "type": "string",
                    "description": "Tuya cloud device ID (required on create, immutable after)",
                },
                "name": {"type": "string", "description": "Display name"},
                "category": {
                    "type": "string",
                    "description": "Tuya category (affects reference DPS hints)",
                },
                "ip": {"type": "string", "description": "LAN IP for local control"},
                "local_key": {
                    "type": "string",
                    "writeOnly": True,
                    "description": "Local key for tinytuya (never returned by list/get)",
                },
                "has_local_key": {
                    "type": "boolean",
                    "readOnly": True,
                    "description": "True when a local_key is stored",
                },
                "protocol_version": {
                    "type": "string",
                    "enum": list(_PROTOCOL_VERSIONS),
                    "default": "3.3",
                    "description": "Local protocol version",
                },
                "connection_mode": {
                    "type": "string",
                    "enum": list(_CONNECTION_MODES),
                    "default": "default",
                    "description": "Per-device poll/control: default (module setting), cloud, local, or both",
                },
                "enabled": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include device in polling / local registration",
                },
                "online": {"type": "boolean", "readOnly": True},
                "discovered_at": {"type": "string", "readOnly": True},
                "last_seen": {"type": "string", "readOnly": True},
            },
            "required": ["device_id", "name"],
        }
    if collection == PROPERTIES:
        return {
            "type": "object",
            "description": "DPS property row with optional osysHome property binding.",
            "properties": {
                "id": {"type": "integer", "readOnly": True},
                "device_id": {
                    "type": "integer",
                    "description": "Parent device internal DB id (required on create)",
                },
                "name": {"type": "string", "description": "Human-readable DPS label"},
                "code": {"type": "string", "description": "DPS code (e.g. switch_led, bright_value)"},
                "dp_id": {"type": "integer", "description": "Numeric DPS id on the device"},
                "writable": {
                    "type": "boolean",
                    "description": "Allow writing to device when linked property changes",
                },
                "bidirectional": {
                    "type": "boolean",
                    "description": "Two-way sync intent for the binding",
                },
                "linked_object": {"type": "string", "description": "Bound osysHome object name"},
                "linked_property": {"type": "string", "description": "Bound object property name"},
                "linked_method": {
                    "type": "string",
                    "description": "Optional object method called on DPS value change",
                },
            },
            "required": ["device_id", "name"],
        }
    raise ValueError(f"Unsupported collection: {collection}")


def mcp_list_entities(
    collection: str,
    query: str = None,
    limit: int = 100,
    device_id: Optional[int] = None,
    enabled: Optional[bool] = None,
    online: Optional[bool] = None,
    linked_object: Optional[str] = None,
    has_linked_object: Optional[bool] = None,
) -> List[dict]:
    limit = max(1, min(int(limit or 100), 5000))
    linked_obj = str(linked_object or "").strip()
    binding_filter = _parse_optional_bool(has_linked_object)

    if collection == DEVICES:
        enabled_filter = _parse_optional_bool(enabled)
        online_filter = _parse_optional_bool(online)
        with session_scope() as session:
            q = session.query(TuyaDevice)
            if query:
                like = f"%{query}%"
                q = q.filter(
                    or_(
                        TuyaDevice.name.ilike(like),
                        TuyaDevice.device_id.ilike(like),
                        TuyaDevice.category.ilike(like),
                        TuyaDevice.ip.ilike(like),
                    )
                )
            if enabled_filter is not None:
                q = q.filter(TuyaDevice.enabled.is_(enabled_filter))
            if online_filter is not None:
                q = q.filter(TuyaDevice.online.is_(online_filter))
            rows = q.order_by(TuyaDevice.name, TuyaDevice.id).limit(limit).all()
            return [_device_to_dict(row) for row in rows]

    if collection == PROPERTIES:
        with session_scope() as session:
            q = session.query(TuyaDeviceProperty)
            if device_id not in (None, ""):
                q = q.filter(TuyaDeviceProperty.device_id == int(device_id))
            if query:
                like = f"%{query}%"
                q = q.filter(
                    or_(
                        TuyaDeviceProperty.name.ilike(like),
                        TuyaDeviceProperty.code.ilike(like),
                        TuyaDeviceProperty.linked_object.ilike(like),
                        TuyaDeviceProperty.linked_property.ilike(like),
                    )
                )
            if linked_obj:
                q = q.filter(TuyaDeviceProperty.linked_object == linked_obj)
            if binding_filter is True:
                q = q.filter(
                    TuyaDeviceProperty.linked_object.isnot(None),
                    TuyaDeviceProperty.linked_object != "",
                    TuyaDeviceProperty.linked_property.isnot(None),
                    TuyaDeviceProperty.linked_property != "",
                )
            elif binding_filter is False:
                q = q.filter(
                    or_(
                        TuyaDeviceProperty.linked_object.is_(None),
                        TuyaDeviceProperty.linked_object == "",
                        TuyaDeviceProperty.linked_property.is_(None),
                        TuyaDeviceProperty.linked_property == "",
                    )
                )
            rows = q.order_by(TuyaDeviceProperty.name, TuyaDeviceProperty.id).limit(limit).all()
            return [_property_to_dict(row) for row in rows]
    raise ValueError(f"Unsupported collection: {collection}")


def mcp_get_entity(collection: str, entity_id) -> dict:
    with session_scope() as session:
        if collection == DEVICES:
            row = session.query(TuyaDevice).filter(TuyaDevice.id == int(entity_id)).one_or_none()
            if row is None:
                raise ValueError(f"Device not found: {entity_id}")
            return _device_to_dict(row)
        if collection == PROPERTIES:
            row = session.query(TuyaDeviceProperty).filter(
                TuyaDeviceProperty.id == int(entity_id)
            ).one_or_none()
            if row is None:
                raise ValueError(f"Property not found: {entity_id}")
            return _property_to_dict(row)
    raise ValueError(f"Unsupported collection: {collection}")


def mcp_upsert_entity(collection: str, payload: dict, entity_id=None) -> dict:
    meta = _collection_meta(collection)
    if not meta.get("writable"):
        raise ValueError(f"Collection '{collection}' is read-only")
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    clean_payload = dict(payload)
    for field in _readonly_fields(collection):
        clean_payload.pop(field, None)

    validation = mcp_validate_entity(collection, clean_payload, entity_id=entity_id)
    if not validation.get("ok"):
        raise ValueError(f"validation failed: {validation}")

    merged = _merge_payload(collection, clean_payload, entity_id=entity_id)
    instance = _plugin_instance()

    if collection == DEVICES:
        if instance is None:
            raise ValueError("Tuya plugin not loaded")
        cloud_device_id = str(merged.get("device_id") or "").strip()
        if entity_id not in (None, ""):
            with session_scope() as session:
                row = session.query(TuyaDevice).filter(TuyaDevice.id == int(entity_id)).one_or_none()
                if row is None:
                    raise ValueError(f"Device not found: {entity_id}")
                cloud_device_id = row.device_id
        if not cloud_device_id:
            raise ValueError("device_id is required")

        info = {
            "id": cloud_device_id,
            "name": merged.get("name"),
            "category": merged.get("category"),
            "ip": merged.get("ip"),
            "protocol_version": merged.get("protocol_version"),
            "connection_mode": merged.get("connection_mode"),
        }
        if "local_key" in clean_payload:
            info["local_key"] = clean_payload.get("local_key")
        instance._db_upsert_device(info)

        with session_scope() as session:
            row = session.query(TuyaDevice).filter(TuyaDevice.device_id == cloud_device_id).one_or_none()
            if row is None:
                raise ValueError(f"Device not found after upsert: {cloud_device_id}")
            if "enabled" in merged and merged.get("enabled") is not None:
                row.enabled = bool(merged.get("enabled"))
                session.commit()
            db_id = row.id
            local_payload = row.to_dict()

        if local_payload.get("enabled", True):
            instance._register_device_locally(local_payload)
        elif instance.local_client:
            instance.local_client.remove_device(cloud_device_id)
        return mcp_get_entity(DEVICES, db_id)

    if collection == PROPERTIES:
        with session_scope() as session:
            old_object = None
            old_property = None
            if entity_id not in (None, ""):
                row = session.query(TuyaDeviceProperty).filter(
                    TuyaDeviceProperty.id == int(entity_id)
                ).one_or_none()
                if row is None:
                    raise ValueError(f"Property not found: {entity_id}")
                old_object = row.linked_object
                old_property = row.linked_property
            else:
                device_pk = merged.get("device_id")
                name = str(merged.get("name") or "").strip()
                if device_pk in (None, "") or not name:
                    raise ValueError("device_id and name are required")
                row = (
                    session.query(TuyaDeviceProperty)
                    .filter(
                        TuyaDeviceProperty.device_id == int(device_pk),
                        TuyaDeviceProperty.name == name,
                    )
                    .one_or_none()
                )
                if row is None:
                    row = TuyaDeviceProperty()
                    row.device_id = int(device_pk)
                    row.name = name
                    session.add(row)
                else:
                    old_object = row.linked_object
                    old_property = row.linked_property

            if "name" in merged and entity_id not in (None, ""):
                name = str(merged.get("name") or "").strip()
                if name:
                    row.name = name
            for field in ("code", "linked_object", "linked_property", "linked_method"):
                if field in merged:
                    value = str(merged.get(field) or "").strip() or None
                    setattr(row, field, value)
            if "dp_id" in merged:
                row.dp_id = int(merged["dp_id"]) if merged["dp_id"] not in (None, "") else None
            if "writable" in merged:
                row.writable = bool(merged.get("writable"))
            if "bidirectional" in merged:
                row.bidirectional = bool(merged.get("bidirectional"))
            session.commit()

            ok, err = sync_property_link(
                PLUGIN_NAME,
                row.linked_object,
                row.linked_property,
                old_object=old_object,
                old_property=old_property,
            )
            if not ok:
                raise ValueError(err or "property link validation failed")
            if row.linked_object and row.linked_property and row.writable:
                setLinkToObject(row.linked_object, row.linked_property, PLUGIN_NAME)
            return _property_to_dict(row)

    raise ValueError(f"Unsupported collection: {collection}")


def mcp_delete_entity(collection: str, entity_id) -> bool:
    meta = _collection_meta(collection)
    if not meta.get("writable"):
        raise ValueError(f"Collection '{collection}' is read-only")
    instance = _plugin_instance()
    with session_scope() as session:
        if collection == DEVICES:
            row = session.query(TuyaDevice).filter(TuyaDevice.id == int(entity_id)).one_or_none()
            if row is None:
                raise ValueError(f"Device not found: {entity_id}")
            props = session.query(TuyaDeviceProperty).filter(
                TuyaDeviceProperty.device_id == row.id
            ).all()
            for prop in props:
                if prop.linked_object and prop.linked_property:
                    remove_property_link(PLUGIN_NAME, prop.linked_object, prop.linked_property)
            session.execute(delete(TuyaDeviceProperty).where(TuyaDeviceProperty.device_id == row.id))
            if instance and instance.local_client:
                instance.local_client.remove_device(row.device_id)
            session.delete(row)
            session.commit()
            return True
        if collection == PROPERTIES:
            row = session.query(TuyaDeviceProperty).filter(
                TuyaDeviceProperty.id == int(entity_id)
            ).one_or_none()
            if row is None:
                raise ValueError(f"Property not found: {entity_id}")
            if row.linked_object and row.linked_property:
                remove_property_link(PLUGIN_NAME, row.linked_object, row.linked_property)
            session.delete(row)
            session.commit()
            return True
    raise ValueError(f"Unsupported collection: {collection}")


def mcp_validate_entity_code(collection: str, code: str) -> dict:
    raise ValueError(f"Collection '{collection}' does not support code validation")


def mcp_run_entity_dry(collection: str, code: str, context: dict = None) -> dict:
    raise ValueError(f"Collection '{collection}' does not support dry-run code")


def _connection_status() -> dict:
    instance = _plugin_instance()
    if instance is None:
        return {
            "plugin_loaded": False,
            "connection_mode": None,
            "cloud_ready": False,
            "local_ready": False,
        }
    mode = str((getattr(instance, "config", {}) or {}).get("connection_mode") or "both")
    cloud = getattr(instance, "cloud_client", None)
    local = getattr(instance, "local_client", None)
    cloud_ready = bool(cloud and getattr(cloud, "is_connected", lambda: False)())
    return {
        "plugin_loaded": True,
        "connection_mode": mode,
        "cloud_ready": cloud_ready,
        "local_ready": bool(local),
        "access_id_set": bool((getattr(instance, "config", {}) or {}).get("access_id")),
        "linked_uid_set": bool((getattr(instance, "config", {}) or {}).get("linked_uid")),
        "device_count": None,
    }


def mcp_invoke(operation: str, params: dict = None) -> dict:
    params = params or {}
    if operation == "get_connection_status":
        status = _connection_status()
        if status.get("plugin_loaded"):
            with session_scope() as session:
                status["device_count"] = session.query(TuyaDevice).count()
        return {"ok": True, "operation": operation, **status}

    instance = _plugin_instance()
    if instance is None:
        raise ValueError("Tuya plugin not loaded")

    if operation == "discover":
        if not instance.cloud_client:
            raise ValueError("Cloud not connected")
        count = 0
        for cd in instance.cloud_client.get_devices():
            device_id = cd.get("id") or cd.get("device_id")
            if not device_id:
                continue
            info = instance.cloud_client.get_device_info(device_id) or {
                "id": device_id,
                "name": cd.get("name") or device_id,
                "category": cd.get("category", "unknown"),
                "ip": cd.get("ip"),
                "local_key": cd.get("local_key"),
                "protocol_version": instance._normalize_protocol_version(cd) or "3.3",
                "online": cd.get("online", False),
            }
            dev_dict = instance._db_upsert_device(info)
            instance._register_device_locally(dev_dict)
            count += 1
        return {"ok": True, "operation": operation, "count": count}

    if operation == "scan_local":
        if not instance.local_client:
            raise ValueError("Local client not initialized")
        devices = instance.local_client.scan_local()
        return {"ok": True, "operation": operation, "devices": devices}

    if operation == "poll_now":
        instance._poll_devices()
        return {"ok": True, "operation": operation}

    raise ValueError(f"Unsupported operation: {operation}")


def mcp_descriptors() -> Tuple[list, list, list]:
    return build_plugin_mcp_descriptors(PLUGIN_NAME, mcp_capabilities())


def mcp_get_prompt(name: str, arguments: dict = None) -> dict:
    arguments = arguments or {}
    notes_block = "\n".join(f"- {note}" for note in _PLUGIN_NOTES)

    if name == _BINDING_PROMPT:
        object_name = str(arguments.get("object_name") or "").strip()
        property_name = str(arguments.get("property_name") or "").strip()
        device_id = arguments.get("device_id")
        dps_code = str(arguments.get("code") or arguments.get("dps") or "").strip()
        prompt_text = (
            "Bind a Tuya DPS property to an osysHome object property.\n"
            f"Plugin: {PLUGIN_NAME}\n"
            f"Object: {object_name or '-'}\n"
            f"Property: {property_name or '-'}\n"
            f"Device id (DB): {device_id or '-'}\n"
            f"DPS code: {dps_code or '-'}\n\n"
            f"Plugin notes:\n{notes_block}\n\n"
            "Flow:\n"
            "1. osys_plugin_list_entities collection=devices (find device)\n"
            "2. osys_plugin_list_entities collection=properties device_id=<db id>\n"
            "3. osys_plugin_entity_schema collection=properties\n"
            "4. Upsert properties with linked_object/linked_property "
            "(set writable=false for sensors/R/O; writable=true for switches)\n"
            "5. osys_plugin_validate_entity then osys_plugin_upsert_entity\n"
            "6. Prefer osys_bind_device when available\n"
        )
        return {"messages": [{"role": "user", "content": {"type": "text", "text": prompt_text}}]}

    if name == _ENTITY_AUTHORING_PROMPT:
        task = str(arguments.get("task") or "").strip()
        collection = str(arguments.get("collection") or DEVICES).strip()
        if not task:
            raise ValueError("task is required")
        prompt_text = (
            "Create or update Tuya plugin entity payload by schema.\n"
            f"Plugin: {PLUGIN_NAME}\nCollection: {collection}\nTask: {task}\n\n"
            f"Plugin notes:\n{notes_block}\n\n"
            "Flow: osys_plugin_entity_schema -> validate_entity -> upsert_entity.\n"
            "Devices: prefer invoke discover/scan_local; manual needs device_id, name, "
            "optionally ip/local_key/protocol_version/connection_mode/enabled.\n"
            "Properties: device_id (DB pk), name, code, dp_id, writable, "
            "linked_object, linked_property, linked_method.\n"
            "local_key is write-only. After saving devices call poll_now if needed.\n"
        )
        return {"messages": [{"role": "user", "content": {"type": "text", "text": prompt_text}}]}

    raise ValueError(f"Unsupported prompt: {name}")


def mcp_entity_revision(collection: str, entity_id) -> str:
    entity = mcp_get_entity(collection, entity_id)
    if collection == DEVICES:
        seen = revision_from_datetime(entity.get("last_seen"))
        if seen:
            return seen
        return revision_from_dict(
            entity,
            keys=["id", "device_id", "name", "enabled", "online", "ip", "has_local_key", "connection_mode"],
        )
    if collection == PROPERTIES:
        return revision_from_dict(
            entity,
            keys=[
                "id",
                "device_id",
                "name",
                "code",
                "dp_id",
                "writable",
                "bidirectional",
                "linked_object",
                "linked_property",
                "linked_method",
            ],
        )
    raise ValueError(f"Unsupported collection: {collection}")


def mcp_validate_entity(collection: str, payload: dict, entity_id=None) -> dict:
    if collection not in (DEVICES, PROPERTIES):
        raise ValueError(f"Unsupported collection: {collection}")
    if not isinstance(payload, dict):
        return {"ok": False, "errors": [{"field": "_", "message": "payload must be an object"}]}

    disallowed = [key for key in payload if key in _readonly_fields(collection)]
    if disallowed:
        return {
            "ok": False,
            "errors": [{"field": disallowed[0], "message": "field is read-only"}],
        }

    merged = _merge_payload(collection, payload, entity_id=entity_id)
    schema = mcp_entity_schema(collection)
    # On update, device_id/name may come from merge; drop writeOnly local_key type check noise
    check_payload = dict(merged)
    if "local_key" in check_payload and check_payload.get("local_key") is None:
        check_payload.pop("local_key", None)
    result = validate_entity_payload(check_payload, schema)
    if not result.get("ok"):
        return result

    errors = list(result.get("errors") or [])
    warnings: List[dict] = []

    if collection == DEVICES:
        protocol = merged.get("protocol_version")
        if protocol not in (None, "") and str(protocol) not in _PROTOCOL_VERSIONS:
            errors.append({
                "field": "protocol_version",
                "message": f"must be one of: {', '.join(_PROTOCOL_VERSIONS)}",
            })

        conn_mode = merged.get("connection_mode")
        if conn_mode not in (None, "") and str(conn_mode).strip().lower() not in _CONNECTION_MODES:
            errors.append({
                "field": "connection_mode",
                "message": f"must be one of: {', '.join(_CONNECTION_MODES)}",
            })

        if entity_id not in (None, ""):
            with session_scope() as session:
                row = session.query(TuyaDevice).filter(TuyaDevice.id == int(entity_id)).one_or_none()
                if row is None:
                    errors.append({"field": "id", "message": f"Device not found: {entity_id}"})
                elif "device_id" in payload:
                    new_id = str(payload.get("device_id") or "").strip()
                    if new_id and new_id != row.device_id:
                        errors.append({
                            "field": "device_id",
                            "message": "device_id is immutable after create",
                        })
        else:
            cloud_id = str(merged.get("device_id") or "").strip()
            if cloud_id:
                with session_scope() as session:
                    existing = session.query(TuyaDevice).filter(
                        TuyaDevice.device_id == cloud_id
                    ).one_or_none()
                    if existing is not None:
                        warnings.append({
                            "field": "device_id",
                            "message": f"device already exists as entity_id={existing.id}; upsert will update it",
                        })

        if not merged.get("ip") and "local_key" in payload and payload.get("local_key"):
            warnings.append({
                "field": "ip",
                "message": "local_key without ip: local control needs both; run scan_local",
            })

    if collection == PROPERTIES:
        device_pk = merged.get("device_id")
        if device_pk in (None, ""):
            if entity_id in (None, ""):
                errors.append({"field": "device_id", "message": "required"})
        else:
            try:
                device_pk_int = int(device_pk)
            except (TypeError, ValueError):
                errors.append({"field": "device_id", "message": "must be an integer"})
                device_pk_int = None
            if device_pk_int is not None:
                with session_scope() as session:
                    device = session.query(TuyaDevice).filter(
                        TuyaDevice.id == device_pk_int
                    ).one_or_none()
                    if device is None:
                        errors.append({
                            "field": "device_id",
                            "message": f"Device not found: {device_pk_int}",
                        })

        if entity_id not in (None, ""):
            with session_scope() as session:
                row = session.query(TuyaDeviceProperty).filter(
                    TuyaDeviceProperty.id == int(entity_id)
                ).one_or_none()
                if row is None:
                    errors.append({"field": "id", "message": f"Property not found: {entity_id}"})

        linked_object = str(merged.get("linked_object") or "").strip()
        linked_property = str(merged.get("linked_property") or "").strip()
        linked_method = str(merged.get("linked_method") or "").strip()

        if linked_object or linked_property:
            if not linked_object or not linked_property:
                errors.append({
                    "field": "linked_property",
                    "message": "linked_object and linked_property must both be set",
                })
            else:
                if not validate_object_exists(linked_object):
                    errors.append({
                        "field": "linked_object",
                        "message": f"Object not found: {linked_object}",
                    })
                elif not validate_object_property_exists(linked_object, linked_property):
                    errors.append({
                        "field": "linked_property",
                        "message": f"Object property not found: {linked_object}.{linked_property}",
                    })

        if linked_method:
            obj_for_method = linked_object
            if not obj_for_method and entity_id not in (None, ""):
                try:
                    current = mcp_get_entity(PROPERTIES, entity_id)
                    obj_for_method = str(current.get("linked_object") or "").strip()
                except ValueError:
                    obj_for_method = ""
            if not obj_for_method:
                errors.append({
                    "field": "linked_method",
                    "message": "linked_object is required when linked_method is set",
                })
            elif not validate_object_method_exists(obj_for_method, linked_method):
                errors.append({
                    "field": "linked_method",
                    "message": f"Object method not found: {obj_for_method}.{linked_method}",
                })

    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}

    response = {"ok": True, "errors": []}
    if warnings:
        response["warnings"] = warnings
    return response
