# Tuya Plugin — Getting Started

## Prerequisites

- Account in [Tuya Smart](https://play.google.com/store/apps/details?id=com.tuya.smart) or [Smart Life](https://play.google.com/store/apps/details?id=com.tuya.smartlife) app
- Devices already added and working in the app
- Internet access for cloud registration

## Step 1 — Create a Tuya IoT Cloud Project

1. Go to **https://iot.tuya.com/** and register (or log in)
2. In the left menu: **Cloud** → **Development** → **Create Cloud Project**
3. Fill in:
   - **Project Name** — any name (e.g. `NextGetSmart`)
   - **Industry** — Smart Home
   - **Development Method** — Smart Home
   - **Data Center** — choose your region:
     | Code | Region |
     |------|--------|
     | `eu` | Western Europe (Ireland) |
     | `us` | Western America |
     | `cn` | China |
     | `in` | India |
4. Click **Create**

## Step 2 — Copy Access ID and Access Secret

After creating the project you will see:

- **Access ID / Client ID** — this is your `Access ID`
- **Access Secret / Client Secret** — this is your `Access Secret`

> Save these values — you will need them in the plugin settings.

## Step 3 — Authorize API Services

On the project page go to **Authorize API Services** tab and make sure the following are enabled:

- **IoT Core** (required)
- **Smart Home Scene Linkage** (optional, for scene automation)
- **IoT Data Analytics** (optional, for history/stats)

If they are not listed, click **Add Authorization** and search for them.

## Step 4 — Link Devices to the Cloud Project

1. On the project page go to **Devices** → **Link Tuya App Account**
2. Click **Add App Account**
3. Open the **Tuya Smart** or **Smart Life** app on your phone
4. Go to **Me** → tap the scan icon (top right) → scan the QR code shown on the website
5. Confirm the link — all devices from your app account are now accessible via the Cloud API

## Step 5 — Configure the Plugin

1. Open the Tuya plugin admin page in NextGetSmart
2. Click the **Settings** (gear icon) button
3. Enter:
   - **Access ID** — from Step 2
   - **Access Secret** — from Step 2
   - **Region** — the same Data Center code you selected in Step 1 (`eu`, `us`, `cn`, `in`)
   - **Connection Mode** — recommended: `Both` (cloud + local)
   - **Poll Interval** — how often to poll device status (default: 30 seconds)
4. Click **Save**

## Step 6 — Discover Devices

Click **Discover Devices** — the plugin will pull all devices from your Tuya account, including their names, categories, and local keys.

## Step 7 — Link DPS to System Objects

1. Click the **Link** (chain icon) button next to a device
2. The DPS list is loaded:
   - **Cloud** (green badge) — real DPS from the device specification (only what the device actually supports)
   - **Reference** (yellow badge) — standard DPS from the built-in reference table
3. For each DPS, select:
   - **Object** — the system object to bind to
   - **Property** — the property to read/write values
   - **Method** — the method to call (optional)
   - **Mode** — check "R/O" to make a writable DPS read-only in the system
4. Click **Save**

## Optional — Local Control

For faster response without cloud latency, the plugin supports direct LAN control via `tinytuya`.

Requirements for local control:
- Device must be on the same network as the server
- Device **Local Key** is required (auto-filled when discovered via cloud)
- Device **IP address** (auto-detected via LAN scan, or enter manually)

Use the **Scan LAN** button to find local devices on the network.

## Optional — Manual Device Addition

If you don't want to use the cloud, you can add devices manually:

1. Click **Add Device**
2. Enter:
   - **Device ID** — from the Tuya app (Device Info → Virtual ID) or from the device itself
   - **Device Name** — friendly name
   - **Local Key** — required for local control (can be obtained via tinytuya wizard or cloud API)
   - **IP Address** — device IP on local network
   - **Category** — device type (determines available DPS codes)
3. Click **Add Device**

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Cloud shows "Disconnected" | Check Access ID, Secret, and Region; make sure the project is active on iot.tuya.com |
| Discover finds 0 devices | Make sure you linked your app account to the cloud project (Step 4) |
| Device shows "Offline" | Check if device is powered on and connected to Wi-Fi |
| Local control doesn't work | Verify Local Key and IP; make sure the device is on the same network |
| DPS list is empty | Category may be "unknown" — edit the device and set the correct category |
| Commands not sent | Check if DPS is not marked as Read-only; check logs for errors |

## Cloud API Limits

Tuya IoT Platform has usage limits depending on your subscription plan:

| | Trial (free) | Flagship | Corporate |
|---|---|---|---|
| **Price** | Free | Paid subscription | Paid subscription |
| **Max devices** | **50** | 75,000 | 200,000 |
| **Controllable devices** | **10** | 30,000 | 75,000 |
| **API calls/month** | ~**26,000** | ~224 million | ~426 million |
| **Messages/month** | ~**68,000** | ~568 million | ~1 billion |
| **Data centers** | **1** region | 7 regions | 7 regions |
| **Log retention** | None | 72 hours | 168 hours |

### Trial Edition limitations

- **50 devices** max in a project
- **10 controllable** — only 10 devices can receive commands via Cloud API
- **~26,000 API calls/month** — polling 1 device every 30s = ~86,400 calls/month, so roughly **9 devices** max with constant polling
- **When the limit is reached, the service is suspended** until the next month (no overage charges)
- **Commercial use is prohibited**

### Recommended configuration

Use **Connection Mode: Both** (cloud + local) to minimize cloud API usage:

| Function | Channel | Counts toward API limit? |
|----------|---------|--------------------------|
| Device discovery | Cloud | Yes (one-time) |
| DPS specification | Cloud | Yes (one-time per device) |
| Real-time push (Pulsar) | Cloud | Messages, not API calls |
| Status polling | **Local (LAN)** | **No** |
| Send commands | **Local (LAN)** | **No** |
| Fallback commands | Cloud | Yes |

With local control as the primary channel, the cloud API is only used for discovery and push notifications, keeping usage well within the free tier limits even with dozens of devices.
