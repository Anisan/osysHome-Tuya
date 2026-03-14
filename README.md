# Tuya Plugin

Integration plugin for Tuya ecosystem devices in osysHome smart home system.

## Features

- **Cloud Control**: Uses Tuya IoT Platform API with MQTT push notifications
- **Local Control**: Direct LAN control via tinytuya (no cloud latency)
- **Auto Discovery**: Automatically discovers devices from Tuya account
- **Manual Add**: Add devices manually with device ID and local key
- **Universal Support**: Supports switches, lights, sensors, climate, covers, and more

## Configuration

1. Create a Cloud Project on [iot.tuya.com](https://iot.tuya.com)
2. Obtain Access ID and Access Secret
3. Link your Smart Life/Tuya Smart app account
4. Configure the plugin in the admin panel

## Supported Device Types

- Switches and outlets
- Smart lights (RGB, dimmers)
- Sensors (temperature, humidity, motion, door)
- Climate devices (thermostats, air conditioners)
- Covers (curtains, blinds)
- All other devices via universal DPS mapping
