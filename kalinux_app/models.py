from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
        }


class FirewallRule(db.Model):
    __tablename__ = "firewall_rules"

    id = db.Column(db.Integer, primary_key=True)
    direction = db.Column(db.String(10), nullable=False)  # IN/OUT
    protocol = db.Column(db.String(10), nullable=False)  # TCP/UDP
    source_ip = db.Column(db.String(50), default="any")
    source_port = db.Column(db.String(50), default="any")
    destination_ip = db.Column(db.String(50), default="any")
    destination_port = db.Column(db.String(50), default="any")

    def to_dict(self):
        return {
            "id": self.id,
            "direction": self.direction,
            "protocol": self.protocol,
            "source_ip": self.source_ip,
            "source_port": self.source_port,
            "destination_ip": self.destination_ip,
            "destination_port": self.destination_port,
        }


class LogEntry(db.Model):
    __tablename__ = "log_entries"

    id = db.Column(db.Integer, primary_key=True)
    log_type = db.Column(db.String(50), nullable=False)  # auth/iptables
    timestamp = db.Column(db.DateTime, nullable=False)
    message = db.Column(db.Text, nullable=False)
    ip = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "log_type": self.log_type,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "ip": self.ip,
        }
