"""Send ONE test call with your Twilio settings (from settings.txt) to check they work.

Usage:  python test_twilio.py
"""
import sys

import config

if config.CREATED_SETTINGS:
    sys.exit(config.SETUP_MESSAGE)

settings = config.twilio_settings()
if settings is None:
    sys.exit("Twilio is not configured. Open settings.txt and fill in the four TWILIO_ lines.")

from twilio.rest import Client

client = Client(settings["account_sid"], settings["auth_token"])

print("Twilio account:", client.api.accounts(settings["account_sid"]).fetch().friendly_name)

answer = input("Place a test call to the TWILIO_TO_NUMBER now? [y/N] ").strip().lower()
if answer != "y":
    sys.exit("Cancelled; no call was made.")

call = client.calls.create(
    to=settings["to_number"],
    from_=settings["from_number"],
    url=settings["voice_url"],
)

print("Call started, SID:", call.sid)
