"""
Tuya Local LAN control client
Uses tinytuya for direct device communication without cloud
"""

import logging
import tinytuya
from typing import Dict, Optional, List, Any


class TuyaLocalClient:
    """Wrapper for tinytuya local LAN control"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize Tuya Local client
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.devices: Dict[str, tinytuya.Device] = {}
        self._device_configs: Dict[str, Dict] = {}
        
    def add_device(self, device_id: str, ip: str, local_key: str, version: str = "3.3") -> bool:
        """
        Add a device for local control
        
        Args:
            device_id: Device ID
            ip: Device IP address
            local_key: Device local key
            version: Protocol version (3.1, 3.3, 3.4 or 3.5)
            
        Returns:
            True if device added successfully
        """
        try:
            device = tinytuya.Device(device_id, ip, local_key, version=version)
            device.set_socketPersistent(True)
            device.set_socketTimeout(5)
            
            self.devices[device_id] = device
            self._device_configs[device_id] = {
                "ip": ip,
                "local_key": local_key,
                "version": version
            }
            
            self.logger.info("Added local device %s at %s (protocol=%s)", device_id, ip, version)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add device {device_id}: {e}")
            return False
    
    def remove_device(self, device_id: str):
        """Remove device from local control"""
        if device_id in self.devices:
            try:
                self.devices[device_id].close()
            except:
                pass
            del self.devices[device_id]
            
        if device_id in self._device_configs:
            del self._device_configs[device_id]
    
    def get_device(self, device_id: str) -> Optional[tinytuya.Device]:
        """Get device instance"""
        return self.devices.get(device_id)
    
    def update_device_ip(self, device_id: str, new_ip: str) -> bool:
        """
        Update device IP address
        
        Args:
            device_id: Device ID
            new_ip: New IP address
            
        Returns:
            True if updated successfully
        """
        if device_id not in self._device_configs:
            return False
        
        config = self._device_configs[device_id]
        self.remove_device(device_id)
        return self.add_device(device_id, new_ip, config["local_key"], config["version"])
    
    def get_status(self, device_id: str) -> Dict[str, Any]:
        """
        Get device status (DPS values)
        
        Args:
            device_id: Device ID
            
        Returns:
            Dictionary of DPS values {dp_id: value}
        """
        device = self.devices.get(device_id)
        if not device:
            self.logger.error(f"Device {device_id} not found in local client")
            return {}
        
        try:
            status = device.status()
            
            if not status or 'dps' not in status:
                self.logger.warning("get_status %s: no DPS, raw response: %s", device_id, status)
                return {}
            
            dps = status['dps']
            self.logger.debug("get_status %s: dps=%s (full: %s)", device_id, dps, status)
            return dps
            
        except Exception as e:
            self.logger.error(f"Error getting status for {device_id}: {e}")
            return {}
    
    def _normalize_dp_value(self, value: Any, dp_id: int = None) -> Any:
        """
        Normalize value for Tuya protocol.
        Switch DPS often expect bool (True/False), not int 0/1 — especially for protocol 3.4+.
        """
        if value in (0, "0", False):
            return False
        if value in (1, "1", True):
            return True
        return value

    def set_dp(self, device_id: str, dp_id: int, value: Any) -> bool:
        """
        Set a single data point value
        
        Args:
            device_id: Device ID
            dp_id: Data point ID (integer)
            value: Value to set
            
        Returns:
            True if command sent successfully
        """
        device = self.devices.get(device_id)
        if not device:
            self.logger.error(f"Device {device_id} not found in local client")
            return False
        
        # Normalize switch/boolean values — Tuya 3.4+ often expects bool
        normalized = self._normalize_dp_value(value, dp_id)
        if isinstance(normalized, bool):
            self.logger.debug("set_dp %s dp=%s: normalized value %s -> bool %s",
                              device_id, dp_id, value, normalized)
        
        try:
            result = device.set_value(dp_id, normalized)
            ok = not (isinstance(result, dict) and (result.get("Error") or result.get("Err")))
            err_code = result.get("Error") or result.get("Err") if isinstance(result, dict) else None
            self.logger.debug("set_dp %s dp=%s value=%s -> ok=%s, result=%s",
                              device_id, dp_id, value, ok, result)
            if not ok and err_code is not None:
                self.logger.debug("  device error response: Error=%s Err=%s (full=%s)",
                                  result.get("Error"), result.get("Err"), result)
            if isinstance(result, dict) and (result.get("Error") or result.get("Err")):
                return False
            return True
        except Exception as e:
            self.logger.error("set_dp %s dp=%s failed: %s", device_id, dp_id, e)
            return False
    
    def set_multiple_dps(self, device_id: str, dps: Dict[int, Any]) -> bool:
        """
        Set multiple data points at once
        
        Args:
            device_id: Device ID
            dps: Dictionary of {dp_id: value}
            
        Returns:
            True if command sent successfully
        """
        device = self.devices.get(device_id)
        if not device:
            self.logger.error(f"Device {device_id} not found in local client")
            return False
        
        try:
            result = device.set_multiple_values(dps)
            ok = not (isinstance(result, dict) and (result.get("Error") or result.get("Err")))
            self.logger.debug("set_multiple_dps %s dps=%s -> ok=%s, result=%s",
                              device_id, dps, ok, result)
            if not ok and isinstance(result, dict):
                self.logger.debug("  device error: Error=%s Err=%s", result.get("Error"), result.get("Err"))
            if isinstance(result, dict) and (result.get("Error") or result.get("Err")):
                return False
            return True
        except Exception as e:
            self.logger.error("set_multiple_dps %s failed: %s", device_id, e)
            return False
    
    def scan_local(self, timeout: int = 18) -> List[Dict]:
        """
        Scan local network for Tuya devices
        
        Args:
            timeout: Scan timeout in seconds
            
        Returns:
            List of discovered devices with IP and ID
        """
        try:
            self.logger.info("Scanning local network for Tuya devices (timeout=%ds)...", timeout)
            devices = tinytuya.deviceScan(verbose=False, maxretry=timeout)
            
            result = []
            for _key, device_info in devices.items():
                # tinytuya may use IP as dict key; use id/gwId from response for device_id
                dev_id = device_info.get("id") or device_info.get("gwId") or device_info.get("ip") or _key
                item = {
                    "id": dev_id,
                    "ip": device_info.get("ip"),
                    "version": device_info.get("version", "3.3"),
                    "name": device_info.get("name") or "Unknown"
                }
                result.append(item)
                self.logger.debug("Scan found: id=%s ip=%s version=%s name=%s",
                                  dev_id, item["ip"], item["version"], item["name"])
                self.logger.debug("  device raw response: %s", device_info)
            
            self.logger.info("Scan complete: found %d devices", len(result))
            for d in result:
                self.logger.debug("  - %s ip=%s version=%s name=%s", d["id"], d["ip"], d["version"], d["name"])
            return result
            
        except Exception as e:
            self.logger.error(f"Error scanning local network: {e}")
            return []
    
    def detect_device(self, device_id: str) -> Optional[Dict]:
        """
        Detect a specific device on the network by ID
        
        Args:
            device_id: Device ID to find
            
        Returns:
            Device info dict if found
        """
        devices = self.scan_local()
        for device in devices:
            if device["id"] == device_id:
                return device
        return None
    
    def test_connection(self, device_id: str) -> bool:
        """
        Test connection to a device
        
        Args:
            device_id: Device ID
            
        Returns:
            True if device responds
        """
        device = self.devices.get(device_id)
        if not device:
            return False
        
        try:
            status = device.status()
            return status is not None and 'dps' in status
        except:
            return False
    
    def close_all(self):
        """Close all device connections"""
        for device_id, device in list(self.devices.items()):
            try:
                device.close()
            except:
                pass
        
        self.devices.clear()
        self._device_configs.clear()
        self.logger.info("Closed all local device connections")
