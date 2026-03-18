# Tuya Troubleshooting

## 1. Where to start

If something does not work, check in this order:

1. Does cloud connection work
2. Are devices found by `Discover Devices`
3. Are devices visible in `Scan LAN`
4. Does the device have a `Local Key`
5. Is the `Protocol Version` correct
6. Are the DPS bindings configured correctly

## 2. `Discover Devices` returns 0 devices

Check that:

- the app account is linked through `Devices -> Link Tuya App Account`
- the selected `Region` is correct
- the Tuya Cloud project was created in the correct data center
- `Linked App User UID` is filled in if normal discovery did not work

If the problem remains:

- relink the mobile app account
- verify that the devices are actually in the same app account

## 3. Device exists in cloud but local control does not work

Check that:

- the server and device are on the same network
- the device has a current IP address
- the device record contains a `Local Key`
- the correct protocol version is selected

What to do:

1. click `Scan LAN`
2. click `Update and add devices`
3. if key is missing, use `Get local keys`
4. try nearby protocol versions such as `3.3`, `3.4`, and `3.5`

## 4. Errors `904`, `905`, `914`

### What they usually mean

- `904` — the device returned an unexpected response or interrupted local communication
- `905` — the device was temporarily unreachable on the network
- `914` — `tinytuya` could not complete local communication correctly; this does not always mean the key or version is wrong

### Important practical note

If a device:

- works normally some of the time
- but occasionally reports `904`, `905`, or `914`

then the problem is often not the saved settings, but rather:

- unstable local session state
- Wi-Fi quality
- device firmware behavior
- temporary socket disconnects

### What to do

- refresh IP using `Scan LAN`
- check Wi-Fi signal and device power stability
- only try another `Protocol Version` if local control never works or almost never works
- use `Both` mode so cloud remains available as a fallback

## 5. Device is always offline

Check that:

- the device is powered on
- it is actually connected to Wi-Fi
- its IP address did not change
- traffic between server and device is not blocked

For local mode:

- make sure the device is reachable from the server network
- check Wi-Fi client isolation settings on the router

## 6. Status from the mobile app arrives too late

This is especially noticeable in `Local only` mode.

Why it happens:

- the mobile app changes device state through cloud
- in `Local only`, the module does not receive cloud push and only sees the new state on the next local poll
- even with `Poll Interval = 5`, the actual delay can be longer if the local status request itself is slow
- if there is a network hiccup or transient failure, an automatic retry can add more delay

What to check:

- confirm that `Local only` is really enabled
- inspect how long `get_status()` actually takes in the logs
- check whether retries happen after `904`, `905`, or `914`
- verify Wi-Fi stability for the device

Practical conclusion:

- if you need near-instant updates from mobile app changes, prefer `Both`
- if you want cloud-independent operation, in `Local only` you should expect polling behavior rather than push behavior

## 7. `Get local keys` finds nothing

Check that:

- the email is correct
- the password matches the mobile app account
- the correct `App / Vendor` is selected
- the correct region is selected

Also remember:

- some OEM-branded apps behave differently
- if the account belongs to a branded app rather than `Smart Life`, choose the matching vendor

## 8. DPS values are visible but commands do not work

Check that:

- the point is not set to `R/O`
- the DPS is actually writable
- the value type matches what the device expects

Common mistakes:

- trying to write to a sensor-only DPS
- choosing the wrong `switch`
- binding brightness or color to the wrong point

## 9. DPS list is empty or looks wrong

Possible causes:

- wrong `Category`
- cloud specification is unavailable
- the device was added recently and its metadata is not complete yet

What to do:

1. open device editing
2. verify `Category`
3. refresh the device through `Discover Devices`
4. reopen `Link DPS`

## 10. When to change `Protocol Version`

Change the protocol version when:

- local control never works
- the device gives the same error every time

Do not rush to change it when:

- the device works most of the time
- occasional errors alternate with successful responses

A sensible order is:

1. auto-detected version
2. `3.3`
3. `3.4`
4. `3.5`

`3.1` is mainly worth trying for some older devices.

## 11. How to read the new log messages

To diagnose polling delays, look in `Tuya.log` for these messages:

- `Poll cycle complete: devices=... elapsed=... interval=...`
- `Poll batch: devices=... mode=... elapsed=...`
- `Poll <device_id>: local status ready in ...s`
- `Poll <device_id>: cloud fallback ready in ...s`
- `Poll <device_id>: no status after ...s`
- `get_status <device_id>: success in ...s on attempt ...`
- `get_status <device_id>: finished without DPS in ...s after ... attempt(s)`

How to interpret them:

- if cycle or batch `elapsed` is close to your configured interval, the module is spending most of its time polling
- if `local status ready in ...s` is large, the slow part is the local request to the device itself
- if you often see `finished without DPS` or repeated attempts, the delay is caused by unstable local replies

## 12. When to use cloud only

Stay with `Cloud only` when:

- the local network is unreliable
- the device behaves correctly only through cloud
- `Local Key` could not be obtained

The downside is slower response and higher cloud usage.

## 13. When `Both` mode is best

Use `Both` when you want:

- fast local control
- automatic device discovery
- cloud fallback

For daily operation, this is usually the most practical mode.

## 14. Quick verification checklist

If a device does not work, check in this order:

1. `Region`
2. app account linking
3. `Linked App User UID`
4. presence of `Local Key`
5. IP after `Scan LAN`
6. protocol version
7. DPS bindings

In most cases, the problem is found in one of these steps.
