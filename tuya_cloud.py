"""
Tuya Cloud API client wrapper
Uses tuya-connector-python for OAuth2, REST API, and Pulsar push notifications
"""

import logging
from typing import Dict, List, Optional, Callable
from tuya_connector import TuyaOpenAPI, TuyaOpenPulsar

try:
    from tuya_connector import TuyaCloudPulsarTopic
except ImportError:
    TuyaCloudPulsarTopic = None


class TuyaCloudClient:
    """Wrapper for Tuya Cloud API with MQTT support"""
    
    ENDPOINTS = {
        "cn": "https://openapi.tuyacn.com",
        "us": "https://openapi.tuyaus.com",
        "eu": "https://openapi.tuyaeu.com",
        "in": "https://openapi.tuyain.com",
    }
    
    def __init__(self, access_id: str, access_secret: str, region: str = "eu",
                 linked_uid: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize Tuya Cloud client

        Args:
            access_id: Tuya IoT Platform Access ID
            access_secret: Tuya IoT Platform Access Secret
            region: Region code (cn/us/eu/in)
            linked_uid: Optional UID of linked Tuya/Smart Life app user (use when token UID has no devices)
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.access_id = access_id
        self.access_secret = access_secret
        self.region = region
        self.linked_uid = (linked_uid or "").strip() or None
        self.endpoint = self.ENDPOINTS.get(region, self.ENDPOINTS["eu"])

        self.api: Optional[TuyaOpenAPI] = None
        self.pulsar: Optional[TuyaOpenPulsar] = None
        self._connected = False
        
    def connect(self) -> bool:
        """
        Connect to Tuya Cloud API
        
        Returns:
            True if connected successfully
        """
        try:
            self.api = TuyaOpenAPI(self.endpoint, self.access_id, self.access_secret)
            self.api.connect()
            self._connected = True
            self.logger.info(f"Connected to Tuya Cloud API ({self.region})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Tuya Cloud: {e}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to cloud"""
        return self._connected and self.api is not None
    
    def get_devices(self) -> List[Dict]:
        """
        Get all devices from Tuya account.
        Tries multiple APIs: users/devices, users/homes->homes/devices, iot-03/assets->assets/devices.
        Requires: Link Tuya App Account (iot.tuya.com → project → Devices → Link Tuya App Account).
        """
        if not self.is_connected():
            self.logger.error("Not connected to Tuya Cloud")
            return []

        def _extract_list(res: dict) -> list:
            r = res.get("result")
            if r is None:
                return []
            if isinstance(r, list):
                return r
            if isinstance(r, dict):
                return r.get("list") or r.get("devices") or []
            return []

        def _normalize(d: dict) -> dict:
            """Ensure device has 'id' for compatibility."""
            if "id" not in d and "device_id" in d:
                d = dict(d)
                d["id"] = d["device_id"]
            return d

        uid = self.linked_uid or getattr(self.api.token_info, "uid", None)
        if not uid:
            self.logger.error("No UID available (set Linked App User UID in settings or check token)")
            return []
        if self.linked_uid:
            self.logger.debug("Using linked_uid=%s for device discovery", uid)

        try:
            # 1) users/{uid}/devices (Smart Home, with pagination)
            for params in [{"page_no": 0, "page_size": 100}, {}]:
                resp = self.api.get("/v1.0/users/{}/devices".format(uid), params)
                if resp.get("success"):
                    devices = _extract_list(resp)
                    if devices:
                        self.logger.info("Retrieved %d devices from users/devices", len(devices))
                        return [_normalize(d) for d in devices]

            # 2) users/{uid}/homes -> homes/{home_id}/devices
            resp = self.api.get("/v1.0/users/{}/homes".format(uid))
            if resp.get("success"):
                homes = _extract_list(resp)
                all_devices = []
                seen_ids = set()
                for h in homes:
                    home_id = h.get("home_id") or h.get("id")
                    if not home_id:
                        continue
                    dr = self.api.get("/v1.0/homes/{}/devices".format(home_id))
                    if dr.get("success"):
                        for d in _extract_list(dr):
                            did = d.get("id") or d.get("device_id")
                            if did and did not in seen_ids:
                                seen_ids.add(did)
                                all_devices.append(_normalize(d))
                if all_devices:
                    self.logger.info("Retrieved %d devices from homes", len(all_devices))
                    return all_devices

            # 3) iot-03/users/{uid}/assets -> iot-02/assets/{asset_id}/devices
            ar = self.api.get("/v1.0/iot-03/users/{}/assets".format(uid), {"page_no": 1, "page_size": 50})
            if ar.get("success"):
                assets = _extract_list(ar)
                all_devices = []
                seen_ids = set()
                for a in assets:
                    aid = a.get("asset_id")
                    if not aid:
                        continue
                    dr = self.api.get("/v1.0/iot-02/assets/{}/devices".format(aid), {"page_size": 100})
                    if dr.get("success"):
                        for d in _extract_list(dr):
                            did = d.get("device_id") or d.get("id")
                            if did and did not in seen_ids:
                                seen_ids.add(did)
                                all_devices.append(_normalize(d))
                if all_devices:
                    self.logger.info("Retrieved %d devices from assets", len(all_devices))
                    return all_devices

            # 4) iot-03/devices (often empty without device_ids)
            r2 = self.api.get("/v1.0/iot-03/devices")
            if r2.get("success"):
                devices = _extract_list(r2)
                if devices:
                    self.logger.info("Retrieved %d devices from iot-03/devices", len(devices))
                    return [_normalize(d) for d in devices]

            self.logger.warning("All device list APIs returned empty (uid=%s)", uid)
            return []
        except Exception as e:
            self.logger.error("Error getting devices: %s", e)
            return []
    
    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """
        Get detailed device information
        
        Args:
            device_id: Device ID
            
        Returns:
            Device info dict or None
        """
        if not self.is_connected():
            return None
        
        try:
            response = self.api.get(f"/v1.0/iot-03/devices/{device_id}")
            if response.get("success"):
                return response.get("result")
            else:
                self.logger.error(f"Failed to get device info for {device_id}: {response}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting device info: {e}")
            return None
    
    def get_device_status(self, device_id: str) -> Dict:
        """
        Get current device status (all data points)
        
        Args:
            device_id: Device ID
            
        Returns:
            Dictionary of status data points {code: value}
        """
        if not self.is_connected():
            return {}
        
        try:
            response = self.api.get(f"/v1.0/iot-03/devices/{device_id}/status")
            if response.get("success"):
                status_list = response.get("result", [])
                out = {item["code"]: item["value"] for item in status_list}
                self.logger.debug("Cloud get_status %s: %s", device_id, out)
                return out
            else:
                self.logger.debug("Cloud get_status %s failed: %s", device_id, response)
                return {}
        except Exception as e:
            self.logger.error(f"Error getting device status: {e}")
            return {}
    
    def get_device_specification(self, device_id: str) -> Optional[Dict]:
        """
        Get device specification — real functions and status DPS this device supports.

        Returns:
            Dict with 'functions' and 'status' lists, or None.
            Each item: {code, dp_id, type, values}
        """
        if not self.is_connected():
            return None

        try:
            response = self.api.get(f"/v1.0/iot-03/devices/{device_id}/specification")
            if response.get("success"):
                return response.get("result")
            else:
                self.logger.debug(f"Specification not available for {device_id}: {response}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting device specification: {e}")
            return None

    def send_commands(self, device_id: str, commands: List[Dict]) -> bool:
        """
        Send commands to device
        
        Args:
            device_id: Device ID
            commands: List of command dicts, e.g. [{"code": "switch_1", "value": True}]
            
        Returns:
            True if command sent successfully
        """
        if not self.is_connected():
            self.logger.error("Not connected to Tuya Cloud")
            return False
        
        try:
            response = self.api.post(f"/v1.0/iot-03/devices/{device_id}/commands", {"commands": commands})
            if response.get("success"):
                self.logger.debug("Cloud send_commands %s %s -> success", device_id, commands)
                return True
            else:
                self.logger.debug("Cloud send_commands %s %s failed: %s", device_id, commands, response)
                return False
        except Exception as e:
            self.logger.error(f"Error sending commands: {e}")
            return False
    
    def get_device_functions(self, device_id: str) -> List[Dict]:
        """
        Get available functions/commands for device
        
        Args:
            device_id: Device ID
            
        Returns:
            List of function specifications
        """
        if not self.is_connected():
            return []
        
        try:
            response = self.api.get(f"/v1.0/iot-03/devices/{device_id}/functions")
            if response.get("success"):
                return response.get("result", {}).get("functions", [])
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error getting device functions: {e}")
            return []
    
    def get_device_specifications(self, device_id: str) -> Dict:
        """
        Get device specifications (status and function definitions)
        
        Args:
            device_id: Device ID
            
        Returns:
            Dict with 'status' and 'functions' keys
        """
        if not self.is_connected():
            return {}
        
        try:
            response = self.api.get(f"/v1.0/iot-03/devices/{device_id}/specification")
            if response.get("success"):
                return response.get("result", {})
            else:
                return {}
        except Exception as e:
            self.logger.error(f"Error getting device specifications: {e}")
            return {}
    
    def start_mqtt(self, message_callback: Callable[[str, Dict], None]) -> bool:
        """
        Start Pulsar connection for real-time device updates
        
        Args:
            message_callback: Callback function(device_id, status_dict)
            
        Returns:
            True if Pulsar started successfully
        """
        if not self.is_connected():
            self.logger.error("Cannot start Pulsar: not connected to API")
            return False
        
        try:
            mq_endpoint = {
                "cn": "pulsar+ssl://mqe.tuyacn.com:7285/",
                "us": "pulsar+ssl://mqe.tuyaus.com:7285/",
                "eu": "pulsar+ssl://mqe.tuyaeu.com:7285/",
                "in": "pulsar+ssl://mqe.tuyain.com:7285/",
            }.get(self.region, "pulsar+ssl://mqe.tuyaeu.com:7285/")
            topic = TuyaCloudPulsarTopic.PROD if TuyaCloudPulsarTopic else "openapi"
            self.pulsar = TuyaOpenPulsar(
                self.access_id,
                self.access_secret,
                mq_endpoint,
                topic,
            )
            
            def on_message(msg):
                """Handle incoming Pulsar message"""
                try:
                    # tuya-connector-python Pulsar message format
                    if isinstance(msg, dict):
                        # Status update message
                        device_id = msg.get("devId") or msg.get("deviceId")
                        
                        # Extract status from different possible locations
                        status = msg.get("status", [])
                        if not status and "data" in msg:
                            status = msg.get("data", {}).get("status", [])
                        
                        if device_id and status:
                            if isinstance(status, list):
                                status_dict = {item["code"]: item["value"] for item in status}
                            else:
                                status_dict = status
                            message_callback(device_id, status_dict)
                                
                except Exception as e:
                    self.logger.error(f"Error processing Pulsar message: {e}")
            
            self.pulsar.add_message_listener(on_message)
            self.pulsar.start()
            self.logger.info("Pulsar connection started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Pulsar: {e}")
            return False
    
    def stop_mqtt(self):
        """Stop Pulsar connection"""
        if self.pulsar:
            try:
                self.pulsar.stop()
                self.logger.info("Pulsar connection stopped")
            except Exception as e:
                self.logger.error(f"Error stopping Pulsar: {e}")
    
    def disconnect(self):
        """Disconnect from Tuya Cloud"""
        self.stop_mqtt()
        self._connected = False
        self.logger.info("Disconnected from Tuya Cloud")
