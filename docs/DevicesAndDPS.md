# Devices and DPS

## 1. Where devices come from

The module can obtain devices in several ways:

- from cloud using `Discover Devices`
- from the local network using `Scan LAN`
- manually using `Add Device`

In practice, the best results usually come from this sequence:

1. `Discover Devices`
2. `Scan LAN`
3. if needed, `Get local keys`

## 2. How to read the device list

Important fields in the device list:

- `Name` — the device name in the system
- `Category` — Tuya device category
- `Status` — online or offline
- `Connection`:
  - `LAN` — the device has a local IP
  - `Cloud` — the device is known via cloud, but no local IP is known yet
- `Device ID` — unique device identifier

## 3. When to use `Discover Devices`

Use `Discover Devices` when:

- Tuya cloud is configured
- you want the module to pull devices automatically
- you want names, categories, metadata, and possibly local keys from cloud

If `Discover Devices` returns 0 devices:

1. verify that the mobile app account is linked to the Tuya project
2. verify `Region`
3. try filling in `Linked App User UID`

## 4. When to use `Scan LAN`

`Scan LAN` searches the local network for Tuya devices and shows:

- name
- `Device ID`
- IP address
- detected protocol version

It is especially useful when:

- cloud discovery did not fill IP addresses
- a device changed its IP address
- you are setting up `Local only`

After scanning, use `Update and add devices` to:

- update IP and protocol version for existing devices
- add new devices found only on the local network

## 5. Manual device addition

Use `Add Device` when cloud is not configured or when you need to add a device manually.

Form fields:

- `Device ID` — required
- `Device Name` — friendly name
- `Local Key` — required for local control
- `IP Address` — local IP address of the device
- `Protocol Version` — device protocol version
- `Category` — helps when working with DPS

Recommendations:

- if you do not know the exact category yet, start with `unknown`
- update it later when you identify the correct category

## 6. What device category means

`Category` determines which typical DPS codes are expected for a device type.

It affects:

- how DPS rows are labeled
- suggested types and semantics
- reference DPS shown when live cloud specification is not available

If category is wrong:

- the DPS list may be incomplete or confusing
- labels may not match the real meaning of a point

## 7. What DPS means

`DPS` stands for Data Points: the individual values exposed by the device.

Examples:

- power on/off
- brightness
- color
- temperature
- operating mode
- current sensor reading

Most devices expose multiple DPS values.

## 8. Where the DPS list comes from in `Link DPS`

The binding dialog can show two sources:

- `Cloud` — real functions and status from the device cloud specification
- `Reference` — built-in reference data based on the device category

Practical rule:

- if `Cloud` is available, trust it first
- if only `Reference` is available, validate mappings against real device behavior

## 9. How to bind DPS to a system object

Open `Link DPS` for the device and configure:

- `Object` — target system object
- `Property` — property to read or write
- `Method` — optional method to call
- `Mode`:
  - normal mode — writable if the DPS supports writing
  - `R/O` — force read-only behavior

After saving:

- device status updates can update the linked property
- property changes in the system can send commands to the device

## 10. When to use `R/O`

Set `R/O` when:

- the value should only be observed, not written back
- the device behaves poorly when writing to that point
- you want to prevent accidental control from automation logic

Good `R/O` examples:

- sensor temperature
- humidity
- battery level
- diagnostic flags

## 11. Practical binding order

For a light:

1. find `switch` or `switch_led`
2. bind it to a boolean `status` property
3. find `bright_value` or `bright_value_v2`
4. bind it to a numeric brightness property
5. if `colour_data` is available, bind it to a color property

For a smart plug:

1. bind the main `switch`
2. if power or current values exist, bind them as `R/O`

For a sensor:

1. bind measured values as `R/O`
2. avoid enabling writes for values that are published by the device only

## 12. How to verify a correct binding

Signs of a correct setup:

- the linked property changes when device status changes
- changing the property in the system makes the device react correctly
- current values are visible in `Link DPS`

If the behavior is wrong:

- verify `Category`
- compare the selected DPS against real device behavior
- temporarily switch uncertain points to `R/O`

## 13. What to do after IP or protocol changes

If a device changes IP or starts behaving poorly over local control:

1. run `Scan LAN`
2. click `Update and add devices`
3. if needed, open the device and verify `Protocol Version`

For error handling and local communication issues, continue with `Troubleshooting.md`.
