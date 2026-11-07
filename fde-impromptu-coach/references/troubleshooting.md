# Troubleshooting

Start with `fde-coach doctor` (add `--warmup` to re-trigger macOS permission
prompts). Logs: `~/FDE-Impromptu/logs/fde_coach.log` (all commands),
`daily.err.log` / `reminder.err.log` (launchd output), `background.log`
(detached sessions and uploads).

If today is at risk, protect the streak first: record any way you can
(QuickTime → File → New Movie Recording, or your phone) and run
`fde-coach complete --video PATH` (or `--no-video`). Fix the cause afterwards.

| Symptom | Likely cause | Fix |
|---|---|---|
| `/legato`, `/impromptu`, `/pronunciation`, `/stage` or `/fde-learn` is "unknown", or Claude doesn't recognise a practice | the skills are not in `~/.claude/skills/<name>/SKILL.md` (installed from a clone without linking, a copied folder, or the repo cloned *inside* `~/.claude/skills`, one level too deep) | `fde-coach doctor` shows the *Claude Code skills* line. From your clone: `bash fde-impromptu-coach/link_skills.sh` (`--check` to verify), then start a new Claude Code session. A clone inside `~/.claude/skills`: move it (e.g. to `~/Code/fde-impromptu-coach`) and run `install.sh` again |
| Nothing happened at 05:30 | Mac asleep or off | The 15-minute agent prepares everything when the Mac wakes. For on-time readiness: `sudo pmset repeat wakeorpoweron MTWRFSU 05:25:00` |
| `doctor` shows an agent "not loaded" | agents removed or failed to load | `fde-coach install-agents` |
| No dialogs or banners | Focus / Do Not Disturb, or notifications off for Script Editor | System Settings → Notifications → Script Editor → Allow; allow it in your Focus mode |
| "Python" is not allowed to control QuickTime / PowerPoint / Reminders | Automation permission denied | System Settings → Privacy & Security → Automation → enable the switches under Python (and Terminal if you start from Terminal or Claude Code). Then `fde-coach doctor --warmup` |
| Black video or no sound | QuickTime lacks camera or microphone access, or wrong input selected | Privacy & Security → Camera / Microphone → QuickTime Player. In QuickTime, the menu next to the record button picks the camera and mic; it remembers the choice |
| Guided mode appeared (manual record button) | QuickTime automation failed | Follow the dialog; fix Automation permission afterwards |
| "Automatic saving didn't work" | QuickTime refused the scripted save | Press ⌘S in QuickTime and save into `~/Movies/FDE-Impromptu`; the tool finishes by itself when the file appears |
| Slides don't advance | "Use Timings" off, or you clicked during the show | The deck enables Use Timings; in PowerPoint check Slide Show → Use Timings. Don't click during the show |
| Timer bar doesn't move | Opened in an app without animation support | Use Microsoft PowerPoint; Keynote and Google Slides ignore these timings |
| Questions came from the "bank" | Claude Code unavailable (not logged in, offline, usage limit, slow) | Run `claude` once in Terminal and log in; `fde-coach doctor` shows the path. Set `claude_path` if Claude Code lives elsewhere. The bank keeps the streak safe meanwhile |
| Answer key says "Model answer pending" | Claude Code unavailable when the session finished (offline, usage limit, not logged in) | Nothing to do: the 15-minute tick fills it in and notifies you (up to `answer_key.max_attempts`). Now: `fde-coach answers --open`. `answer_key.last_error` in `fde-coach status --json` says why |
| Answer key didn't open after the session | it opens when the practice chain (FDE → pronunciation → legato) ends, or `answer_key.open_after_session=false` | `fde-coach answers --open` |
| `fde-coach answers` refuses | today isn't recorded yet (model answers would spoil the surprise) | Record first, or `--reveal` if you really want them now |
| Too many / too few exec slides | `exec_mode.focus_slots` (default 2); bank questions with an executive listener also become exec slides | `fde-coach config --set exec_mode.focus_slots=N`; `exec_mode.enabled=false` turns exec slides off |
| Questions feel too easy / hard | calibration | Tap the after-session feedback, or `fde-coach level --up` / `--down`, then `fde-coach generate --replace` (before recording) |
| YouTube: "authorization expired" every week | Google OAuth app still in **Testing** | Google Auth Platform → Audience → Publish app (In production), then `fde-coach youtube-auth` |
| YouTube: "Connect YouTube once" | not authorized yet | README → YouTube setup, then `fde-coach youtube-auth` |
| YouTube: quota or 403 errors | daily API quota used up, or channel missing | Failed uploads retry automatically (up to 12 times); check the account has a YouTube channel; `fde-coach upload` to retry now |
| No Google Calendar alerts on a missed day | not connected, Calendar API not enabled, or notifications off on the device | `fde-coach doctor`; enable **Google Calendar API** in the Cloud project and run `fde-coach calendar-auth`; turn on notifications in the Google Calendar app or calendar.google.com → Settings → Notification settings |
| Calendar alert fired although I recorded | recorded on another machine, or the Mac was offline when you recorded | `fde-coach calendar-sync` (it also runs every 15 minutes and deletes the event once online) |
| Calendar: "authorization expired" | OAuth app in Testing, or access removed | publish the app (In production), then `fde-coach calendar-auth` |
| Leftover "FDE practice not recorded yet" events | tool uninstalled without cleanup | `fde-coach calendar-sync --clear`, or delete them in Google Calendar |
| Upload status "missing" | video file moved or deleted | Put it back at the recorded path, or upload it by hand |
| Pronunciation or legato video skipped | ffmpeg not installed | `brew install ffmpeg`; the .m4a is always kept. Retry with `fde-coach pronounce upload` / `fde-coach legato upload` (the 15-minute tick also retries) |
| Pronunciation audio not saved | QuickTime save quirk on macOS 26 | Same fallbacks as the FDE recording; the guided dialog asks you to press ⌘S. The .m4a lands in `~/Movies/FDE-Impromptu/pronunciation/` |
| Pronunciation words never change | every word retired (4 easy answers in a row) | `fde-coach pronounce words --add WORD` — new words enter the schedule immediately |
| Nothing happened at 05:45 | pronouncing agent not loaded | `fde-coach install-agents` (reinstalls every agent); check `pronounce.err.log` |
| Nothing happened at 06:00 | legato agent not loaded, or legato turned off | `fde-coach install-agents`; `fde-coach legato status` says if it is off (`config --set legato.enabled=true`); check `legato.err.log` |
| Nothing happened on Saturday at 08:00 | Mac asleep, the stage agent not loaded, or Weekend Stage turned off | Sunday 08:00 reopens the same weekend. `fde-coach install-agents`; `fde-coach stage status` says if it is off (`config --set stage.enabled=true`); check `stage.err.log` |
| Weekend Stage prep page shows no video | offline, or the browser blocks TED's embedded player | Use *Open on ted.com* under the player; the segment, passes and prompts on the page still apply |
| Take A says "find it on your first watch" | no start and end saved for this talk's segment yet | `fde-coach stage segment --start M:SS --end M:SS`; an unrecorded deck is rebuilt with them |
| No "Pronunciation practice next?" after the FDE session (older versions) | the prompt checked the session lock while still holding it, so it never showed | Fixed: the next practice is offered after the lock is released (FDE → pronunciation → legato). Turn the prompts off with `pronunciation.prompt_after_fde=false` / `legato.prompt_after_pronunciation=false` |
| Pronunciation warm-up shows words without respellings | a due word has no coach notes yet and Claude Code was unavailable | It still works; the notes are added the next time Claude Code answers. `fde-coach doctor` shows the Claude CLI |
| Want the old AI-written work paragraphs back | — | `fde-coach config --set pronunciation.paragraph_source=claude` |
| Same few passages keep coming | a narrow `themes` filter, or every passage has been read once | `fde-coach config --set 'legato.themes=[]'` (same under `pronunciation`); add books with `fde-coach library import-gutenberg N` |
| `library import-gutenberg` fails | offline, wrong ebook number, or the book has no plain-text edition | Check gutenberg.org/ebooks/N; download the .txt yourself and use `library import-file PATH --author … --title …` |
| Imported book added 0 passages | its paragraphs are mostly dialogue, verse or very long | Try `--max 40`, or another book; prose of 50–130-word paragraphs works best |
| Worried a built-in passage was altered | — | `python3 scripts/tools/build_passage_library.py verify` re-downloads the editions and compares every passage |
| YouTube playlist never filled (older versions) | `add_to_playlist` raised NameError | Fixed; set `youtube.pronunciation_playlist_id` / `youtube.legato_playlist_id` |
| Old pronunciation agent kept firing after uninstall | `uninstall.sh` skipped `com.fdecoach.pronounce` | Fixed (removes every agent). Clean up by hand: `launchctl bootout gui/$(id -u)/com.fdecoach.pronounce` |
| Deck file deleted | — | Any command (`fde-coach open`) rebuilds it from the saved questions |
| Broke after a Homebrew Python upgrade | the virtual environment points at a removed Python | Re-run `install.sh` (history is kept) |
| Want to start fresh | — | `bash uninstall.sh --purge`, then `install.sh` |

