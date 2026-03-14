from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import SurrogatePK, db


class TuyaDevice(SurrogatePK, db.Model):
    __tablename__ = "tuya_devices"

    device_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(50), default="unknown")
    ip = Column(String(45))
    local_key = Column(String(255))
    protocol_version = Column(String(10), default="3.3")
    online = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    discovered_at = Column(DateTime)
    last_seen = Column(DateTime)

    properties = relationship(
        "TuyaDeviceProperty", back_populates="device", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.device_id,
            "name": self.name,
            "category": self.category,
            "ip": self.ip,
            "local_key": self.local_key,
            "protocol_version": self.protocol_version,
            "online": self.online,
            "enabled": self.enabled,
            "discovered_at": str(self.discovered_at) if self.discovered_at else None,
            "last_seen": str(self.last_seen) if self.last_seen else None,
            "db_id": self.id,
        }


class TuyaDeviceProperty(SurrogatePK, db.Model):
    __tablename__ = "tuya_device_properties"

    device_id = Column(Integer, ForeignKey("tuya_devices.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(255))
    dp_id = Column(Integer)
    writable = Column(Boolean, default=False)
    linked_object = Column(String(255))
    linked_property = Column(String(255))
    linked_method = Column(String(255))
    bidirectional = Column(Boolean, default=False)

    device = relationship("TuyaDevice", back_populates="properties")

    def to_dict(self):
        return {
            "name": self.name,
            "code": self.code,
            "dp_id": self.dp_id,
            "writable": self.writable,
            "linked_object": self.linked_object,
            "linked_property": self.linked_property,
            "linked_method": self.linked_method,
            "bidirectional": self.bidirectional,
        }
