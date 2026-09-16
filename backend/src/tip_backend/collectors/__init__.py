from .feodotracker import FeodoTrackerCollector
from .malwarebazaar import MalwareBazaarCollector
from .threatfox import ThreatFoxCollector
from .urlhaus import UrlhausCollector

ALL_COLLECTORS = [
    UrlhausCollector(),
    ThreatFoxCollector(),
    MalwareBazaarCollector(),
    FeodoTrackerCollector(),
]

__all__ = [
    "ALL_COLLECTORS",
    "UrlhausCollector",
    "ThreatFoxCollector",
    "MalwareBazaarCollector",
    "FeodoTrackerCollector",
]