## Running the tests

From your clone of the repo, `make test` runs the whole suite once and keeps the
full output in `.test-output.log`. Without make:

```bash
cd ~/.claude/skills/fde-impromptu-coach
~/FDE-Impromptu/venv/bin/python -m unittest discover -s scripts/tests -v
```

The suite simulates macOS (`FDE_COACH_DRYRUN=1`), uses a throw-away data
folder and a fake Claude CLI, and never records, uploads or touches your
schedule. A clean run ends in `OK`; skipped tests are expected (off macOS the two
ffmpeg video tests skip, because the slides need the Apple Symbols font).

## Useful environment variables (testing and debugging)

`scripts/tools/sandbox.sh` (or `make sandbox ARGS='…'` from the clone) sets the
test ones for you and runs one command in a throw-away home.

| Variable | Effect |
|---|---|
| `FDE_COACH_HOME` | use another data folder |
| `FDE_COACH_DRYRUN=1` | simulate every macOS action (no dialogs, recording or upload) |
| `FDE_COACH_DRYRUN_ANSWERS='Start now,Later'` | with dry-run: the answers to the next dialogs, in order |
| `FDE_COACH_NOW=2026-10-01T07:31:00` | pretend it is that time (reminder testing) |
| `FDE_COACH_TODAY=2026-10-01` | pretend it is that day (wins over `FDE_COACH_NOW` for the date) |
| `FDE_COACH_RECORDINGS` | use another recordings folder |
| `FDE_COACH_AGENTS_DIR` | write the launchd agents somewhere other than `~/Library/LaunchAgents` |
| `FDE_COACH_NO_CLAUDE_DISCOVERY=1` | use only `claude_path` from the settings; never look for the real `claude` |
| `FDE_COACH_SKIP_NETWORK_WAIT=1` | don't wait for the network before calling Claude |
