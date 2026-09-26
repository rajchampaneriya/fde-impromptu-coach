# FDE Impromptu Coach

Five minutes a day, on camera, answering five questions you have never seen,
each one a little harder than the last. Built for the communication and
leadership side of the **Forward Deployed Engineer** role.

Every morning at **05:30** your Mac:

1. writes 5 fresh impromptu questions (Claude Code, with a curated fallback bank),
   never repeating anything you have answered before and ramping up difficulty;
2. builds a minimalist blue, Calibri deck: a 10-second intro, then one question
   per slide with a 60-second progress bar that auto-advances;
3. opens it in PowerPoint (thumbnails collapsed so nothing is spoiled) and asks
   **Start now / Snooze / Later**.

When you start, QuickTime records your camera, the slides run by themselves, and
after about 5½ minutes everything stops. The video is saved to
`~/Movies/FDE-Impromptu/` and uploaded to YouTube as a **private** video with the
questions and chapter marks in the description. Your streak goes up.

Miss it, and reminders keep coming on the Mac (06:30, 07:30, 09:00, 12:30,
17:30, 19:30, 21:00 and a last call at 22:00). **Google Calendar** alerts you
too (phone app, calendar.google.com and email at 07:30, 12:30, 18:00 and 21:30),
but only on days you have not recorded yet, and even when the Mac is closed.
The streak is the point.

---

## 1. Install (about 3 minutes)

Requirements: macOS 12 or later, Microsoft PowerPoint, QuickTime Player (built in),
Claude Code (logged in), and Python 3.9+ (Apple's command line tools are enough:
`xcode-select --install`).

```bash
mkdir -p ~/.claude/skills
unzip ~/Downloads/fde-impromptu-coach.zip -d ~/.claude/skills/
bash ~/.claude/skills/fde-impromptu-coach/install.sh
```

Optional: `install.sh --time 06:00` to use a different daily time.

The installer creates `~/FDE-Impromptu/` (history, decks, logs, settings), a
Python virtual environment, the launcher `~/FDE-Impromptu/bin/fde-coach` (also
linked to `~/.local/bin/fde-coach`), and two background jobs (launchd agents).

### Approve the permission prompts

Right after installing, macOS asks for permissions once. Click **OK / Allow** on
each:

| Prompt | Why |
|---|---|
| "Python" wants to control "QuickTime Player" / "Microsoft PowerPoint" / "Reminders" | start the recording and the slide show, add the reminder |
| QuickTime Player would like to access the camera / microphone | the video itself (a 3-second preview opens as the check) |
| Script Editor notifications | reminder banners (macOS shows script notifications under "Script Editor") |

If you missed one, run `fde-coach doctor --warmup` to trigger them again, or turn
them on in **System Settings → Privacy & Security → Automation / Camera /
Microphone**, and **System Settings → Notifications → Script Editor**.

Check the result:

```bash
~/FDE-Impromptu/bin/fde-coach doctor
```

Then try a session: double-click **`~/FDE-Impromptu/Start Practice.command`**.

## 2. Google setup: YouTube + Calendar (once, about 10 minutes)

YouTube uploads and the Google Calendar alerts use your own free Google Cloud
project, so everything goes straight from your Mac to your account. Uploads from
a new, unverified API project are always private, which is exactly what this
tool wants.

1. Make sure your Google account has a YouTube channel (youtube.com → Create a channel).
2. Open <https://console.cloud.google.com/>, create a project (e.g. "FDE Practice").
3. **APIs & Services → Library** → search **YouTube Data API v3** → **Enable**.
   Then search **Google Calendar API** → **Enable**.
4. **Google Auth Platform** (older consoles: "OAuth consent screen") → **Get started**:
   app name "FDE Practice", your email as support and contact email,
   audience **External** → **Create**.
5. **Audience** → **Publish app** so the status reads **In production**.
   *Do not skip this.* In "Testing" status Google expires the sign-in every 7 days
   and uploads would stop weekly. You do not need Google verification for
   personal use.
6. **Clients** → **Create client** → application type **Desktop app** → **Create**
   → **Download JSON**.
7. Save that file as `~/FDE-Impromptu/secrets/client_secret.json`:
   ```bash
   mv ~/Downloads/client_secret_*.json ~/FDE-Impromptu/secrets/client_secret.json
   ```
8. Run `~/FDE-Impromptu/bin/fde-coach youtube-auth`. A browser opens: choose the
   account with your channel. Google warns "Google hasn't verified this app"
   because it is your own project: click **Advanced → Go to FDE Practice** →
   **Continue**. The tool asks only for permission to upload videos.
9. Run `~/FDE-Impromptu/bin/fde-coach calendar-auth` and approve the same way,
   choosing the Google account whose calendar you use. This permission lets the
   tool add and delete its own events only.

Any recordings made before this are uploaded right away. Videos are never made
public by this tool.

