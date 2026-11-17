# Schedule Checker

Watches a [College Scheduler](https://collegescheduler.com) page and **alerts you the moment your schedules are generated**: it speaks a message on your computer and can also **call your phone with Twilio**.

It was written to catch the registration-time schedule generation at a university using College Scheduler, where the "Generate Schedules" result only appears once the term opens. The script:

1. opens the scheduler in a visible Chrome window,
2. waits while **you** sign in (username, password and Duo) and pick your courses,
3. refreshes the page every few seconds, clicks **OK** and **Generate Schedules**,
4. looks for the word `Generated` on the page, and when it appears keeps alerting you (voice + phone call) until you stop it.

**Your login is never in the code and the script never sees it.** You type your username and password into the browser window yourself and approve Duo there. Everything private (scheduler link, Twilio key, phone numbers) goes in **one file, `settings.txt`**, which stays on your computer and is git-ignored.

> Use it responsibly. Keep the check interval polite (the default is 5 seconds), check that automated page refreshes are allowed by your school's rules, and never share your `settings.txt`.

---

## Requirements

- Python 3.10 or newer
- A Chromium-compatible machine (the script uses Playwright's own Chromium)
- Windows for the spoken alert (`pyttsx3` uses the built-in Windows voices; on other systems the voice step may need extra packages, and a failed voice never stops the phone call)
- Optional: a [Twilio](https://www.twilio.com) account for the phone call

## Setup

### 1. Get the code and install the packages

```bash
git clone https://github.com/CZutavern/schedule-checker.git
cd schedule-checker

python -m venv venv
# Windows:        venv\Scripts\activate
# macOS / Linux:  source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### 2. Fill in your one settings file

Run the program once:

```bash
python main.py
```

The first time, it creates **`settings.txt`** next to the program (from `settings.example.txt`) and stops. (Or copy `settings.example.txt` to `settings.txt` yourself.) Open `settings.txt` in any text editor, fill in the values after each `=`, and save. **This is the only file you need to edit.**

| Setting | What to put there |
|---|---|
| `SCHEDULER_URL` | The College Scheduler **options** page for your term, for example `https://YOUR-SCHOOL.collegescheduler.com/terms/YOUR%20TERM/options`. Leave it empty and the program asks for it each run. |
| `TWILIO_ACCOUNT_SID` | Twilio Console home page, Account Info. Starts with `AC`. |
| `TWILIO_AUTH_TOKEN` | Twilio Console home page, Account Info (click to reveal). Treat it like a password. |
| `TWILIO_FROM_NUMBER` | A Twilio phone number you own, as `+1XXXXXXXXXX`. The call comes **from** this number. |
| `TWILIO_TO_NUMBER` | Your own phone, as `+1XXXXXXXXXX`. The call goes **to** this number. |

Leave the four `TWILIO_*` lines empty if you only want the spoken alert on your computer; the program then says so once and skips the phone call.

### 3. Set up Twilio (only for the phone call)

1. Create an account at <https://www.twilio.com> and open the Console.
2. Copy the **Account SID** and **Auth Token** into `settings.txt`.
3. Get a phone number (Phone Numbers, Buy a number) with Voice capability. Put it in `TWILIO_FROM_NUMBER` in `settings.txt`.
4. On a **trial** account Twilio only calls numbers you have verified: add your phone under Phone Numbers, Verified Caller IDs, then put it in `TWILIO_TO_NUMBER` in `settings.txt`.
5. Test it with a single call:

   ```bash
   python test_twilio.py
   ```

   It shows your Twilio account name and asks before calling.

### 4. Run it

```bash
python main.py
```

1. A Chrome window opens on your scheduler page.
2. **In that window, sign in with your username and password and approve the Duo prompt.** Then choose your courses and options so the schedule page is showing.
3. Come back to the terminal and press **ENTER**. Monitoring starts.
4. Leave it running. When generated schedules appear it prints `SCHEDULE FOUND`, speaks the message and places the call, then repeats every two minutes until you press `Ctrl+C`.

If the session expires while you wait (the page sends you back to the login screen), stop the script, run it again and sign in again.

## Settings

Add these lines to `settings.txt` if you want to change them (all optional; defaults shown; the example file has them commented out):

| Setting | Default | Meaning |
|---|---|---|
| `WAIT_TIME` | `5` | Seconds between checks |
| `CALL_INTERVAL` | `120` | Seconds between repeated alerts once a schedule is found |
| `VOICE_ALERT` | `true` | Speak the alert on this computer |
| `MAKE_CALLS` | `true` | Place the Twilio call (needs the `TWILIO_*` values) |
| `REFRESH_PAGE` | `true` | Reload the page on every check |
| `CLICK_OK` | `true` | Click an `OK` button if one shows up |
| `CLICK_GENERATE` | `true` | Click `Generate Schedules` on every check |
| `CLICK_SELECT_ALL` | `false` | Untick the "Select All Registered Sections" box if it is ticked |
| `TWILIO_VOICE_URL` | Twilio's public voice template | The TwiML URL Twilio plays when the call is answered |

The word the script looks for (`Generated`) and the spoken message are constants at the top of `main.py`.

## Files

| File | What it is |
|---|---|
| `main.py` | The monitor |
| `config.py` | Reads `settings.txt` and the Twilio settings |
| `test_twilio.py` | Places one test call |
| `settings.example.txt` | Template for your settings; the program copies it to `settings.txt` on first run |
| `settings.txt` | **Your** settings (created on first run, git-ignored, never shared) |
| `requirements.txt` | Python packages |

## Troubleshooting

- **`Twilio is not configured`**: one of the four `TWILIO_*` values in `settings.txt` is empty. Fill them in or set `MAKE_CALLS=false`.
- **The call never arrives on a trial account**: the destination number must be a verified caller ID in your Twilio Console.
- **`Generate button not found`**: the page is not on the schedule options screen. Select your courses, or sign in again.
- **No spoken alert**: install the packages again (`pip install -r requirements.txt`) and check that Windows has a text-to-speech voice installed.
- **Browser not found**: run `playwright install chromium`.

## Keeping your keys safe

- `settings.txt` is listed in `.gitignore`; check `git status` before every commit and never paste its contents anywhere public.
- If a Twilio token ever ends up in a commit, a screenshot or a chat, **rotate it** in the Twilio Console right away.

## License

MIT. See [LICENSE](LICENSE).
