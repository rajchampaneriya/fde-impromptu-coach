"""Software Factory demos: every video shows real commands and their real output.

Two demo cities live under `factory.demo_root` (default ~/rajcwork-demo):
  file/    — Gas City with the file-based bead store (Week 1: no Dolt, no bd)
  default/ — the default setup (bd + Dolt), from Week 2 on
Each has a rig `hello-factory` (a small git repo) that grows across the series.

A day's demo is a list of steps (see references/factory_curriculum.md):
  {"run": cmd, "say": cue, "highlight": text, "save": {"name": regex}, "cwd": "rig|city|scratch"}
  {"wait_for": cmd, "until": text, "timeout": s, "say": cue}   -> shown as a time-lapse
  {"write": path, "content": text}                             -> hidden file setup
  {"hidden": true, ...}                                         -> runs, never shown
Values saved from earlier output are used as @{name}; @{city}, @{rig}, @{scratch} are built in.

`capture` runs the steps on the Mac and stores what they really printed; the
slides and the video are rendered from that capture (terminal animation, with
time-lapse cards for slow agent work). Nothing is screen-recorded.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import Paths
from .macos import dry_run

log = logging.getLogger("fdecoach")

STORES = ("file", "bd")
STORE_DIRS = {"file": "file", "bd": "default"}
RIG_NAME = "hello-factory"
VAR = re.compile(r"@\{(\w+)\}")
ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\r")
MAX_OUTPUT_LINES = 40
BUILTIN_VARS = ("city", "rig", "scratch", "rig_name")


# --------------------------------------------------------------------------- places

def root(cfg: Dict[str, Any]) -> Path:
    return Path(str(cfg.get("factory", {}).get("demo_root", "~/rajcwork-demo"))).expanduser()


def lab(cfg: Dict[str, Any], store: str) -> Dict[str, Path]:
    base = root(cfg) / STORE_DIRS[store]
    return {"base": base, "city": base / "city", "rig": base / RIG_NAME, "marker": base / ".ready.json"}


def is_ready(cfg: Dict[str, Any], store: str) -> bool:
    return lab(cfg, store)["marker"].exists()


def capture_path(paths: Paths, d: Dict[str, Any]) -> Path:
    return paths.factory / "demos" / f"Day{int(d['day']):02d}_{d['id']}.json"


def load_capture(paths: Paths, d: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    p = capture_path(paths, d)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _env(store: str) -> Dict[str, str]:
    env = dict(os.environ)
    for d in ("/opt/homebrew/bin", "/usr/local/bin", str(Path.home() / ".local/bin"),
              str(Path.home() / ".claude/local")):
        if d not in env.get("PATH", "").split(":"):
            env["PATH"] = env.get("PATH", "") + ":" + d
    if store == "file":
        env["GC_BEADS"] = "file"
    env.setdefault("TERM", "dumb")
    env["NO_COLOR"] = "1"
    return env


def tools_report(store: str, need_agent: bool = True) -> List[Tuple[str, bool, str]]:
    """[(tool, found, hint)] for what the demo cities need."""
    env = _env(store)
    out = []
    wanted = [("gc", "brew install gascity"), ("tmux", "brew install gascity (installs it)"),
              ("git", "xcode-select --install")]
    if store == "bd":
        wanted += [("bd", "brew install gascity (installs beads)"), ("dolt", "brew install gascity (installs dolt)")]
    if need_agent:
        wanted.append(("claude", "curl -fsSL https://claude.ai/install.sh | bash, then run claude once to log in"))
    for tool, hint in wanted:
        found = shutil.which(tool, path=env["PATH"]) is not None
        out.append((tool, found, hint))
    return out


# --------------------------------------------------------------------------- shell

def _sh(cmd: str, cwd: Path, store: str, timeout: int) -> Tuple[int, str, float]:
    t0 = time.time()
    try:
        proc = subprocess.run(["/bin/bash", "-lc", cmd], cwd=str(cwd), env=_env(store), capture_output=True,
                              text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        text = (proc.stdout or "") + (proc.stderr or "")
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        text = ((exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""))
        text += f"\n(timed out after {timeout} s)"
        code = 124
    return code, text, time.time() - t0


def clean_output(text: str, home: Optional[str] = None) -> List[str]:
    text = ANSI.sub("", text or "")
    home = home or str(Path.home())
    lines = [ln.rstrip().replace(home, "~") for ln in text.splitlines()]
    while lines and not lines[-1].strip():
        lines.pop()
    if len(lines) > MAX_OUTPUT_LINES:
        extra = len(lines) - MAX_OUTPUT_LINES
        lines = lines[:MAX_OUTPUT_LINES] + [f"… ({extra} more lines)"]
    return lines


def substitute(text: str, values: Dict[str, str]) -> str:
    return VAR.sub(lambda m: values.get(m.group(1), m.group(0)), text)


def shown_command(cmd: str, values: Dict[str, str]) -> str:
    """The command as viewers see it: saved values filled in, absolute demo paths shortened."""
    out = substitute(cmd, values)
    for key, label in (("rig", "~/hello-factory"), ("city", "~/lab"), ("scratch", "/tmp/scratch")):
        if values.get(key) and values[key].startswith("/"):
            out = out.replace(values[key], label)
    return out.replace(str(Path.home()), "~")


# --------------------------------------------------------------------------- setup

def setup(cfg: Dict[str, Any], store: str, log_lines: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create the demo city and its rig (idempotent)."""
    if store not in STORES:
        raise ValueError(f"store must be one of {STORES}")
    places = lab(cfg, store)
    say = log_lines.append if log_lines is not None else (lambda s: None)
    missing = [(t, hint) for t, ok, hint in tools_report(store) if not ok]
    if missing:
        return {"ok": False, "error": "missing tools: " + "; ".join(f"{t} ({h})" for t, h in missing)}
    places["base"].mkdir(parents=True, exist_ok=True)
    rig = places["rig"]
    if not (rig / ".git").exists():
        rig.mkdir(parents=True, exist_ok=True)
        (rig / "README.md").write_text("# hello-factory\n\nThe demo project for the rajcwork Software Factory "
                                       "series.\n", encoding="utf-8")
        for cmd in ("git init -q", "git add README.md",
                    "git -c user.name=rajcwork -c user.email=demo@rajcwork.local commit -q -m 'Start hello-factory'"):
            code, out, _ = _sh(cmd, rig, store, 60)
            if code:
                return {"ok": False, "error": f"git setup failed: {out[-200:]}"}
        say(f"created rig repo {rig}")
    city = places["city"]
    if not (city / "city.toml").exists():
        code, out, _ = _sh(f"gc init --template gascity --default-provider claude {_q(str(city))}",
                           places["base"], store, 600)
        say(out[-600:])
        if code or not (city / "city.toml").exists():
            return {"ok": False, "error": f"gc init failed: {out[-300:]}"}
        if store == "file":
            toml = (city / "city.toml").read_text(encoding="utf-8")
            if "[beads]" not in toml:
                (city / "city.toml").write_text(toml.rstrip() + '\n\n[beads]\nprovider = "file"\n',
                                                encoding="utf-8")
    code, out, _ = _sh("gc rig list", city, store, 120)
    if RIG_NAME not in out:
        code, out, _ = _sh(f"gc rig add {_q(str(rig))}", city, store, 300)
        say(out[-400:])
        if code:
            return {"ok": False, "error": f"gc rig add failed: {out[-300:]}"}
    places["marker"].write_text(json.dumps({"store": store, "at": dt.datetime.now().isoformat(timespec="seconds")}),
                                encoding="utf-8")
    return {"ok": True, "city": str(city), "rig": str(rig), "store": store}


