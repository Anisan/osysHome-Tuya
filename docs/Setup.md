# Tuya Setup

## 1. What to prepare first

Before configuring the module, make sure:

- devices are already added to `Tuya Smart` or `Smart Life`
- the `osysHome` server has internet access
- for local control, the server is on the same network as the devices

## 2. Tuya cloud setup

Basic setup flow:

1. Create a project on [iot.tuya.com](https://iot.tuya.com/).
2. Select the correct `Data Center`.
3. Copy `Access ID` and `Access Secret`.
4. Authorize at least the `IoT Core` service.
5. Link the mobile app account in `Devices -> Link Tuya App Account`.

If you need the exact click-by-click path, see `GetStarted.md`.

## 3. Module settings fields

The `Settings` dialog includes:

- `Access ID` — Tuya cloud project identifier
- `Access Secret` — Tuya cloud project secret
- `Region` — cloud region; must match the Tuya project `Data Center`
- `Connection Mode` — how the module communicates with devices
- `Poll Interval` — status polling interval in seconds
- `Linked App User UID` — optional app user UID for device discovery

Settings are applied immediately without restarting the module.

## 4. Connection modes

### Cloud only

Use this mode when:

- local networking is not available
- you only want cloud discovery and cloud control
- you do not have `Local Key`

Pros:

- easiest initial setup
- no LAN scanning required

Cons:

- higher command latency
- higher Tuya Cloud usage

### Local only

Use this mode when:

- you already have `Device ID`, `Local Key`, and device IP addresses
- the cloud project is not needed or not available

Pros:

- fast commands
- minimal cloud dependency

Cons:

- harder first-time setup
- harder to obtain categories and real DPS metadata automatically

### Both (Cloud + Local)

This is the recommended mode for most installations.

How it works:

- cloud helps discover devices and fetch their specification
- LAN is used for status polling and command delivery
- if a local request fails, the module can use cloud access as a fallback

## 5. When `Linked App User UID` is needed

This field is useful when:

- cloud connection succeeds
- `Discover Devices` returns 0 devices
- the mobile app account is already linked to the Tuya project

Where to find it:

- on `iot.tuya.com`
- in the `Devices` section
- under the linked mobile app account details

Practical rule:

- if discovery works without UID, leave it empty
- if no devices are found, first verify app linking, then try filling in the UID

## 6. Local control requirements

For local control you need:

- `Device ID`
- `Local Key`
- device IP address
- correct protocol version, usually `3.3`, `3.4`, or `3.5`

Where to get these values:

- after `Discover Devices`, some values are pulled from cloud automatically
- IP addresses can be found via `Scan LAN`
- `Local Key` can be obtained through `Get local keys`

## 7. How to get `Local Key`

There are two main options:

### Via Tuya cloud

Works best when:

- the cloud project is configured correctly
- the device appears in discovered cloud devices

### Via `Get local keys`

This uses the login credentials from the `Tuya Smart` / `Smart Life` mobile app.

You need to provide:

- `Email`
- `Password`
- `App / Vendor`
- `Region`

The module then shows discovered devices and their `Local Key` values. After that, you can click `Apply keys to existing devices`.

Important:

- app credentials should not be treated as a permanent admin secret
- if your account uses OEM branding or extra protection, results depend on the specific brand and region

## 8. Choosing the protocol version

The manual options are:

- `3.1`
- `3.3`
- `3.4`
- `3.5`

Recommendations:

- start with the auto-detected version
- if local control never works, try nearby versions manually
- if the device mostly works but sometimes reports `904`, `905`, or `914`, that does not always mean the version is wrong

## 9. Poll interval guidance

`Poll Interval` controls how often device state is checked.

Important details:

- the interval is measured from the start of the poll cycle, not as "request time plus another full interval"
- when several devices are enabled, the module tries to poll them in parallel
- with only one device, parallelism does not matter and the main delay comes from the local status request itself
- in `Local only` mode, a change made in the mobile app is visible only on the next local poll
- if a local request fails and needs a retry, the effective delay can be longer than the configured interval

Recommendations:

- `30` seconds — a solid default
- `10-15` seconds — for faster response with a small number of devices
- `60+` seconds — for larger installations or lower load

In `Both` mode, it is usually best to rely on LAN for routine polling.

### What this means in practice

If you have:

- `Local only`
- `Poll Interval = 5`
- one device

then a status change made from the mobile app usually becomes visible within the next local poll, but:

- not instantly, because there is no cloud push in this mode
- not always exactly after `5` seconds, because `device.status()` itself also takes time
- sometimes later, if the first local request fails and a retry is needed

### New diagnostic log messages

To analyze delays, inspect `Tuya.log` and look for:

- `Poll cycle complete: devices=... elapsed=... interval=...`
- `Poll batch: devices=... mode=... elapsed=...`
- `Poll <device_id>: local status ready in ...s`
- `Poll <device_id>: cloud fallback ready in ...s`
- `Poll <device_id>: no status after ...s`
- `get_status <device_id>: success in ...s on attempt ...`
- `get_status <device_id>: finished without DPS in ...s after ... attempt(s)`

## 10. Minimal recommended setup

For a stable first deployment:

- `Region` — same as in Tuya Cloud
- `Connection Mode` — `Both (Cloud + Local)`
- `Poll Interval` — `30`
- run `Discover Devices`
- run `Scan LAN`
- if needed, fetch keys via `Get local keys`

After that, continue with DPS binding in `DevicesAndDPS.md`.
