# Schedule Checker

Watches a [College Scheduler](https://collegescheduler.com) page and **alerts you the moment your schedules are generated**: it speaks a message on your computer and can also **call your phone with Twilio**.

It was written to catch the registration-time schedule generation at a university using College Scheduler, where the "Generate Schedules" result only appears once the term opens. The script:

1. opens the scheduler in a visible Chrome window,
2. waits while **you** sign in (username, password and Duo),
3. refreshes the page every few seconds, ticks the classes you named (see **Choosing your classes** below), clicks **OK** and **Generate Schedules**,
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

The first time, it creates **`settings.txt`** next to the program (from `settings.example.txt`) and stops. (Your classes are added to the same file later, when you sign in.) (Or copy `settings.example.txt` to `settings.txt` yourself.) Open `settings.txt` in any text editor, fill in the values after each `=`, and save. **This is the only file you need to edit.**

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
2. **In that window, sign in with your username and password and approve the Duo prompt.** Then open the schedule builder page (the one that lists your Courses, Breaks and Current Schedule).
3. Come back to the terminal and press **ENTER**. The first time, the program copies your classes into `settings.txt` and waits while you mark the ones you want (see [Choosing your classes](#choosing-your-classes-the-checklist-in-settingstxt)); after that, monitoring starts.
4. Leave it running. When generated schedules appear it prints `SCHEDULE FOUND`, speaks the message and places the call, then repeats every two minutes until you press `Ctrl+C`.

If the session expires while you wait (the page sends you back to the login screen), stop the script, run it again and sign in again.

## Choosing your classes (the checklist in `settings.txt`)

You never have to type a class name or find anything on the page. The schedule builder has three lists of checkboxes, and the program copies all of them into `settings.txt` for you:

| List on the page | Called | What it is |
|---|---|---|
| **Courses** | `[looking for]` | Classes you want to get into |
| **Current Schedule** | `[registered]` | Classes you are already enrolled in |
| **Breaks** | `[breaks]` | Your blocked-out times |

### How it works the first time

1. Run `python main.py`, sign in in the browser window, open the schedule builder page and press **ENTER**.
2. The program reads your page and **writes every class and break it finds into the bottom of `settings.txt`** as a checklist, with the exact names the page uses (so nothing can be misspelled):

   ```
   [looking for]
   [ ] ECEN 325 - Electronics
   [ ] ECEN 340 - Electric Energy Conversion
   [ ] PHYS 221 - Optics and Thermal Physics

   [registered]
   [ ] ECEN 350 - Computer Architecture and Design (CRN 12345)
   [ ] ECEN 370 - Electronic Properties of Materials (CRN 67890)

   [breaks]
   [ ] afternoon
   ```

3. It pauses and tells you to open `settings.txt`. **Put an x in the brackets of the ones you want** (`[x] ECEN 340 - ...`), set `SELECT_MODE` (below) and **save the file**.
4. Back in the terminal press **ENTER**. It reads your choices and starts monitoring.

Every later run refreshes the list from the page and **keeps your x marks**: new classes show up unmarked, classes that left the page disappear. You can edit the file at any time; the program re-reads your choices on every check.

(Registered classes also show their 5-digit CRN, which is how two sections of the same class are told apart.)

### The two modes

Set `SELECT_MODE` in `settings.txt`:

| `SELECT_MODE` | What it does | Use it when |
|---|---|---|
| `off` (default) | Ticks nothing. You set the boxes yourself before pressing ENTER. | You prefer to click yourself |
| `all` (or `1`) | Ticks the classes you marked under `[looking for]` and **all** your registered classes. | You are adding classes on top of your current schedule |
| `specified` (or `2`) | Ticks the classes you marked under `[looking for]` and **only** the ones you marked under `[registered]`. | You are **replacing** a class: mark the registered classes you keep and leave out the one you are swapping |

Examples of what to mark:

```
# add ECEN 340 and PHYS 221 on top of my schedule        (SELECT_MODE=all)
[looking for]
[x] ECEN 340 - Electric Energy Conversion
[x] PHYS 221 - Optics and Thermal Physics

# swap out MATH 308 for MATH 311: keep ECEN 350 and ECEN 370  (SELECT_MODE=specified)
[looking for]
[x] MATH 311 - Some Course
[registered]
[x] ECEN 350 - Computer Architecture and Design (CRN 12345)
[x] ECEN 370 - Electronic Properties of Materials (CRN 67890)
```

Only the classes you mark stay ticked in the "looking for" list; every other box in it is unticked. Under `[breaks]` mark the breaks you want ticked (mark none to leave your breaks alone, or set `BREAKS=all` / `BREAKS=none`). When you untick a registered class the page shows a warning box; the program clicks its OK button for you.

### Typing names instead (optional)

If you would rather type, put names on the `LOOKING_FOR=` / `REGISTERED=` lines in `settings.txt`, separated by commas (`LOOKING_FOR=ECEN 340, PHYS 221`). They are added to anything you marked. A name that matches nothing on the page prints a warning instead of guessing. `python main.py --list` prints everything on the page with its current state, without changing any file.

## Settings

All of these are lines in `settings.txt` (the first four are described above, and your checklist marks live at the bottom of the same file; the rest are optional and the example file has them commented out):

| Setting | Default | Meaning |
|---|---|---|
| `SELECT_MODE` | `off` | `off`, `all` or `specified` (see above) |
| `LOOKING_FOR` | empty | Optional: class names to look for, separated by commas (added to your checklist marks) |
| `REGISTERED` | empty | Optional: registered classes to keep ticked in `specified` mode |
| `BREAKS` | `leave` | `leave`, `all`, `none` or break names (breaks marked in the checklist win) |
| `WAIT_TIME` | `5` | Seconds between checks |
| `CALL_INTERVAL` | `120` | Seconds between repeated alerts once a schedule is found |
| `VOICE_ALERT` | `true` | Speak the alert on this computer |
| `MAKE_CALLS` | `true` | Place the Twilio call (needs the `TWILIO_*` values) |
| `REFRESH_PAGE` | `true` | Reload the page on every check |
| `CLICK_OK` | `true` | Click an `OK` button if one shows up |
| `CLICK_GENERATE` | `true` | Click `Generate Schedules` on every check |
| `TWILIO_VOICE_URL` | Twilio's public voice template | The TwiML URL Twilio plays when the call is answered |

The word the script looks for (`Generated`) and the spoken message are constants at the top of `main.py`.

## Files

| File | What it is |
|---|---|
| `main.py` | The monitor |
| `checklist.py` | Writes your page's classes into `settings.txt` and reads your x marks |
| `selection.py` | Finds the checkboxes for your classes and ticks them |
| `config.py` | Reads `settings.txt` and the Twilio settings |
| `test_twilio.py` | Places one test call |
| `settings.example.txt` | Template for your settings; the program copies it to `settings.txt` on first run |
| `settings.txt` | **Your** settings and class checklist (created on first run, git-ignored, never shared) |
| `requirements.txt` | Python packages |

## Troubleshooting

- **`Twilio is not configured`**: one of the four `TWILIO_*` values in `settings.txt` is empty. Fill them in or set `MAKE_CALLS=false`.
- **The call never arrives on a trial account**: the destination number must be a verified caller ID in your Twilio Console.
- **`WARNING: 'XYZ' was not found in the ... list`**: a name you typed on the `LOOKING_FOR=` / `REGISTERED=` lines does not match anything on the page. Use the checklist instead (it holds the exact names), or run `python main.py --list`.
- **`I could not find any classes on this page`**: the schedule builder was not showing when you pressed ENTER. Open the page that lists your Courses and Current Schedule, then run it again.
- **A class is missing from the checklist**: the list is refreshed from the page at the start of each run, so add the class on the page, then run again.
- **`Generate button not found`**: the page is not on the schedule options screen. Select your courses, or sign in again.
- **No spoken alert**: install the packages again (`pip install -r requirements.txt`) and check that Windows has a text-to-speech voice installed.
- **Browser not found**: run `playwright install chromium`.

## Keeping your keys safe

- `settings.txt` is listed in `.gitignore`; check `git status` before every commit and never paste its contents anywhere public.
- If a Twilio token ever ends up in a commit, a screenshot or a chat, **rotate it** in the Twilio Console right away.

## License

MIT. See [LICENSE](LICENSE).
