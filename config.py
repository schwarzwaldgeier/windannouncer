import os
import platform
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

__version__ = "1.1.0"  
__release_date__ = "2026-02-24"

def get_env(key: str, default=None, required=False):
    val = os.getenv(key, default)
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return val

# API Credentials
API_KEY = get_env("API_KEY", required=True)
API_SECRET = get_env("API_SECRET", required=True)
STATION_ID = get_env("STATION_ID", required=True)

# App Settings
BROADCAST_INTERVAL = int(get_env("BROADCAST_INTERVAL", 10))
PLAYER_TYPE = get_env("SOUND_PLAYER", "soundblock").lower()

# --- Path Mapping ---
BASE_DIR = Path(__file__).parent
SOUND_DIR = BASE_DIR / "sound" / "natural"

# Platform-specific paths
SYSTEM = platform.system()
PATHS = {
    "Windows": {
        "temp": Path("C:/temp"),        
    },
    "Linux": {
        "temp": Path("/tmp"),        
    },
    "Darwin": { # macOS
        "temp": Path("/tmp"),        
    }
}

_sys_paths = PATHS.get(SYSTEM, PATHS["Linux"])

TEMP_DIR = _sys_paths["temp"]

TEMP_DIR.mkdir(parents=True, exist_ok=True)