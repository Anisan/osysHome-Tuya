# MCP — Tuya

Плагин работает с устройствами Tuya через облако и/или LAN (`tinytuya`), хранит DPS и привязывает их к свойствам объектов osysHome.

## Plugin notes

- Предпочитайте `discover` + `scan_local`, а не ручное изобретение устройств; ручное создание требует `device_id`, для LAN ещё `ip` + `local_key`.
- Режим `both`: облако — discovery/спецификация/fallback, локально — быстрое управление при наличии IP и ключа.
- `device_id` — cloud ID Tuya (не меняется после create). MCP `entity_id` — внутренний DB id.
- `local_key` и `access_secret` — write-only (в list/get не возвращаются; есть `has_local_key`).
- `properties` — привязки DPS: `code`/`dp_id`, `linked_object` + `linked_property`.
- `writable=false` — только чтение (датчики); `writable=true` — команды при изменении свойства.
- Если `discover` вернул 0 устройств — заполните `config.linked_uid` и повторите.
- Перед upsert привязок вызывайте `validate_entity`.

## Collections

| ID | binding_mode | writable | writable_fields | list_filters |
|----|--------------|----------|-----------------|--------------|
| `devices` | `none` | yes | `device_id`, `name`, `category`, `ip`, `local_key`, `protocol_version`, `enabled` | `query`, `enabled`, `online` |
| `properties` | `property` | yes | `device_id`, `name`, `code`, `dp_id`, `writable`, `bidirectional`, `linked_object`, `linked_property`, `linked_method` | `query`, `device_id`, `linked_object`, `has_linked_object` |

### Поля entity (devices)

| поле | writable | описание |
|------|----------|----------|
| `id` | read-only | DB id (MCP entity_id) |
| `device_id` | create | Cloud ID Tuya |
| `name`, `category`, `ip`, `protocol_version`, `enabled` | да | Метаданные / LAN |
| `local_key` | write-only | Ключ tinytuya |
| `has_local_key`, `online`, `last_seen`, `discovered_at` | read-only | Статус |

### Поля entity (properties)

| поле | writable | описание |
|------|----------|----------|
| `id` | read-only | DB id |
| `device_id` | create | DB id родителя из `devices` |
| `name`, `code`, `dp_id` | да | Идентификация DPS |
| `writable`, `bidirectional` | да | Режим записи / двусторонняя синхронизация |
| `linked_object`, `linked_property`, `linked_method` | да | Привязка к osysHome |

## Операции (invoke)

| operation | Описание |
|-----------|----------|
| `discover` | Подтянуть устройства из Tuya Cloud в БД |
| `scan_local` | Сканировать LAN (IP / protocol); без автосохранения |
| `poll_now` | Немедленный опрос статуса enabled-устройств |
| `get_connection_status` | Режим подключения и готовность cloud/local (без секретов) |

## Промпты

| name | Назначение |
|------|------------|
| `osys_tuya_entity_authoring` | Собрать payload устройства/DPS по схеме |
| `osys_tuya_binding` | Привязать `object.property` к DPS |

## Примеры

### Discover + LAN scan

```json
{
  "plugin": "Tuya",
  "action": "invoke",
  "args": { "operation": "discover", "params": {} }
}
```

```json
{
  "plugin": "Tuya",
  "action": "invoke",
  "args": { "operation": "scan_local", "params": {} }
}
```

### Список устройств онлайн

```json
{
  "plugin": "Tuya",
  "action": "list_entities",
  "args": {
    "collection": "devices",
    "online": true,
    "limit": 100
  }
}
```

### Привязать DPS к свойству

```json
{
  "plugin": "Tuya",
  "action": "upsert_entity",
  "args": {
    "collection": "properties",
    "payload": {
      "device_id": 1,
      "name": "Switch",
      "code": "switch_led",
      "dp_id": 1,
      "writable": true,
      "linked_object": "Lamp.Kitchen",
      "linked_property": "status"
    }
  }
}
```

### Только свойства с привязкой

```json
{
  "plugin": "Tuya",
  "action": "list_entities",
  "args": {
    "collection": "properties",
    "device_id": 1,
    "has_linked_object": true
  }
}
```

### Статус интеграции

```json
{
  "plugin": "Tuya",
  "action": "invoke",
  "args": {
    "operation": "get_connection_status",
    "params": {}
  }
}
```