### How the missed-practice alerts work

Every day has a red "FDE practice not recorded yet" event at 21:30 in your
Google Calendar, with alerts at 07:30, 12:30, 18:00 and 21:30 plus an email at
12:30. Recording deletes that day's event, so on days you practise you never see
an alert. Events for the next two days are always in place, so the alerts still
arrive when the Mac is closed or off. The events don't block your free/busy time.

To receive them without an iPhone: install Google Calendar on your Android phone,
or turn on browser notifications in calendar.google.com (Settings → Notification
settings → Desktop notifications). The email alert goes to your Gmail either way.

Change the times with, for example:

```bash
fde-coach config --set 'google_calendar.popup_times=["08:00","13:00","20:00"]'
fde-coach config --set google_calendar.event_time=21:00
fde-coach calendar-sync
```

Google Calendar allows at most 5 alerts per event (popup + email together), all
at or before `event_time`. Turn the feature off with
`fde-coach config --set google_calendar.enabled=false` (upcoming events are removed).

## 3. Using it

| You want to… | Do this |
|---|---|
| Record today | Click **Start now** in the morning dialog, double-click `Start Practice.command`, or tell Claude Code "start my FDE practice" |
| See your streak | `fde-coach status` |
| Review past questions | `fde-coach history` (today's stay hidden until you have recorded) |
| Make questions harder or easier | tap **Too easy / Too hard** after a session, or `fde-coach level --up` / `--down` |
| Steer today's topic | ask Claude Code: "make today's FDE questions about a hospital rollout", or `fde-coach generate --replace --brief "hospital rollout"` |
| Tell the coach about yourself | `fde-coach config --set 'learner_context=Backend engineer moving into FDE roles at AI companies; I ramble when challenged'` |
| Change the time | `fde-coach config --set daily_time=06:15` |
| Change reminder times | `fde-coach config --set 'reminders.times=["07:00","12:30","20:00","22:00"]'` |
| Recorded some other way | `fde-coach complete --video ~/path/to/video.mov` |
| Check today's calendar alert | `fde-coach status` ("armed" means it will alert you until you record) |
| Something went wrong | `fde-coach doctor`, then `references/troubleshooting.md` |

During a session: look at the camera, not the slide. Each slide shows the
competency, difficulty dots, the question, sometimes a **constraint** (a twist such
as "No jargon: your listener is non-technical"), and a bar that fills over 60
seconds with a **Wrap up** cue at 0:45. Pressing **Esc** ends the slide show
early; the recording stops too, and if it is short you can keep it or try again.

After recording, the speaker notes of each slide (and the YouTube description)
list what a strong answer does and a five-point self-review checklist.

### How difficulty grows

Level 1–5, starting at 2. Every 6 recorded sessions adds a level. Each day ramps
(L, L, L+1, L+1, L+2). From level 3, constraint twists appear; after level 2 the
framework hints disappear. Twelve competencies rotate, least-practised first:
executive communication, technical translation, discovery, saying no, incidents
and bad news, influence without authority, prioritization, ownership, trust and
ethics, leadership, commercial conversations, and ambiguity.

## 4. Optional: wake the Mac for 05:30

If the Mac is asleep at 05:30, the practice is prepared as soon as it wakes
(nothing is lost). To have it ready on time, schedule a wake (needs admin, and
works best plugged in with the lid open):

```bash
sudo pmset repeat wakeorpoweron MTWRFSU 05:25:00
```

Undo with `sudo pmset repeat cancel`.

## 5. Google Slides

The deck uses only plain shapes, text and speaker notes, so it imports cleanly
into Google Slides (File → Import slides, or open the .pptx from Drive). Google
Slides ignores PowerPoint's per-slide timings: use **Slideshow → Auto-play → Every
minute** there. PowerPoint on the Mac is the primary, fully timed experience.

## 6. Privacy and where things live

| What | Where |
|---|---|
| Settings | `~/FDE-Impromptu/config.json` |
| Question history, streak | `~/FDE-Impromptu/state/history.json` |
| Decks | `~/FDE-Impromptu/decks/` |
| Videos | `~/Movies/FDE-Impromptu/` |
| Logs | `~/FDE-Impromptu/logs/` |
| YouTube and Calendar sign-in | `~/FDE-Impromptu/secrets/` (only readable by you) |

Only three things leave your Mac: the question-writing prompt sent through your
Claude Code login, the private video sent to your own YouTube channel, and the
missed-practice events in your own Google Calendar.

## 7. Uninstall

```bash
bash ~/.claude/skills/fde-impromptu-coach/uninstall.sh          # keeps history and videos, removes calendar alerts
bash ~/.claude/skills/fde-impromptu-coach/uninstall.sh --purge  # also deletes ~/FDE-Impromptu
```

Videos in `~/Movies/FDE-Impromptu/` are never deleted by the uninstaller.
