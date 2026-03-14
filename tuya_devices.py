"""
Tuya DPS reference — maps device categories to their known Data Point Standard codes.

Used by the Link UI to show available DPS for a device category so the user
can bind them to existing system object properties.

Source: https://developer.tuya.com/en/docs/iot/standarddescription?id=K9i5ql6waswzq
"""

import logging
from typing import Dict, List, Optional
from app.core.lib.constants import PropertyType


class TuyaDPSReference:
    """Reference table of Tuya device categories and their typical DPS codes."""

    CATEGORY_MAPPINGS = {
        # ══════════════════════════════════════════════════════════════
        #  LIGHTING
        # ══════════════════════════════════════════════════════════════

        "dj": {
            "label": "Light",
            "dps": {
                "switch_led":       {"type": PropertyType.Bool,    "dp_id": 20, "writable": True,  "label": "On/Off"},
                "work_mode":        {"type": PropertyType.String,  "dp_id": 21, "writable": True,  "label": "Mode (white/colour/scene/music)"},
                "bright_value":     {"type": PropertyType.Integer, "dp_id": 22, "writable": True,  "label": "Brightness v1 (25-255)"},
                "bright_value_v2":  {"type": PropertyType.Integer, "dp_id": 22, "writable": True,  "label": "Brightness v2 (10-1000)"},
                "temp_value":       {"type": PropertyType.Integer, "dp_id": 23, "writable": True,  "label": "Color Temp v1 (0-255)"},
                "temp_value_v2":    {"type": PropertyType.Integer, "dp_id": 23, "writable": True,  "label": "Color Temp v2 (0-1000)"},
                "colour_data":      {"type": PropertyType.String,  "dp_id": 24, "writable": True,  "label": "Colour HSV data v1"},
                "colour_data_v2":   {"type": PropertyType.String,  "dp_id": 24, "writable": True,  "label": "Colour HSV data v2"},
                "scene_data":       {"type": PropertyType.String,  "dp_id": 25, "writable": True,  "label": "Scene data v1"},
                "scene_data_v2":    {"type": PropertyType.String,  "dp_id": 25, "writable": True,  "label": "Scene data v2"},
                "flash_scene_1":    {"type": PropertyType.String,  "dp_id": 26, "writable": True,  "label": "Soft light mode"},
                "flash_scene_2":    {"type": PropertyType.String,  "dp_id": 27, "writable": True,  "label": "Colorful mode"},
                "flash_scene_3":    {"type": PropertyType.String,  "dp_id": 28, "writable": True,  "label": "Dazzling mode"},
                "flash_scene_4":    {"type": PropertyType.String,  "dp_id": 29, "writable": True,  "label": "Gorgeous mode"},
                "music_data":       {"type": PropertyType.String,  "dp_id": 27, "writable": True,  "label": "Music light control"},
                "control_data":     {"type": PropertyType.String,  "dp_id": 28, "writable": True,  "label": "Adjust DP control"},
                "countdown_1":      {"type": PropertyType.Integer, "dp_id": 26, "writable": True,  "label": "Countdown (s)"},
                "do_not_disturb":   {"type": PropertyType.Bool,    "dp_id": 34, "writable": True,  "label": "Do not disturb"},
                "rhythm_mode":      {"type": PropertyType.String,  "dp_id": 30, "writable": True,  "label": "Circadian rhythm"},
                "sleep_mode":       {"type": PropertyType.String,  "dp_id": 31, "writable": True,  "label": "Sleep mode"},
                "wakeup_mode":      {"type": PropertyType.String,  "dp_id": 32, "writable": True,  "label": "Wake-up mode"},
            },
        },
        "xdd": {
            "label": "Ceiling Light",
            "dps": {
                "switch_led":       {"type": PropertyType.Bool,    "dp_id": 20, "writable": True,  "label": "On/Off"},
                "work_mode":        {"type": PropertyType.String,  "dp_id": 21, "writable": True,  "label": "Mode"},
                "bright_value_v2":  {"type": PropertyType.Integer, "dp_id": 22, "writable": True,  "label": "Brightness (10-1000)"},
                "temp_value_v2":    {"type": PropertyType.Integer, "dp_id": 23, "writable": True,  "label": "Color Temp (0-1000)"},
                "scene_data_v2":    {"type": PropertyType.String,  "dp_id": 25, "writable": True,  "label": "Scene data"},
                "countdown_1":      {"type": PropertyType.Integer, "dp_id": 26, "writable": True,  "label": "Countdown (s)"},
                "sleep_mode":       {"type": PropertyType.String,  "dp_id": 31, "writable": True,  "label": "Sleep mode"},
                "wakeup_mode":      {"type": PropertyType.String,  "dp_id": 32, "writable": True,  "label": "Wake-up mode"},
                "do_not_disturb":   {"type": PropertyType.Bool,    "dp_id": 34, "writable": True,  "label": "Do not disturb"},
            },
        },
        "fwd": {
            "label": "Ambiance Light",
            "dps": {
                "switch_led":       {"type": PropertyType.Bool,    "dp_id": 20, "writable": True,  "label": "On/Off"},
                "work_mode":        {"type": PropertyType.String,  "dp_id": 21, "writable": True,  "label": "Mode"},
                "bright_value_v2":  {"type": PropertyType.Integer, "dp_id": 22, "writable": True,  "label": "Brightness (10-1000)"},
                "temp_value_v2":    {"type": PropertyType.Integer, "dp_id": 23, "writable": True,  "label": "Color Temp (0-1000)"},
                "colour_data_v2":   {"type": PropertyType.String,  "dp_id": 24, "writable": True,  "label": "Colour HSV data"},
                "scene_data_v2":    {"type": PropertyType.String,  "dp_id": 25, "writable": True,  "label": "Scene data"},
                "countdown_1":      {"type": PropertyType.Integer, "dp_id": 26, "writable": True,  "label": "Countdown (s)"},
                "music_data":       {"type": PropertyType.String,  "dp_id": 27, "writable": True,  "label": "Music light control"},
            },
        },
        "dc": {
            "label": "String Lights",
            "dps": {
                "switch_led":       {"type": PropertyType.Bool,    "dp_id": 20, "writable": True,  "label": "On/Off"},
                "work_mode":        {"type": PropertyType.String,  "dp_id": 21, "writable": True,  "label": "Mode"},
                "bright_value_v2":  {"type": PropertyType.Integer, "dp_id": 22, "writable": True,  "label": "Brightness (10-1000)"},
                "scene_data_v2":    {"type": PropertyType.String,  "dp_id": 25, "writable": True,  "label": "Scene data"},
            },
        },
        "dd": {
            "label": "Strip Lights",
            "dps": {
                "switch_led":       {"type": PropertyType.Bool,    "dp_id": 20, "writable": True,  "label": "On/Off"},
                "work_mode":        {"type": PropertyType.String,  "dp_id": 21, "writable": True,  "label": "Mode"},
                "bright_value_v2":  {"type": PropertyType.Integer, "dp_id": 22, "writable": True,  "label": "Brightness (10-1000)"},
                "temp_value_v2":    {"type": PropertyType.Integer, "dp_id": 23, "writable": True,  "label": "Color Temp (0-1000)"},
                "colour_data_v2":   {"type": PropertyType.String,  "dp_id": 24, "writable": True,  "label": "Colour HSV data"},
                "scene_data_v2":    {"type": PropertyType.String,  "dp_id": 25, "writable": True,  "label": "Scene data"},
                "music_data":       {"type": PropertyType.String,  "dp_id": 27, "writable": True,  "label": "Music light control"},
            },
        },
        "gyd": {
            "label": "Motion Sensor Light",
            "dps": {
                "switch_led":       {"type": PropertyType.Bool,    "dp_id": 20, "writable": True,  "label": "On/Off"},
                "work_mode":        {"type": PropertyType.String,  "dp_id": 21, "writable": True,  "label": "Mode"},
                "bright_value_v2":  {"type": PropertyType.Integer, "dp_id": 22, "writable": True,  "label": "Brightness (10-1000)"},
                "temp_value_v2":    {"type": PropertyType.Integer, "dp_id": 23, "writable": True,  "label": "Color Temp (0-1000)"},
                "standby_bright":   {"type": PropertyType.Integer, "dp_id": 44, "writable": True,  "label": "Standby brightness"},
                "pir_sensitivity":  {"type": PropertyType.String,  "dp_id": 43, "writable": True,  "label": "PIR sensitivity"},
                "cds":              {"type": PropertyType.String,  "dp_id": 45, "writable": True,  "label": "Light sensitivity"},
                "standby_time":     {"type": PropertyType.Integer, "dp_id": 46, "writable": True,  "label": "Standby time (s)"},
            },
        },
        "fsd": {
            "label": "Ceiling Fan Light",
            "dps": {
                "switch_led":       {"type": PropertyType.Bool,    "dp_id": 20, "writable": True,  "label": "Light On/Off"},
                "work_mode":        {"type": PropertyType.String,  "dp_id": 21, "writable": True,  "label": "Light Mode"},
                "bright_value_v2":  {"type": PropertyType.Integer, "dp_id": 22, "writable": True,  "label": "Brightness (10-1000)"},
                "temp_value_v2":    {"type": PropertyType.Integer, "dp_id": 23, "writable": True,  "label": "Color Temp (0-1000)"},
                "fan_switch":       {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Fan On/Off"},
                "fan_speed":        {"type": PropertyType.Integer, "dp_id": 3,  "writable": True,  "label": "Fan Speed"},
                "fan_direction":    {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Fan Direction (forward/reverse)"},
            },
        },
        "tyndj": {
            "label": "Solar Light",
            "dps": {
                "switch_led":       {"type": PropertyType.Bool,    "dp_id": 20, "writable": True,  "label": "On/Off"},
                "work_mode":        {"type": PropertyType.String,  "dp_id": 21, "writable": True,  "label": "Mode"},
                "bright_value_v2":  {"type": PropertyType.Integer, "dp_id": 22, "writable": True,  "label": "Brightness (10-1000)"},
                "colour_data_v2":   {"type": PropertyType.String,  "dp_id": 24, "writable": True,  "label": "Colour HSV data"},
            },
        },
        "tgq": {
            "label": "Dimmer",
            "dps": {
                "switch_led_1":     {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Dimmer 1 On/Off"},
                "bright_value_1":   {"type": PropertyType.Integer, "dp_id": 2,  "writable": True,  "label": "Dimmer 1 Brightness (10-1000)"},
                "brightness_min_1": {"type": PropertyType.Integer, "dp_id": 3,  "writable": True,  "label": "Dimmer 1 Min Brightness"},
                "led_type_1":       {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Dimmer 1 LED Type"},
                "switch_led_2":     {"type": PropertyType.Bool,    "dp_id": 5,  "writable": True,  "label": "Dimmer 2 On/Off"},
                "bright_value_2":   {"type": PropertyType.Integer, "dp_id": 6,  "writable": True,  "label": "Dimmer 2 Brightness (10-1000)"},
            },
        },
        "sxd": {
            "label": "Spotlight",
            "dps": {
                "switch_led":       {"type": PropertyType.Bool,    "dp_id": 20, "writable": True,  "label": "On/Off"},
                "work_mode":        {"type": PropertyType.String,  "dp_id": 21, "writable": True,  "label": "Mode"},
                "bright_value_v2":  {"type": PropertyType.Integer, "dp_id": 22, "writable": True,  "label": "Brightness (10-1000)"},
                "temp_value_v2":    {"type": PropertyType.Integer, "dp_id": 23, "writable": True,  "label": "Color Temp (0-1000)"},
                "colour_data_v2":   {"type": PropertyType.String,  "dp_id": 24, "writable": True,  "label": "Colour HSV data"},
            },
        },
        "ykq": {
            "label": "Remote Control (Lighting)",
            "dps": {
                "switch_led":       {"type": PropertyType.Bool,    "dp_id": 20, "writable": True,  "label": "On/Off"},
                "work_mode":        {"type": PropertyType.String,  "dp_id": 21, "writable": True,  "label": "Mode"},
                "bright_value_v2":  {"type": PropertyType.Integer, "dp_id": 22, "writable": True,  "label": "Brightness"},
                "temp_value_v2":    {"type": PropertyType.Integer, "dp_id": 23, "writable": True,  "label": "Color Temp"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  ELECTRICAL PRODUCTS — Switches, Sockets, Power Strips
        # ══════════════════════════════════════════════════════════════

        "kg": {
            "label": "Switch",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Switch"},
                "switch_1":         {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Switch 1"},
                "switch_2":         {"type": PropertyType.Bool,    "dp_id": 2,  "writable": True,  "label": "Switch 2"},
                "switch_3":         {"type": PropertyType.Bool,    "dp_id": 3,  "writable": True,  "label": "Switch 3"},
                "switch_4":         {"type": PropertyType.Bool,    "dp_id": 4,  "writable": True,  "label": "Switch 4"},
                "switch_5":         {"type": PropertyType.Bool,    "dp_id": 5,  "writable": True,  "label": "Switch 5"},
                "switch_6":         {"type": PropertyType.Bool,    "dp_id": 6,  "writable": True,  "label": "Switch 6"},
                "countdown_1":      {"type": PropertyType.Integer, "dp_id": 7,  "writable": True,  "label": "Countdown 1 (s)"},
                "countdown_2":      {"type": PropertyType.Integer, "dp_id": 8,  "writable": True,  "label": "Countdown 2 (s)"},
                "countdown_3":      {"type": PropertyType.Integer, "dp_id": 9,  "writable": True,  "label": "Countdown 3 (s)"},
                "countdown_4":      {"type": PropertyType.Integer, "dp_id": 10, "writable": True,  "label": "Countdown 4 (s)"},
                "countdown_5":      {"type": PropertyType.Integer, "dp_id": 11, "writable": True,  "label": "Countdown 5 (s)"},
                "countdown_6":      {"type": PropertyType.Integer, "dp_id": 12, "writable": True,  "label": "Countdown 6 (s)"},
                "child_lock":       {"type": PropertyType.Bool,    "dp_id": 13, "writable": True,  "label": "Child Lock"},
                "relay_status":     {"type": PropertyType.String,  "dp_id": 14, "writable": True,  "label": "Power-on State (last/on/off)"},
                "switch_backlight": {"type": PropertyType.Bool,    "dp_id": 16, "writable": True,  "label": "Backlight"},
            },
        },
        "cz": {
            "label": "Socket / Smart Plug",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Switch"},
                "switch_1":         {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Switch 1"},
                "switch_2":         {"type": PropertyType.Bool,    "dp_id": 2,  "writable": True,  "label": "Switch 2"},
                "countdown_1":      {"type": PropertyType.Integer, "dp_id": 9,  "writable": True,  "label": "Countdown 1 (s)"},
                "countdown_2":      {"type": PropertyType.Integer, "dp_id": 10, "writable": True,  "label": "Countdown 2 (s)"},
                "cur_current":      {"type": PropertyType.Integer, "dp_id": 18, "writable": False, "label": "Current (mA)"},
                "cur_power":        {"type": PropertyType.Integer, "dp_id": 19, "writable": False, "label": "Power (0.1 W)"},
                "cur_voltage":      {"type": PropertyType.Integer, "dp_id": 20, "writable": False, "label": "Voltage (0.1 V)"},
                "child_lock":       {"type": PropertyType.Bool,    "dp_id": 13, "writable": True,  "label": "Child Lock"},
                "relay_status":     {"type": PropertyType.String,  "dp_id": 14, "writable": True,  "label": "Power-on State"},
                "switch_backlight": {"type": PropertyType.Bool,    "dp_id": 16, "writable": True,  "label": "Backlight"},
            },
        },
        "pc": {
            "label": "Power Strip",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Master Switch"},
                "switch_1":         {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Switch 1"},
                "switch_2":         {"type": PropertyType.Bool,    "dp_id": 2,  "writable": True,  "label": "Switch 2"},
                "switch_3":         {"type": PropertyType.Bool,    "dp_id": 3,  "writable": True,  "label": "Switch 3"},
                "switch_4":         {"type": PropertyType.Bool,    "dp_id": 4,  "writable": True,  "label": "Switch 4"},
                "switch_5":         {"type": PropertyType.Bool,    "dp_id": 5,  "writable": True,  "label": "Switch 5"},
                "switch_6":         {"type": PropertyType.Bool,    "dp_id": 6,  "writable": True,  "label": "Switch 6"},
                "switch_usb1":      {"type": PropertyType.Bool,    "dp_id": 7,  "writable": True,  "label": "USB 1"},
                "switch_usb2":      {"type": PropertyType.Bool,    "dp_id": 8,  "writable": True,  "label": "USB 2"},
                "switch_usb3":      {"type": PropertyType.Bool,    "dp_id": 9,  "writable": True,  "label": "USB 3"},
                "switch_usb4":      {"type": PropertyType.Bool,    "dp_id": 10, "writable": True,  "label": "USB 4"},
                "countdown_1":      {"type": PropertyType.Integer, "dp_id": 11, "writable": True,  "label": "Countdown 1 (s)"},
                "countdown_2":      {"type": PropertyType.Integer, "dp_id": 12, "writable": True,  "label": "Countdown 2 (s)"},
                "countdown_usb1":   {"type": PropertyType.Integer, "dp_id": 15, "writable": True,  "label": "USB 1 Countdown (s)"},
                "cur_current":      {"type": PropertyType.Integer, "dp_id": 18, "writable": False, "label": "Current (mA)"},
                "cur_power":        {"type": PropertyType.Integer, "dp_id": 19, "writable": False, "label": "Power (0.1 W)"},
                "cur_voltage":      {"type": PropertyType.Integer, "dp_id": 20, "writable": False, "label": "Voltage (0.1 V)"},
                "child_lock":       {"type": PropertyType.Bool,    "dp_id": 13, "writable": True,  "label": "Child Lock"},
            },
        },
        "cjkg": {
            "label": "Scene Switch",
            "dps": {
                "switch1_value":    {"type": PropertyType.String,  "dp_id": 1,  "writable": True,  "label": "Scene 1"},
                "switch2_value":    {"type": PropertyType.String,  "dp_id": 2,  "writable": True,  "label": "Scene 2"},
                "switch3_value":    {"type": PropertyType.String,  "dp_id": 3,  "writable": True,  "label": "Scene 3"},
                "switch4_value":    {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Scene 4"},
                "switch_backlight": {"type": PropertyType.Bool,    "dp_id": 13, "writable": True,  "label": "Backlight"},
            },
        },
        "wxkg": {
            "label": "Wireless Switch",
            "dps": {
                "switch1_value":    {"type": PropertyType.String,  "dp_id": 1,  "writable": False, "label": "Button 1 Action"},
                "switch2_value":    {"type": PropertyType.String,  "dp_id": 2,  "writable": False, "label": "Button 2 Action"},
                "switch3_value":    {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "Button 3 Action"},
                "switch4_value":    {"type": PropertyType.String,  "dp_id": 4,  "writable": False, "label": "Button 4 Action"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 10, "writable": False, "label": "Battery %"},
            },
        },
        "tgkg": {
            "label": "Dimmer Switch",
            "dps": {
                "switch_led_1":     {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Switch 1"},
                "bright_value_1":   {"type": PropertyType.Integer, "dp_id": 2,  "writable": True,  "label": "Brightness 1 (10-1000)"},
                "brightness_min_1": {"type": PropertyType.Integer, "dp_id": 3,  "writable": True,  "label": "Min Brightness 1"},
                "switch_led_2":     {"type": PropertyType.Bool,    "dp_id": 5,  "writable": True,  "label": "Switch 2"},
                "bright_value_2":   {"type": PropertyType.Integer, "dp_id": 6,  "writable": True,  "label": "Brightness 2 (10-1000)"},
            },
        },
        "clkg": {
            "label": "Curtain Switch",
            "dps": {
                "control":          {"type": PropertyType.String,  "dp_id": 1,  "writable": True,  "label": "Control (open/stop/close)"},
                "percent_control":  {"type": PropertyType.Integer, "dp_id": 2,  "writable": True,  "label": "Position (0-100)"},
                "cur_calibration":  {"type": PropertyType.String,  "dp_id": 3,  "writable": True,  "label": "Calibration"},
                "control_back_mode": {"type": PropertyType.String, "dp_id": 5,  "writable": True,  "label": "Motor direction"},
            },
        },
        "ckqdkg": {
            "label": "Card Switch",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Switch"},
            },
        },
        "ckmkzq": {
            "label": "Garage Door Opener",
            "dps": {
                "switch_1":         {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Switch"},
                "door_control_1":   {"type": PropertyType.String,  "dp_id": 2,  "writable": True,  "label": "Control (open/close/stop)"},
                "door_state_1":     {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "Door State"},
                "countdown_1":      {"type": PropertyType.Integer, "dp_id": 4,  "writable": True,  "label": "Countdown (s)"},
            },
        },
        "fskg": {
            "label": "Fan Switch",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Switch"},
                "fan_speed":        {"type": PropertyType.Integer, "dp_id": 2,  "writable": True,  "label": "Fan Speed"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  LARGE HOME APPLIANCES
        # ══════════════════════════════════════════════════════════════

        "kt": {
            "label": "Air Conditioner",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "On/Off"},
                "temp_set":         {"type": PropertyType.Integer, "dp_id": 2,  "writable": True,  "label": "Target Temperature"},
                "temp_current":     {"type": PropertyType.Integer, "dp_id": 3,  "writable": False, "label": "Current Temperature"},
                "mode":             {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Mode (cold/hot/wind/auto)"},
                "fan_speed_enum":   {"type": PropertyType.String,  "dp_id": 5,  "writable": True,  "label": "Fan Speed (auto/low/mid/high)"},
                "switch_vertical":  {"type": PropertyType.Bool,    "dp_id": 104,"writable": True,  "label": "Swing Vertical"},
                "switch_horizontal": {"type": PropertyType.Bool,   "dp_id": 105,"writable": True,  "label": "Swing Horizontal"},
                "temp_current_f":   {"type": PropertyType.Integer, "dp_id": 106,"writable": False, "label": "Current Temp (°F)"},
                "countdown":        {"type": PropertyType.String,  "dp_id": 6,  "writable": True,  "label": "Countdown"},
                "sleep":            {"type": PropertyType.Bool,    "dp_id": 7,  "writable": True,  "label": "Sleep Mode"},
            },
        },
        "wk": {
            "label": "Thermostat",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "On/Off"},
                "temp_set":         {"type": PropertyType.Integer, "dp_id": 2,  "writable": True,  "label": "Target Temperature"},
                "temp_current":     {"type": PropertyType.Integer, "dp_id": 3,  "writable": False, "label": "Current Temperature"},
                "mode":             {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Mode (manual/auto/holiday)"},
                "child_lock":       {"type": PropertyType.Bool,    "dp_id": 7,  "writable": True,  "label": "Child Lock"},
                "upper_temp":       {"type": PropertyType.Integer, "dp_id": 19, "writable": True,  "label": "Upper Temp Limit"},
                "lower_temp":       {"type": PropertyType.Integer, "dp_id": 20, "writable": True,  "label": "Lower Temp Limit"},
                "temp_correction":  {"type": PropertyType.Integer, "dp_id": 27, "writable": True,  "label": "Temperature Correction"},
                "valve_state":      {"type": PropertyType.String,  "dp_id": 36, "writable": False, "label": "Valve State"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 37, "writable": False, "label": "Battery %"},
            },
        },
        "cl": {
            "label": "Curtain / Cover",
            "dps": {
                "control":          {"type": PropertyType.String,  "dp_id": 1,  "writable": True,  "label": "Control (open/stop/close)"},
                "percent_control":  {"type": PropertyType.Integer, "dp_id": 2,  "writable": True,  "label": "Position Set (0-100)"},
                "percent_state":    {"type": PropertyType.Integer, "dp_id": 3,  "writable": False, "label": "Position Current"},
                "mode":             {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Mode (morning/night)"},
                "control_back_mode": {"type": PropertyType.String, "dp_id": 5,  "writable": True,  "label": "Motor direction (forward/back)"},
                "work_state":       {"type": PropertyType.String,  "dp_id": 7,  "writable": False, "label": "Work state (opening/closing)"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  SMALL HOME APPLIANCES
        # ══════════════════════════════════════════════════════════════

        "fs": {
            "label": "Fan",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "On/Off"},
                "fan_speed":        {"type": PropertyType.Integer, "dp_id": 3,  "writable": True,  "label": "Speed (1-100)"},
                "fan_speed_enum":   {"type": PropertyType.String,  "dp_id": 2,  "writable": True,  "label": "Speed (low/mid/high)"},
                "mode":             {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Mode (normal/nature/sleep)"},
                "switch_horizontal": {"type": PropertyType.Bool,   "dp_id": 8,  "writable": True,  "label": "Oscillation Horizontal"},
                "switch_vertical":  {"type": PropertyType.Bool,    "dp_id": 9,  "writable": True,  "label": "Oscillation Vertical"},
                "countdown":        {"type": PropertyType.String,  "dp_id": 22, "writable": True,  "label": "Countdown"},
                "child_lock":       {"type": PropertyType.Bool,    "dp_id": 7,  "writable": True,  "label": "Child Lock"},
                "temp_current":     {"type": PropertyType.Integer, "dp_id": 106,"writable": False, "label": "Temperature"},
                "humidity_current": {"type": PropertyType.Integer, "dp_id": 107,"writable": False, "label": "Humidity"},
            },
        },
        "jsq": {
            "label": "Humidifier",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "On/Off"},
                "mode":             {"type": PropertyType.String,  "dp_id": 2,  "writable": True,  "label": "Mode (small/middle/large)"},
                "humidity_set":     {"type": PropertyType.Integer, "dp_id": 4,  "writable": True,  "label": "Target Humidity (0-100)"},
                "humidity_current": {"type": PropertyType.Integer, "dp_id": 6,  "writable": False, "label": "Current Humidity"},
                "temp_current":     {"type": PropertyType.Integer, "dp_id": 7,  "writable": False, "label": "Current Temperature"},
                "switch_sound":     {"type": PropertyType.Bool,    "dp_id": 5,  "writable": True,  "label": "Sound On/Off"},
                "countdown":        {"type": PropertyType.String,  "dp_id": 11, "writable": True,  "label": "Countdown"},
                "switch_led":       {"type": PropertyType.Bool,    "dp_id": 8,  "writable": True,  "label": "LED On/Off"},
                "child_lock":       {"type": PropertyType.Bool,    "dp_id": 12, "writable": True,  "label": "Child Lock"},
            },
        },
        "cs": {
            "label": "Dehumidifier",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "On/Off"},
                "mode":             {"type": PropertyType.String,  "dp_id": 2,  "writable": True,  "label": "Mode"},
                "humidity_set":     {"type": PropertyType.Integer, "dp_id": 4,  "writable": True,  "label": "Target Humidity"},
                "humidity_current": {"type": PropertyType.Integer, "dp_id": 6,  "writable": False, "label": "Current Humidity"},
                "temp_current":     {"type": PropertyType.Integer, "dp_id": 7,  "writable": False, "label": "Current Temperature"},
                "fan_speed_enum":   {"type": PropertyType.String,  "dp_id": 5,  "writable": True,  "label": "Fan Speed"},
                "child_lock":       {"type": PropertyType.Bool,    "dp_id": 16, "writable": True,  "label": "Child Lock"},
                "countdown":        {"type": PropertyType.String,  "dp_id": 11, "writable": True,  "label": "Countdown"},
            },
        },
        "kj": {
            "label": "Air Purifier",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "On/Off"},
                "mode":             {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Mode (auto/manual/sleep)"},
                "fan_speed_enum":   {"type": PropertyType.String,  "dp_id": 5,  "writable": True,  "label": "Fan Speed"},
                "pm25":             {"type": PropertyType.Integer, "dp_id": 2,  "writable": False, "label": "PM2.5 (µg/m³)"},
                "filter_life":      {"type": PropertyType.Integer, "dp_id": 5,  "writable": False, "label": "Filter Life (%)"},
                "child_lock":       {"type": PropertyType.Bool,    "dp_id": 7,  "writable": True,  "label": "Child Lock"},
                "air_quality":      {"type": PropertyType.String,  "dp_id": 21, "writable": False, "label": "Air Quality Index"},
                "countdown":        {"type": PropertyType.String,  "dp_id": 19, "writable": True,  "label": "Countdown"},
                "switch_uv":        {"type": PropertyType.Bool,    "dp_id": 9,  "writable": True,  "label": "UV Switch"},
                "switch_sound":     {"type": PropertyType.Bool,    "dp_id": 11, "writable": True,  "label": "Sound On/Off"},
            },
        },
        "qn": {
            "label": "Heater",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "On/Off"},
                "temp_set":         {"type": PropertyType.Integer, "dp_id": 2,  "writable": True,  "label": "Target Temperature"},
                "temp_current":     {"type": PropertyType.Integer, "dp_id": 3,  "writable": False, "label": "Current Temperature"},
                "mode":             {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Mode"},
                "child_lock":       {"type": PropertyType.Bool,    "dp_id": 7,  "writable": True,  "label": "Child Lock"},
                "countdown":        {"type": PropertyType.String,  "dp_id": 19, "writable": True,  "label": "Countdown"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  SENSORS
        # ══════════════════════════════════════════════════════════════

        "wsdcg": {
            "label": "Temperature & Humidity Sensor",
            "dps": {
                "va_temperature":     {"type": PropertyType.Integer, "dp_id": 1,  "writable": False, "label": "Temperature"},
                "va_humidity":        {"type": PropertyType.Integer, "dp_id": 2,  "writable": False, "label": "Humidity"},
                "battery_state":      {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "Battery State (low/mid/high)"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Battery %"},
                "temp_unit_convert":  {"type": PropertyType.String,  "dp_id": 9,  "writable": True,  "label": "Temp Unit (c/f)"},
                "maxtemp_set":        {"type": PropertyType.Integer, "dp_id": 18, "writable": True,  "label": "Max Temp Alert"},
                "mintemp_set":        {"type": PropertyType.Integer, "dp_id": 19, "writable": True,  "label": "Min Temp Alert"},
                "maxhum_set":         {"type": PropertyType.Integer, "dp_id": 20, "writable": True,  "label": "Max Hum Alert"},
                "minhum_set":         {"type": PropertyType.Integer, "dp_id": 21, "writable": True,  "label": "Min Hum Alert"},
                "temp_alarm":         {"type": PropertyType.String,  "dp_id": 14, "writable": False, "label": "Temp Alarm"},
                "hum_alarm":          {"type": PropertyType.String,  "dp_id": 15, "writable": False, "label": "Hum Alarm"},
            },
        },
        "mcs": {
            "label": "Door / Window Sensor",
            "dps": {
                "doorcontact_state":  {"type": PropertyType.Bool,    "dp_id": 1,  "writable": False, "label": "Door State (true=open)"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 2,  "writable": False, "label": "Battery %"},
                "battery_state":      {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "Battery State"},
            },
        },
        "pir": {
            "label": "Motion Sensor (PIR)",
            "dps": {
                "pir":                {"type": PropertyType.String,  "dp_id": 1,  "writable": False, "label": "Motion Status (pir/none)"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Battery %"},
                "battery_state":      {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "Battery State"},
                "sensitivity":        {"type": PropertyType.String,  "dp_id": 9,  "writable": True,  "label": "Sensitivity (low/mid/high)"},
            },
        },
        "ywbj": {
            "label": "Smoke Detector",
            "dps": {
                "smoke_sensor_state": {"type": PropertyType.String,  "dp_id": 1,  "writable": False, "label": "Alarm State (alarm/normal)"},
                "smoke_sensor_value": {"type": PropertyType.Integer, "dp_id": 2,  "writable": False, "label": "Smoke Concentration"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Battery %"},
                "battery_state":      {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "Battery State"},
                "muffling":           {"type": PropertyType.Bool,    "dp_id": 14, "writable": True,  "label": "Mute Alarm"},
            },
        },
        "rqbj": {
            "label": "Gas Detector",
            "dps": {
                "gas_sensor_state":   {"type": PropertyType.String,  "dp_id": 1,  "writable": False, "label": "Alarm State (alarm/normal)"},
                "gas_sensor_value":   {"type": PropertyType.Integer, "dp_id": 2,  "writable": False, "label": "Gas Concentration"},
                "self_checking":      {"type": PropertyType.Bool,    "dp_id": 8,  "writable": True,  "label": "Self-check"},
                "muffling":           {"type": PropertyType.Bool,    "dp_id": 14, "writable": True,  "label": "Mute Alarm"},
            },
        },
        "sj": {
            "label": "Water Leak Sensor",
            "dps": {
                "watersensor_state":  {"type": PropertyType.String,  "dp_id": 1,  "writable": False, "label": "Leak State (alarm/normal)"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Battery %"},
                "battery_state":      {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "Battery State"},
            },
        },
        "ldcg": {
            "label": "Luminance Sensor",
            "dps": {
                "bright_value":       {"type": PropertyType.Integer, "dp_id": 2,  "writable": False, "label": "Luminance (lux)"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Battery %"},
                "battery_state":      {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "Battery State"},
            },
        },
        "pm25": {
            "label": "PM2.5 Sensor",
            "dps": {
                "pm25_value":         {"type": PropertyType.Integer, "dp_id": 2,  "writable": False, "label": "PM2.5 (µg/m³)"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Battery %"},
                "battery_state":      {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "Battery State"},
            },
        },
        "co2bj": {
            "label": "CO2 Sensor",
            "dps": {
                "co2_value":          {"type": PropertyType.Integer, "dp_id": 2,  "writable": False, "label": "CO2 (ppm)"},
                "voc_value":          {"type": PropertyType.Integer, "dp_id": 22, "writable": False, "label": "VOC"},
                "ch2o_value":         {"type": PropertyType.Integer, "dp_id": 21, "writable": False, "label": "Formaldehyde (CH₂O)"},
                "va_temperature":     {"type": PropertyType.Integer, "dp_id": 18, "writable": False, "label": "Temperature"},
                "va_humidity":        {"type": PropertyType.Integer, "dp_id": 19, "writable": False, "label": "Humidity"},
            },
        },
        "sgbj": {
            "label": "Siren / Alarm",
            "dps": {
                "alarm_switch":       {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Alarm On/Off"},
                "alarm_time":         {"type": PropertyType.Integer, "dp_id": 7,  "writable": True,  "label": "Alarm Duration (s)"},
                "alarm_volume":       {"type": PropertyType.String,  "dp_id": 5,  "writable": True,  "label": "Volume (low/mid/high/mute)"},
                "alarm_ringtone":     {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Ringtone"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 15, "writable": False, "label": "Battery %"},
            },
        },
        "vibration": {
            "label": "Vibration Sensor",
            "dps": {
                "shock_state":        {"type": PropertyType.String,  "dp_id": 1,  "writable": False, "label": "Vibration State"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Battery %"},
                "sensitivity":        {"type": PropertyType.String,  "dp_id": 9,  "writable": True,  "label": "Sensitivity"},
            },
        },
        "sos": {
            "label": "SOS Button",
            "dps": {
                "sos_state":          {"type": PropertyType.Bool,    "dp_id": 1,  "writable": False, "label": "SOS Pressed"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Battery %"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  LOCKS
        # ══════════════════════════════════════════════════════════════

        "ms": {
            "label": "Smart Lock",
            "dps": {
                "unlock_fingerprint": {"type": PropertyType.Integer, "dp_id": 1,  "writable": False, "label": "Fingerprint Unlock"},
                "unlock_password":    {"type": PropertyType.Integer, "dp_id": 2,  "writable": False, "label": "Password Unlock"},
                "unlock_card":        {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Card Unlock"},
                "unlock_temporary":   {"type": PropertyType.Integer, "dp_id": 3,  "writable": False, "label": "Temporary Unlock"},
                "unlock_app":         {"type": PropertyType.Integer, "dp_id": 5,  "writable": False, "label": "App Unlock"},
                "unlock_key":         {"type": PropertyType.Integer, "dp_id": 15, "writable": False, "label": "Key Unlock"},
                "alarm_lock":         {"type": PropertyType.String,  "dp_id": 21, "writable": False, "label": "Lock Alarm"},
                "closed_opened":      {"type": PropertyType.String,  "dp_id": 11, "writable": False, "label": "Door Open/Close"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 8,  "writable": False, "label": "Battery %"},
                "residual_electricity": {"type": PropertyType.Integer, "dp_id": 12, "writable": False, "label": "Battery Level"},
                "hijack":             {"type": PropertyType.Bool,    "dp_id": 22, "writable": False, "label": "Hijack Alarm"},
                "doorbell":           {"type": PropertyType.Bool,    "dp_id": 18, "writable": False, "label": "Doorbell Pressed"},
            },
        },
        "jtmspro": {
            "label": "Smart Lock Pro",
            "dps": {
                "unlock_fingerprint": {"type": PropertyType.Integer, "dp_id": 1,  "writable": False, "label": "Fingerprint Unlock"},
                "unlock_password":    {"type": PropertyType.Integer, "dp_id": 2,  "writable": False, "label": "Password Unlock"},
                "unlock_card":        {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Card Unlock"},
                "closed_opened":      {"type": PropertyType.String,  "dp_id": 11, "writable": False, "label": "Door Open/Close"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 8,  "writable": False, "label": "Battery %"},
                "alarm_lock":         {"type": PropertyType.String,  "dp_id": 21, "writable": False, "label": "Lock Alarm"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  VALVES
        # ══════════════════════════════════════════════════════════════

        "kgvalve": {
            "label": "Valve Controller",
            "dps": {
                "switch":             {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Valve On/Off"},
                "countdown_1":        {"type": PropertyType.Integer, "dp_id": 9,  "writable": True,  "label": "Countdown (s)"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Battery %"},
            },
        },
        "sfkzq": {
            "label": "Water Valve",
            "dps": {
                "switch":             {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Valve On/Off"},
                "water_total":        {"type": PropertyType.Integer, "dp_id": 7,  "writable": False, "label": "Water Usage (L)"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 4,  "writable": False, "label": "Battery %"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  IR REMOTE
        # ══════════════════════════════════════════════════════════════

        "wnykq": {
            "label": "IR Remote Control",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "On/Off"},
                "ir_send":          {"type": PropertyType.String,  "dp_id": 2,  "writable": True,  "label": "IR Send Code"},
                "ir_receive":       {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "IR Received Code"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  ROBOT VACUUM
        # ══════════════════════════════════════════════════════════════

        "sd": {
            "label": "Robot Vacuum",
            "dps": {
                "switch_go":        {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Start/Pause"},
                "pause":            {"type": PropertyType.Bool,    "dp_id": 2,  "writable": True,  "label": "Pause"},
                "status":           {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "Status"},
                "mode":             {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Clean Mode (smart/spiral/wall)"},
                "electricity_left": {"type": PropertyType.Integer, "dp_id": 5,  "writable": False, "label": "Battery %"},
                "direction_control": {"type": PropertyType.String, "dp_id": 6,  "writable": True,  "label": "Direction (forward/back/left/right)"},
                "suction":          {"type": PropertyType.String,  "dp_id": 5,  "writable": True,  "label": "Suction Power"},
                "clean_time":       {"type": PropertyType.Integer, "dp_id": 8,  "writable": False, "label": "Clean Time (min)"},
                "clean_area":       {"type": PropertyType.Integer, "dp_id": 9,  "writable": False, "label": "Clean Area (m²)"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  GATEWAY
        # ══════════════════════════════════════════════════════════════

        "wg": {
            "label": "Gateway",
            "dps": {
                "switch_alarm":     {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Alarm On/Off"},
                "alarm_ringtone":   {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Alarm Ringtone"},
                "alarm_volume":     {"type": PropertyType.String,  "dp_id": 5,  "writable": True,  "label": "Volume"},
                "master_mode":      {"type": PropertyType.String,  "dp_id": 13, "writable": True,  "label": "Arm Mode (arm/disarm/home)"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  CAMERAS / DOORBELLS
        # ══════════════════════════════════════════════════════════════

        "sp": {
            "label": "Smart Camera (IPC)",
            "dps": {
                "basic_private":    {"type": PropertyType.Bool,    "dp_id": 105, "writable": True,  "label": "Privacy Mode"},
                "basic_flip":       {"type": PropertyType.Bool,    "dp_id": 103, "writable": True,  "label": "Flip Image"},
                "basic_osd":        {"type": PropertyType.Bool,    "dp_id": 104, "writable": True,  "label": "OSD Timestamp"},
                "basic_nightvision": {"type": PropertyType.String, "dp_id": 108, "writable": True,  "label": "Night Vision (auto/on/off)"},
                "motion_switch":    {"type": PropertyType.Bool,    "dp_id": 134, "writable": True,  "label": "Motion Detection"},
                "motion_sensitivity": {"type": PropertyType.String, "dp_id": 106, "writable": True,  "label": "Motion Sensitivity (low/mid/high)"},
                "sd_status":        {"type": PropertyType.Integer, "dp_id": 110, "writable": False, "label": "SD Card Status"},
                "sd_storage":       {"type": PropertyType.String,  "dp_id": 109, "writable": False, "label": "SD Card Storage"},
                "ptz_control":      {"type": PropertyType.String,  "dp_id": 119, "writable": True,  "label": "PTZ Control"},
                "ptz_stop":         {"type": PropertyType.Bool,    "dp_id": 116, "writable": True,  "label": "PTZ Stop"},
                "siren_switch":     {"type": PropertyType.Bool,    "dp_id": 136, "writable": True,  "label": "Siren On/Off"},
                "record_switch":    {"type": PropertyType.Bool,    "dp_id": 150, "writable": True,  "label": "Record On/Off"},
                "record_mode":      {"type": PropertyType.String,  "dp_id": 151, "writable": True,  "label": "Record Mode (event/always)"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  DIGITAL ENTERTAINMENT
        # ══════════════════════════════════════════════════════════════

        "ds": {
            "label": "TV",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "On/Off"},
                "mute":             {"type": PropertyType.Bool,    "dp_id": 2,  "writable": True,  "label": "Mute"},
                "volume_set":       {"type": PropertyType.Integer, "dp_id": 5,  "writable": True,  "label": "Volume (0-100)"},
                "channel":          {"type": PropertyType.Integer, "dp_id": 3,  "writable": True,  "label": "Channel (0-999)"},
                "channel_change":   {"type": PropertyType.String,  "dp_id": 4,  "writable": True,  "label": "Channel Up/Down"},
                "input":            {"type": PropertyType.String,  "dp_id": 6,  "writable": True,  "label": "Signal Input (hdmi1/hdmi2/...)"},
                "sleep":            {"type": PropertyType.Bool,    "dp_id": 7,  "writable": True,  "label": "Sleep Mode"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  KITCHEN APPLIANCES
        # ══════════════════════════════════════════════════════════════

        "bh": {
            "label": "Kettle",
            "dps": {
                "start":            {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Start/Stop"},
                "status":           {"type": PropertyType.String,  "dp_id": 3,  "writable": False, "label": "Status (heating/warm/idle)"},
                "temp_set":         {"type": PropertyType.Integer, "dp_id": 4,  "writable": True,  "label": "Target Temperature"},
                "temp_current":     {"type": PropertyType.Integer, "dp_id": 5,  "writable": False, "label": "Current Temperature"},
                "keep_warm":        {"type": PropertyType.Bool,    "dp_id": 6,  "writable": True,  "label": "Keep Warm"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  ENERGY
        # ══════════════════════════════════════════════════════════════

        "zndb": {
            "label": "Smart Meter / Energy Monitor",
            "dps": {
                "forward_energy_total":  {"type": PropertyType.Integer, "dp_id": 1,  "writable": False, "label": "Total Forward Energy (kWh)"},
                "reverse_energy_total":  {"type": PropertyType.Integer, "dp_id": 2,  "writable": False, "label": "Total Reverse Energy (kWh)"},
                "phase_a_current":       {"type": PropertyType.Integer, "dp_id": 6,  "writable": False, "label": "Phase A Current (mA)"},
                "phase_a_power":         {"type": PropertyType.Integer, "dp_id": 7,  "writable": False, "label": "Phase A Power (W)"},
                "phase_a_voltage":       {"type": PropertyType.Integer, "dp_id": 8,  "writable": False, "label": "Phase A Voltage (0.1V)"},
            },
        },

        # ══════════════════════════════════════════════════════════════
        #  OUTDOOR / TRAVEL
        # ══════════════════════════════════════════════════════════════

        "sp_sprinkler": {
            "label": "Sprinkler / Irrigation",
            "dps": {
                "switch":           {"type": PropertyType.Bool,    "dp_id": 1,  "writable": True,  "label": "Valve On/Off"},
                "countdown_1":      {"type": PropertyType.Integer, "dp_id": 9,  "writable": True,  "label": "Countdown (s)"},
                "water_total":      {"type": PropertyType.Integer, "dp_id": 7,  "writable": False, "label": "Water Usage"},
                "battery_percentage": {"type": PropertyType.Integer, "dp_id": 4, "writable": False, "label": "Battery %"},
            },
        },
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def get_dps_for_category(self, category: str) -> List[Dict]:
        """Return list of DPS dicts for a given Tuya category.

        Each item: {code, dp_id, type, writable, label}
        """
        mapping = self.CATEGORY_MAPPINGS.get(category)
        if not mapping:
            return []
        result = []
        for code, info in mapping.get('dps', {}).items():
            ptype = info.get('type', PropertyType.String)
            result.append({
                'code': code,
                'dp_id': info.get('dp_id'),
                'type': ptype.value if hasattr(ptype, 'value') else str(ptype),
                'writable': info.get('writable', False),
                'label': info.get('label', code),
            })
        return result

    def get_category_label(self, category: str) -> str:
        mapping = self.CATEGORY_MAPPINGS.get(category)
        return mapping['label'] if mapping else category

    def get_all_categories(self) -> Dict[str, str]:
        """Return {code: label} for all known categories."""
        return {k: v['label'] for k, v in self.CATEGORY_MAPPINGS.items()}
