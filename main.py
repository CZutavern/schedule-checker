"""Schedule checker.

Opens a College Scheduler page in a visible browser, lets YOU sign in (username, password and Duo)
and pick your courses, then keeps refreshing, clicks "Generate Schedules" and alerts you
(spoken message + optional Twilio phone call) as soon as generated schedules show up.

The script never sees your login: you type it into the browser yourself.
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

import config
import selection


# ==================================================
# SETTINGS (change them in settings.txt, or edit the defaults here)
# ==================================================

REFRESH_PAGE = config.env_bool("REFRESH_PAGE", True)

# Which boxes to tick (by class name, see settings.txt). "off" = leave the boxes as you set them yourself.
_MODES = {"1": "all", "all": "all", "2": "specified", "specified": "specified", "specific": "specified"}
SELECT_MODE = _MODES.get(os.environ.get("SELECT_MODE", "off").strip().lower(), "off")
LOOKING_FOR = selection.split_names(os.environ.get("LOOKING_FOR", ""))
REGISTERED = selection.split_names(os.environ.get("REGISTERED", ""))
BREAKS = selection.split_names(os.environ.get("BREAKS", "leave")) or ["leave"]

CLICK_OK = config.env_bool("CLICK_OK", True)
CLICK_GENERATE = config.env_bool("CLICK_GENERATE", True)

SEARCH_WORD = "Generated"                          # text that appears on the page when schedules exist

WAIT_TIME = config.env_int("WAIT_TIME", 5)         # seconds between checks
CALL_INTERVAL = config.env_int("CALL_INTERVAL", 120)   # seconds between alerts once a schedule is found

VOICE_ALERT = config.env_bool("VOICE_ALERT", True)
MAKE_CALLS = config.env_bool("MAKE_CALLS", True)   # also needs the TWILIO_* values in settings.txt
ALERT_MESSAGE = "Your schedule is available"

_warned_no_twilio = False


# ==================================================
# ALERT FUNCTIONS
# ==================================================

def make_phone_call():
    """Place a Twilio call. Settings come from settings.txt (never from the code)."""
    global _warned_no_twilio

    if not MAKE_CALLS:
        return

    settings = config.twilio_settings()
    if settings is None:
        if not _warned_no_twilio:
            print("Twilio is not configured (fill in the TWILIO_ lines in settings.txt); skipping the phone call.")
            _warned_no_twilio = True
        return

    from twilio.rest import Client      # imported here so the script still runs without Twilio installed

    print("Calling phone...")

    client = Client(settings["account_sid"], settings["auth_token"])
    client.calls.create(
        to=settings["to_number"],
        from_=settings["from_number"],
        url=settings["voice_url"],
    )

    print("Call sent")


def speak(message):
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.say(message)
        engine.runAndWait()
    except Exception as e:              # a missing voice must never stop the phone call
        print("Voice alert failed:", e)


def alert():
    print("\n==============================")
    print("       SCHEDULE FOUND")
    print("==============================\n")

    if VOICE_ALERT:
        speak(ALERT_MESSAGE)

    make_phone_call()


# ==================================================
# BUTTON FUNCTIONS
# ==================================================

def apply_choices(page):
    """Tick / untick the class boxes according to SELECT_MODE, LOOKING_FOR, REGISTERED and BREAKS."""
    try:
        selection.apply_selection(page, SELECT_MODE, LOOKING_FOR, REGISTERED, BREAKS)
    except Exception as e:
        print("Could not apply your class choices:", e)


def click_ok(page):
    if not CLICK_OK:
        return

    button = page.get_by_role("button", name="OK")

    try:
        if button.count():
            button.click(timeout=3000)
            print("Clicked OK")
    except Exception:
        pass


def click_generate(page):
    if not CLICK_GENERATE:
        return

    button = page.get_by_role("button", name="Generate Schedules")

    if button.count():
        button.click()
        print("Clicked Generate Schedules")

        # wait for the generated results to load
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        time.sleep(2)
    else:
        print("Generate button not found")


# ==================================================
# CHECK FOR SCHEDULE
# ==================================================

def check_schedule(page):
    text = page.locator("body").inner_text()
    return SEARCH_WORD.lower() in text.lower()


# ==================================================
# MAIN PROGRAM
# ==================================================

def get_url():
    import os

    url = os.environ.get("SCHEDULER_URL", "").strip()
    if not url:
        print("Paste the College Scheduler page to watch (the 'options' page for your term).")
        print("Tip: put it in settings.txt as SCHEDULER_URL so you are not asked next time.")
        url = input("URL: ").strip()
    return url


def main():
    if config.CREATED_SETTINGS:
        print(config.SETUP_MESSAGE)
        return

    url = get_url()
    if not url:
        print("No URL given; nothing to do.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("\nOpening the scheduler...")
        page.goto(url)

        print()
        print("A browser window is open. In that window, YOU do the following:")
        print("  1. Sign in (type your username and password there).")
        print("  2. Approve the Duo / two-factor prompt.")
        print("  3. Open the schedule builder page (your Courses, Breaks and Current Schedule are listed there).")
        if SELECT_MODE == "off":
            print("     SELECT_MODE is off, so tick the boxes you want yourself.")
        else:
            print(f"     The program ticks the boxes for you (SELECT_MODE={SELECT_MODE}, see settings.txt).")
        print()
        print("This script never sees or stores your login.")
        print()

        input("Press ENTER here once you are signed in and ready to start monitoring...")

        if "--list" in sys.argv:
            print("\nEverything on the page you can choose by name:")
            selection.list_page(page)
            print("\nCopy the names exactly as shown into settings.txt (LOOKING_FOR / REGISTERED / BREAKS).")
            return

        apply_choices(page)

        print("\nMonitoring started (Ctrl+C to stop)")

        while True:
            try:
                print("\nChecking...")

                if REFRESH_PAGE:
                    page.reload()

                    try:
                        page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass

                    print("Page refreshed")

                click_ok(page)
                apply_choices(page)
                click_generate(page)

                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass

                if check_schedule(page):
                    print("Schedule detected!")

                    while True:
                        alert()
                        print(f"Waiting {CALL_INTERVAL} seconds before the next alert...")
                        time.sleep(CALL_INTERVAL)
                else:
                    print("No schedule found")

                time.sleep(WAIT_TIME)

            except KeyboardInterrupt:
                print("\nProgram stopped")
                break

            except Exception as e:
                print("Error:", e)
                time.sleep(5)


if __name__ == "__main__":
    main()
