from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Message:
    event_type: str
    payload: dict
    sender: str
    timestamp: datetime = field(default_factory=datetime.now)

