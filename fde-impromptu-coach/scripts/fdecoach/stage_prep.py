"""The Weekend Stage prep page: a local HTML page for the study half of the weekend.

It embeds TED's own player (TED's usage policy asks for the embeddable player and
does not allow scraping), links the transcript on ted.com instead of copying it,
and shows the segment, three watch passes, the beat-sheet rules and Take B's
prompt. Take C's twist is never on it: that stays a surprise until its slide.
"""
from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict

from .config import Paths
from .stage import catalogue, credit, segment_text

PASSES = (
    ("Normal", "What is the structure? Where are the beats?"),
    ("Muted", "Body only: stance, hands, where the eyes go."),
    ("Eyes closed", "Voice only: pace, pauses, pitch, the stressed words."),
)
BEAT_SHEET = ("5 to 7 keywords in your own words, never sentences. Mark a pause with / and a stressed word in "
              "CAPS. You perform from this, not from a script.")
SHADOW = ("Headphones on, speak along with the segment twice, half a beat behind. "
          "Headphones keep TED's audio out of your microphone.")


def prep_path(paths: Paths, session: Dict[str, Any]) -> Path:
    return paths.stage / f"{session['date']}_Stage_Week{session['day_number']}_prep.html"


def _e(text: Any) -> str:
    return html.escape(str(text), quote=True)


def render(session: Dict[str, Any]) -> str:
    talk = session["talk"]
    tb = talk["take_b"]
    seg = session["segment"]
    lic = catalogue().get("license") or {}
    week = session["day_number"]
    passes = "".join(f"<li><b>{_e(name)}.</b> {_e(what)}</li>" for name, what in PASSES)
    notes = "".join(f"<li>{_e(n)}</li>" for n in talk.get("watch_for") or [])
    find = "" if seg.get("start") and seg.get("end") else (
        "<p class=\"hint\">Found it? Save the times so the deck shows them: "
        "<code>fde-coach stage segment --start M:SS --end M:SS</code></p>")
    yt = (f' · <a href="{_e(talk["youtube_url"])}">TED on YouTube</a>' if talk.get("youtube_url") else "")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Weekend Stage · Week {week} · {_e(talk['speaker'])}</title>
<style>
  body {{ font: 17px/1.5 -apple-system, "Segoe UI", Calibri, sans-serif; color: #0B2545; margin: 0; background: #F1F6FD; }}
  main {{ max-width: 900px; margin: 0 auto; padding: 32px 24px 64px; }}
  .label {{ color: #1F5FBF; font-weight: 700; letter-spacing: .12em; font-size: 13px; text-transform: uppercase; }}
  h1 {{ font-size: 34px; margin: 6px 0 2px; }} h2 {{ font-size: 20px; margin: 28px 0 8px; }}
  .sub {{ color: #5B6B7F; }} .card {{ background: #fff; border-radius: 10px; padding: 18px 22px; margin: 14px 0; }}
  .player {{ position: relative; padding-bottom: 56.25%; height: 0; background: #0B2545; border-radius: 10px; overflow: hidden; }}
  .player iframe {{ position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }}
  .move {{ font-size: 22px; font-weight: 700; }} .hint {{ color: #5B6B7F; font-size: 15px; }}
  code {{ background: #DCE7F7; padding: 1px 6px; border-radius: 4px; font-size: 14px; }}
  textarea {{ width: 100%; min-height: 120px; font: inherit; padding: 10px; border: 1px solid #DCE7F7; border-radius: 8px; box-sizing: border-box; }}
  footer {{ color: #8A98A9; font-size: 13px; margin-top: 36px; }}
</style></head>
<body><main>
<div class="label">Weekend Stage · Week {week}{(' · ' + _e(session.get('phase'))) if session.get('phase') else ''}</div>
<h1>{_e(talk['title'])}</h1>
<div class="sub">{_e(talk['speaker'])} · {_e(talk['event'])} · {_e(talk['length'])} · {_e(talk['subject'])}</div>

<h2>1 · Watch (15 min)</h2>
<div class="player"><iframe src="{_e(talk['embed_url'])}" title="{_e(talk['title'])} (TED)" allowfullscreen></iframe></div>
<p class="hint"><a href="{_e(talk['ted_url'])}">Open on ted.com</a>{yt} ·
<a href="{_e(talk['ted_url'])}/transcript">Read the transcript on ted.com</a></p>
<div class="card"><b>Segment:</b> {_e(segment_text(seg))}{find}</div>
<div class="card"><b>Three passes over the segment</b><ol>{passes}</ol>
<b>Watch for</b><ul>{notes}</ul></div>
<div class="card"><div class="label">Move to steal</div><div class="move">{_e(talk['move'])}</div></div>

<h2>2 · Beat sheet (5 min)</h2>
<p>{_e(BEAT_SHEET)}</p>
<textarea id="beats" placeholder="hook / ONE idea / ..."></textarea>
<p class="hint">Kept in this browser only. Paper works just as well.</p>

<h2>3 · Shadow (5 min)</h2>
<p>{_e(SHADOW)}</p>

<h2>4 · Then record (about 10 min on camera)</h2>
<div class="card"><b>Take A · Mirror.</b> The segment, from your beat sheet, as the speaker would do it.</div>
<div class="card"><b>Take B · Make it yours.</b> To <b>{_e(tb['listener'])}</b>, who cares about {_e(tb['cares'])}:
{_e(tb['prompt'])}</div>
<div class="card"><b>Take C · Pressure.</b> A twist you'll see only on its slide.</div>
<p>Start with <code>fde-coach stage session</code>, or type <code>/stage</code> in Claude Code.</p>

<footer>{_e(credit(talk))}<br>
This page embeds TED's player and links to ted.com; it copies none of the talk.
<a href="{_e(lic.get('policy', ''))}">TED Talks usage policy</a>.</footer>
</main>
<script>
try {{
  var box = document.getElementById("beats"), key = "fde-stage-beats-{_e(talk['id'])}";
  box.value = localStorage.getItem(key) || "";
  box.addEventListener("input", function () {{ try {{ localStorage.setItem(key, box.value); }} catch (e) {{}} }});
}} catch (e) {{}}
</script>
</body></html>
"""


def write(paths: Paths, session: Dict[str, Any]) -> Path:
    out = prep_path(paths, session)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name("." + out.name + ".tmp")
    tmp.write_text(render(session), encoding="utf-8")
    tmp.replace(out)
    return out
