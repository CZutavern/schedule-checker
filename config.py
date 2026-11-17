"""Settings for the schedule checker.

EVERYTHING you need to fill in lives in ONE file: settings.txt (next to this script).
On the first run the program creates it for you from settings.example.txt.
Nothing private (passwords, Twilio keys, phone numbers) is ever stored in the code.
"""
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SETTINGS_FILE = HERE / "settings.txt"
EXAMPLE_FILE = HERE / "settings.example.txt"

CREATED_SETTINGS = False     # True when settings.txt did not exist and was just created from the example


def ensure_settings_file():
    """Create settings.txt from the example the first time, so people just open it and fill it in."""
    global CREATED_SETTINGS
    if not SETTINGS_FILE.exists() and EXAMPLE_FILE.exists():
        shutil.copyfile(EXAMPLE_FILE, SETTINGS_FILE)
        CREATED_SETTINGS = True
    return CREATED_SETTINGS


def load_settings(path=None):
    """Read KEY=VALUE lines from settings.txt into os.environ.

    Lines starting with # are comments. Variables already set in the environment win over the file.
    """
    path = Path(path) if path else SETTINGS_FILE
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("[") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


def file_values(path=None):
    """The KEY=VALUE lines of settings.txt, read fresh from disk (so edits made while the program runs are seen)."""
    path = Path(path) if path else SETTINGS_FILE
    values = {}
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("[") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key.strip()] = value
    return values


def get(name, default=""):
    """Setting from settings.txt (fresh), else from the environment, else the default."""
    value = file_values().get(name, "")
    if value == "":
        value = os.environ.get(name, "")
    return value if value != "" else default


def env_bool(name, default):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    try:
        return int(os.environ.get(name, "").strip() or default)
    except ValueError:
        return default


def twilio_settings():
    """Return the Twilio settings as a dict, or None if any required value is missing."""
    keys = {
        "account_sid": "TWILIO_ACCOUNT_SID",
        "auth_token": "TWILIO_AUTH_TOKEN",
        "from_number": "TWILIO_FROM_NUMBER",
        "to_number": "TWILIO_TO_NUMBER",
    }
    values = {name: get(var).strip() for name, var in keys.items()}      # read fresh, so edits to settings.txt count
    if not all(values.values()):
        return None
    values["voice_url"] = get(
        "TWILIO_VOICE_URL",
        "https://webhooks.twilio.com/v1/Voice/Template/voice_speech_recognition",
    ).strip()
    return values


SETUP_MESSAGE = (
    "\nI created 'settings.txt' next to this program.\n"
    "Open it, fill in your details (scheduler link and, for the phone call, your Twilio keys and phone numbers),\n"
    "save it, then run the program again.\n"
)

ensure_settings_file()
load_settings()