def _q(text: str) -> str:
    return "'" + text.replace("'", "'\"'\"'") + "'"


# --------------------------------------------------------------------------- capture

def _cwd(step: Dict[str, Any], places: Dict[str, Path], scratch: Path) -> Path:
    return {"city": places["city"], "scratch": scratch}.get(step.get("cwd", "rig"), places["rig"])


def _simulated(demo: Dict[str, Any]) -> Dict[str, Any]:
    """Dry-run capture: the documented sample output (`expect`) or a short placeholder."""
    steps = []
    values = {"city": "~/lab", "rig": ".", "scratch": ".", "rig_name": RIG_NAME}
    for st in demo["steps"]:
        if st.get("hidden") or "write" in st:
            continue
        cmd = st.get("run") or st.get("wait_for")
        lines = list(st.get("expect") or ["(simulated output)"])
        for name, rx in (st.get("save") or {}).items():
            values.setdefault(name, f"{name}-1")
        steps.append({"cmd": shown_command(cmd, values), "output": lines, "code": 0, "seconds": 1.0,
                      "say": st.get("say", ""), "highlight": substitute(st.get("highlight", ""), values),
                      "timelapse": int(st.get("timeout", 0)) // 4 if "wait_for" in st else 0,
                      "cwd": st.get("cwd", "rig")})
    return {"ok": True, "simulated": True, "steps": steps}


