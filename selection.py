"""Choose which classes are ticked on the College Scheduler page, by NAME instead of by page element.

The page has three groups of checkboxes and this module knows how to find each one:

    looking for   the "Courses" list (classes you want to get into)
    registered    the "Current Schedule" table (classes you are already enrolled in)
    breaks        the "Breaks" list

You give names in settings.txt (for example "ECEN 340" or "PHYS 221"; a 5-digit CRN also works for
registered classes) and the program finds the matching checkbox for you.
"""
import re
import time

# How to find each group's checkboxes. (These are the page's own ids / table, not something users have to touch.)
GROUPS = {
    "looking for": {
        "boxes": 'input[type="checkbox"][id^="course_checkbox_"]',
        "select_all": "#select_all_courses",
        "prefix": "Select ",
    },
    "registered": {
        "boxes": 'table:has(#checkbox_select_all_Registered) tbody input[type="checkbox"]',
        "select_all": "#checkbox_select_all_Registered",
        "prefix": "Select ",
    },
    "breaks": {
        "boxes": 'input[type="checkbox"][id^="break_checkbox_"]',
        "select_all": "#select_all_breaks",
        "prefix": "Select Break ",
    },
}

CODE_LIKE = re.compile(r"^[A-Za-z]{2,5}\s*\d{3,4}[A-Za-z]?$")      # e.g. "ECEN 340", "PHYS221"


def compact(text):
    return re.sub(r"\s+", "", text or "").lower()


def split_names(value):
    """'ECEN 340, PHYS 221' -> ['ECEN 340', 'PHYS 221']  (commas or semicolons)."""
    return [part.strip() for part in re.split(r"[;,]", value or "") if part.strip()]


def read_group(page, group):
    """Return [{'label', 'id', 'box'}] for every checkbox in the group, using the page's own accessible names."""
    spec = GROUPS[group]
    items = []
    boxes = page.locator(spec["boxes"])
    for i in range(boxes.count()):
        box = boxes.nth(i)
        box_id = box.get_attribute("id") or ""
        if "select_all" in box_id:
            continue
        label = (box.get_attribute("aria-label") or "").strip()
        if label.startswith(spec["prefix"]):
            label = label[len(spec["prefix"]):]
        items.append({"label": label, "id": box_id, "box": box})
    return items


def name_matches(name, item):
    """Does the name the user typed refer to this checkbox?"""
    name = name.strip()
    if not name:
        return False
    # a CRN (5 digits) matches the registered section with that CRN
    if re.fullmatch(r"\d{5}", name) and item["id"].endswith("_" + name):
        return True
    label_c, name_c = compact(item["label"]), compact(name)
    if CODE_LIKE.match(name):
        # course code: must be at the start of the label and not the start of a longer number (340 vs 3401)
        return label_c.startswith(name_c) and not label_c[len(name_c):len(name_c) + 1].isdigit()
    # anything else (a break's name, part of a course title): text match
    return name_c in label_c


def dismiss_modal(page):
    """The page pops up a warning (for example when you untick a registered class) that must be OK'd.
    Click its OK button if one is showing. Returns True if a dialog was closed."""
    try:
        button = page.locator('.modal.in button:has-text("OK"), [role="dialog"] button:has-text("OK")')
        if button.count() and button.first.is_visible():
            button.first.click(timeout=2000)
            time.sleep(0.4)
            return True
    except Exception:
        pass
    return False


def set_checked(box, wanted, wait=3.0):
    """Make a checkbox ticked/unticked and confirm it. Returns True if it ends in the wanted state.

    The page updates a moment AFTER a click, so after clicking we wait (up to `wait` seconds) for the new state
    before trusting it, and only click again if it still has not changed.
    """
    page = box.page
    dismiss_modal(page)
    try:
        if box.is_checked() == wanted:
            return True
        if not box.is_enabled():
            return False
    except Exception:
        return False

    for _attempt in range(2):
        try:
            # a script click works even when the page's sticky header or a scroll position covers the box
            box.evaluate("el => el.click()")
        except Exception:
            try:
                box.click(force=True, timeout=3000)
            except Exception:
                pass
        deadline = time.time() + wait
        while time.time() < deadline:
            dismiss_modal(page)
            try:
                if box.is_checked() == wanted:
                    return True
            except Exception:
                pass
            time.sleep(0.1)
    return False


def apply_group(page, group, names, log=print):
    """Tick exactly the checkboxes that match `names` in one group, and untick the others.

    names == ["all"]  ticks everything in the group,  names == ["none"] unticks everything.
    Returns a list of names that matched nothing on the page.
    """
    items = read_group(page, group)
    wants_all = any(n.lower() == "all" for n in names)
    wants_none = any(n.lower() == "none" for n in names)
    missing = []
    chosen = set()

    if not (wants_all or wants_none):
        for name in names:
            hits = [i for i, item in enumerate(items) if name_matches(name, item)]
            if not hits:
                missing.append(name)
            chosen.update(hits)

    changed = []
    for idx, item in enumerate(items):
        want = True if wants_all else False if wants_none else idx in chosen
        before = None
        try:
            before = item["box"].is_checked()
        except Exception:
            pass
        ok = set_checked(item["box"], want)
        if before is not None and before != want and ok:
            changed.append(("ticked " if want else "unticked ") + item["label"])
        elif not ok and (before is None or before != want):
            log(f"  could not change: {item['label']}")
    for text in changed:
        log(f"  [{group}] {text}")
    return missing


def apply_selection(page, mode, looking_for, registered, breaks, log=print):
    """Apply the user's choices.

    mode "off"        leave every checkbox alone
    mode "all"        tick the looking-for classes you named, and ALL registered classes
    mode "specified"  tick the looking-for classes you named, and ONLY the registered classes you named
                      (use this to replace a class: leave the one you want to drop out of `registered`)
    breaks            "leave" (default), "all", "none", or a list of break names
    """
    problems = []
    if mode == "off":
        return problems

    if looking_for:
        problems += [("looking for", n) for n in apply_group(page, "looking for", looking_for, log)]

    if mode == "all":
        problems += [("registered", n) for n in apply_group(page, "registered", ["all"], log)]
    elif mode == "specified":
        problems += [("registered", n) for n in apply_group(page, "registered", registered or ["none"], log)]

    if breaks and [b.lower() for b in breaks] != ["leave"]:
        problems += [("breaks", n) for n in apply_group(page, "breaks", breaks, log)]

    for group, name in problems:
        log(f"  WARNING: '{name}' was not found in the {group} list on the page")
    return problems


def list_page(page, log=print):
    """Print everything on the page that can be chosen, with its current state: shows users exactly what to type."""
    for group in ("looking for", "registered", "breaks"):
        log(f"\n{group.upper()}:")
        items = read_group(page, group)
        if not items:
            log("  (nothing found: is the page showing the schedule builder?)")
        for item in items:
            try:
                state = "ticked  " if item["box"].is_checked() else "unticked"
            except Exception:
                state = "?       "
            crn = item["id"].rsplit("_", 1)[-1] if group == "registered" else ""
            log(f"  [{state}] {item['label']}" + (f"   (CRN {crn})" if crn else ""))
