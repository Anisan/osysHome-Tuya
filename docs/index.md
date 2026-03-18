# Tuya Plugin Documentation

This section explains how the `Tuya` module works, which connection mode to choose, how to add devices, and how to bind DPS values to system properties.

## What the module can do

- Connect to Tuya Cloud using `Access ID` and `Access Secret`
- Control devices locally over LAN via `tinytuya`
- Auto-discover devices from a `Tuya Smart` / `Smart Life` account
- Add devices manually using `Device ID`, `Local Key`, and IP
- Fetch `Local Key` values from the mobile app account directly from the module UI
- Bind DPS values to system objects and properties
- Use cloud and local access together, with local control as the primary channel

## How to use this documentation

- `GetStarted.md` — the fastest path to a working setup
- `Setup.md` — detailed cloud, local, and connection mode configuration
- `DevicesAndDPS.md` — adding devices, scanning LAN, categories, and DPS binding
- `Troubleshooting.md` — common errors, validation steps, and practical fixes

## Key terms

- `Tuya Cloud` — Tuya cloud API, used for device discovery, specification lookup, and fallback control
- `LAN / Local` — direct communication with the device over the local network
- `Device ID` — unique Tuya device identifier
- `Local Key` — secret key required for local control
- `Category` — Tuya device type that helps determine typical DPS codes
- `DPS` — Data Points, individual device values such as power, brightness, temperature, mode, and so on
- `Linked App User UID` — UID of the linked `Tuya Smart` / `Smart Life` app user; useful when cloud discovery returns 0 devices

## Recommended flow for most users

1. Create a Tuya cloud project and link your app account.
2. Set the connection mode to `Both (Cloud + Local)`.
3. Run `Discover Devices`.
4. Click `Scan LAN` so the module can find device IP addresses on the local network.
5. If devices are missing `Local Key`, use `Get local keys`.
6. Open `Link DPS` for each important device and bind the required values to system properties.

## Which connection mode to choose

- `Cloud only` — use when you only need cloud access or local networking is not available
- `Local only` — use when all devices are already known and you already have `Local Key` values and IP addresses
- `Both (Cloud + Local)` — recommended:
  - cloud is used for discovery, DPS metadata, and fallback access
  - LAN is used for fast commands and status polling

## Important things to know up front

- Not all devices behave equally well over local control; firmware quality matters.
- Errors `904`, `905`, and `914` do not always mean a wrong key or protocol version.
- For local control, the device and the server must be on the same network, or on routed subnets without blocked traffic.
- Device category helps with DPS mapping, but real cloud specification data is still more accurate.

## Security

- `Access Secret` and `Local Key` provide control over your devices.
- Do not publish them in screenshots, logs, or public repositories.
- The `Get local keys` feature uses your app account credentials only for the request and should not replace normal cloud configuration.