def capture(paths: Paths, cfg: Dict[str, Any], d: Dict[str, Any]) -> Dict[str, Any]:
    """Run the day's demo in its demo city and save what really happened."""
    demo = d["demo"]
    store = demo.get("store", "bd")
    if dry_run():
        result = _simulated(demo)
    else:
        places = lab(cfg, store)
        if not is_ready(cfg, store):
            return {"ok": False, "error": f"demo city not set up: fde-coach factory demo setup --store {store}"}
        scratch = Path(tempfile.mkdtemp(prefix="rajcwork-scratch-"))
        values = {"city": str(places["city"]), "rig": str(places["rig"]), "scratch": str(scratch),
                  "rig_name": RIG_NAME}
        steps: List[Dict[str, Any]] = []
        result = {"ok": True, "simulated": False, "steps": steps}
        try:
            for i, st in enumerate(list(demo.get("setup") or []) + list(demo["steps"])):
                cwd = _cwd(st, places, scratch)
                if "write" in st:
                    target = Path(substitute(st["write"], values))
                    target = target if target.is_absolute() else cwd / target
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(substitute(st["content"], values), encoding="utf-8")
                    if st.get("mode") == "x":
                        target.chmod(0o755)
                    continue
                if "wait_for" in st:
                    cmd = substitute(st["wait_for"], values)
                    deadline = time.time() + int(st.get("timeout", 600))
                    t0 = time.time()
                    while True:
                        code, out, _ = _sh(cmd, cwd, store, 120)
                        if str(st.get("until", "")).lower() in out.lower():
                            break
                        if time.time() > deadline:
                            result.update(ok=False, failed_step=i,
                                          error=f"waited {int(st.get('timeout', 600))} s: "
                                                f"'{st.get('until')}' never appeared in `{cmd}`")
                            break
                        time.sleep(int(st.get("every", 10)))
                    seconds = time.time() - t0
                    timelapse = int(seconds)
                else:
                    cmd = substitute(st["run"], values)
                    code, out, seconds = _sh(cmd, cwd, store, int(st.get("timeout", 180)))
                    timelapse = 0
                    if code and not st.get("may_fail"):
                        result.update(ok=False, failed_step=i, error=f"`{cmd}` exited {code}: {out.strip()[-200:]}")
                for name, rx in (st.get("save") or {}).items():
                    m = re.search(rx, ANSI.sub("", out), re.MULTILINE)
                    if m:
                        values[name] = m.group(1)
                    elif result.get("ok"):
                        result.update(ok=False, failed_step=i, error=f"couldn't find {name} in the output of `{cmd}`")
                if not st.get("hidden") and i >= len(demo.get("setup") or []):
                    steps.append({"cmd": shown_command(st.get("run") or st["wait_for"], values),
                                  "output": clean_output(out), "code": code, "seconds": round(seconds, 1),
                                  "say": st.get("say", ""), "highlight": substitute(st.get("highlight", ""), values),
                                  "timelapse": timelapse, "cwd": st.get("cwd", "rig")})
                if not result.get("ok"):
                    break
        finally:
            for st in demo.get("teardown") or []:
                _sh(substitute(st, values), scratch, store, 120)
            shutil.rmtree(scratch, ignore_errors=True)
        _, ver, _ = _sh("gc version", Path.home(), store, 30)
        result["gc_version"] = ver.strip().splitlines()[-1] if ver.strip() else ""
    result.update(day=d["day"], topic=d["id"], store=store,
                  captured_at=dt.datetime.now().isoformat(timespec="seconds"))
    p = capture_path(paths, d)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log.info("demo capture Day %s: %s", d["day"], "ok" if result.get("ok") else result.get("error"))
    return result


# --------------------------------------------------------------------------- validation

def validate_demo(demo: Any) -> List[str]:
    if not isinstance(demo, dict):
        return ["demo must be an object with title, store and steps"]
    errs = []
    if not demo.get("title") or len(demo["title"]) > 60:
        errs.append("demo.title is required, at most 60 characters")
    if demo.get("store") not in STORES:
        errs.append(f"demo.store must be one of {STORES}")
    known = set(BUILTIN_VARS)
    shown = 0
    for i, st in enumerate(list(demo.get("setup") or []) + list(demo.get("steps") or [])):
        kinds = [k for k in ("run", "wait_for", "write") if k in st]
        if len(kinds) != 1:
            errs.append(f"step {i}: needs exactly one of run, wait_for, write")
            continue
        text = st[kinds[0]] + st.get("content", "")
        for name in VAR.findall(text):
            if name not in known:
                errs.append(f"step {i}: @{{{name}}} is used before it is saved")
        known.update((st.get("save") or {}).keys())
        if "wait_for" in st and not st.get("until"):
            errs.append(f"step {i}: wait_for needs until")
        if st.get("cwd", "rig") not in ("rig", "city", "scratch"):
            errs.append(f"step {i}: cwd must be rig, city or scratch")
        if len(st.get("say", "")) > 90:
            errs.append(f"step {i}: say is longer than 90 characters")
        if i >= len(demo.get("setup") or []) and "write" not in st and not st.get("hidden"):
            shown += 1
    if not 2 <= shown <= 7:
        errs.append(f"demo shows {shown} steps; use 2-7")
    return errs
