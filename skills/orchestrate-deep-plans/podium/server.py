#!/usr/bin/env python3
"""The Podium server of the orchestrate skill this folder sits in.

Serves `podium.html` (next to this file) plus the run directory (default
`.deep-plan/`, whose `podium/` folder holds the orchestrator's files) on 127.0.0.1, and turns the
Podium's buttons into lines in `requests.jsonl`, which the orchestrator
watches. The browser only ever sends an action and a story id; prompts are
built by the orchestrator from the story brief.

GET /prompt/<plan|assign>/<id> returns the prompt the orchestrator would act
on, for the user to run in a session of their own: `/<skill> <id>`
for a milestone; for a story, the story prompt of ../phase-3-build.md (its
single source) filled in, after a step that sets up its worktrees.

POST /handoff/<story> hands a ready story of the active milestone to such a
session: it records the story in `handoffs.json` (this server is its only
writer), so the orchestrator leaves it alone, and returns its prompt.
DELETE /handoff/<story> takes it back.

POST /asana[/<epic>]?url=<Asana link> queues a link of an Asana project or
task (or of an epic to its task) as an `asana` request, like settling an
assumption kept for the next orchestrator run, so it needs no watcher.
POST /asana-done/<milestone>?choice=<drop|keep> queues the user's answer for a
milestone completed in Asana but not landed here, the same way.

The buttons that need the orchestrator (assign, plan, build-all, stop, a
hand-off) answer 409 while no watcher is running (watcher.json older than
30 s): nothing would read the request. GET /info says `watching`.

The availability toggle writes `human.json` (this server is its only writer):
POST /human/<available|unavailable|auto>[?until=HH:MM]. GET /human returns
podium.py's reading of the user's availability.

It stops itself after --idle minutes (default 60, 0 = never) without
activity: a Podium tab in view and used in the last 10 minutes (its polls carry X-Podium-Visible), a button,
or a change to podium.json, events.jsonl or a story's progress file.
--detach binds the port, prints the URL and returns, leaving the server
running in the background with its output in server.log in the podium dir.

GET /git says, per repo the run works in (its own, plus the active milestone's
`repos`), how far the checkout's branch and the default branch are behind
origin, refreshed by a `git fetch` every --git-every minutes (default 5,
0 = never): a run that moved on another machine shows in the Podium.

    python3 server.py [--dir .deep-plan] [--port 8765] [--idle 60] [--detach] [--git-every 5]
"""
import argparse
import glob
import threading
import mimetypes
import urllib.parse
import json
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from podium import HOURS, availability, next_change, podium_dir  # one reading of the user's availability and files

# Run files that are normal to lack early on: an empty answer instead of a 404 on every poll.
EMPTY_WHEN_MISSING = {"handoffs.json": {}, "events.jsonl": "", "requests.jsonl": ""}

STORY_ID = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
ACTIONS = {"assign", "plan", "build-all", "stop", "confirm", "reverse"}
ID_ACTIONS = {"assign", "plan", "confirm", "reverse"}  # these take an id
# The user settling an assumption: an answer, kept until an orchestrator runs, so it needs no watcher.
SETTLE = {"confirm", "reverse"}
# Linking Asana is the user's own request too: queued for the orchestrator, watcher or not.
QUEUED = SETTLE | {"asana", "asana-done"}
ASANA_URL = re.compile(r"^https://app\.asana\.com/[\w/?=&.-]{1,300}$")


def load_run(root):
    """The run's milestones (across every epic) and the active milestone, from podium.json or an older epic.json."""
    for name in ("podium.json", "epic.json"):
        try:
            with open(os.path.join(podium_dir(root), name)) as f:
                data = json.load(f)
            break
        except (OSError, ValueError):
            data = None
    if not data:
        return [], None
    if "epics" in data:
        milestones = [m for e in data["epics"] for m in e.get("milestones", [])]
        active_id = (data.get("active") or {}).get("milestone")
    else:
        milestones = data.get("milestones") or [{"id": data.get("epic", {}).get("id"), "stories": data.get("stories", [])}]
        active_id = data.get("active") or milestones[0].get("id")
    active = next((m for m in milestones if m.get("id") == active_id), None)
    return milestones, active


PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "podium.html")
PHASE_3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phase-3-build.md")
def paseo_server():
    """The local Paseo daemon's server id, which its agent deep links need, or None."""
    try:
        with open(os.path.expanduser("~/.paseo/server-id")) as f:
            return f.read().strip() or None
    except OSError:
        return None


SKILL = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # the command this Podium belongs to


def story_prompt(root, milestone, story):
    """The story prompt of phase-3-build.md for one story, after a step that creates the worktrees the
    orchestrator otherwise makes at dispatch: one per repo in the story's `repos`, else one beside the repo."""
    with open(PHASE_3) as f:
        template = re.search(r"Story prompt[^\n]*\n+```\n(.*?)\n```", f.read(), re.S).group(1)
    sid, mid = story["id"], milestone["id"]
    if story.get("repos"):
        repos = milestone.get("repos") or {}
        trees = {r: os.path.join(root, "worktrees", sid, r) for r in story["repos"]}
        setup = [f"git -C {repos[r]['path']} worktree add -b story/{sid} {t} {repos[r]['branch']}" for r, t in trees.items()]
    else:
        repo = os.path.dirname(root)
        trees = {os.path.basename(repo): f"{repo}-{sid}"}
        setup = [f"git -C {repo} worktree add -b story/{sid} {repo}-{sid} {milestone.get('branch')}"]
    body = (template.replace(" <repo>: <path>, one per line.", "\n" + "\n".join(f"{r}: {t}" for r, t in trees.items()))
            .replace("<podium dir>", podium_dir(root)).replace("<milestone>", mid).replace("<id>", sid))
    return (f"You run outside the orchestrator, which tracks you only through the progress file named below: "
            f"log STARTED before anything else and end on COMMITTED or FAILED. It merges your commit when it reads COMMITTED.\n\n"
            f"First set up your worktree{'s' if len(trees) > 1 else ''}, then work only there:\n" + "\n".join(setup) + "\n\n" + body + "\n")


def watching(root):
    """Whether an orchestrator's watcher is running: its heartbeat in watcher.json is under 30 s old."""
    try:
        with open(os.path.join(podium_dir(root), "watcher.json")) as f:
            return time.time() - json.load(f)["at"] < 30
    except (OSError, ValueError, KeyError):
        return False


def handoffs(root):
    """handoffs.json: {"<milestone>/<story>": {at}} for each story the user took to a session of their own."""
    try:
        with open(os.path.join(podium_dir(root), "handoffs.json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


# Each repo's distance from origin, refreshed by watch_git; GET /git serves it.
GIT = {"repos": [], "at": None}


def git(repo, *args, timeout=30):
    """A git command's output, or None when it fails or hangs (a fetch never prompts for credentials)."""
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def repos_of(root):
    """{name: path} for the run's own repo and the active milestone's `repos`."""
    out, repo = {}, os.path.dirname(root)
    if git(repo, "rev-parse", "--git-dir"):
        out[os.path.basename(repo)] = repo
    _, active = load_run(root)
    for name, r in ((active or {}).get("repos") or {}).items():
        if (r or {}).get("path"):
            out[name] = os.path.expanduser(r["path"])
    return out


def repo_state(name, path):
    git(path, "fetch", "--quiet", "--no-tags", timeout=60)
    branch = git(path, "rev-parse", "--abbrev-ref", "HEAD")
    lr = git(path, "rev-list", "--left-right", "--count", "HEAD...@{u}")
    ahead, behind = map(int, lr.split()) if lr else (0, 0)
    base = (git(path, "symbolic-ref", "--short", "refs/remotes/origin/HEAD") or "origin/main").split("/", 1)[-1]
    base_behind = git(path, "rev-list", "--count", f"{base}..origin/{base}") if base != branch else None
    return {"name": name, "branch": branch, "ahead": ahead, "behind": behind, "base": base,
            "baseBehind": int(base_behind) if base_behind else 0}


def watch_git(root, minutes):
    while True:
        GIT["repos"] = [repo_state(n, p) for n, p in repos_of(root).items()]
        GIT["at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        time.sleep(minutes * 60)


# The last time someone used the Podium; the idle check reads it.
SEEN = {"at": time.time(), "by": "start"}


def last_activity(root):
    """The latest of the last Podium use and the last change to the run's files."""
    pd = podium_dir(root)
    paths = [os.path.join(pd, "podium.json"), os.path.join(pd, "events.jsonl")] + glob.glob(os.path.join(pd, "stories", "*", "*.progress"))
    mtimes = [os.path.getmtime(p) for p in paths if os.path.exists(p)]
    return max([SEEN["at"]] + mtimes)


def stop_when_idle(server, root, minutes):
    while True:
        time.sleep(60)
        if time.time() - last_activity(root) > minutes * 60:
            print(f"{datetime.now():%H:%M} idle for {minutes} min, stopping", flush=True)
            server.shutdown()
            return


def make_handler(root):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=root, **kw)

        def parse_request(self):
            ok = super().parse_request()
            if ok and (self.command != "GET" or self.headers.get("X-Podium-Visible") == "1"):
                SEEN.update(at=time.time(), by=f"{self.command} {self.path.split('?')[0]} from {self.headers.get('User-Agent', '?')[:60]}")
            return ok

        def log_message(self, *_):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def do_GET(self):
            if self.path == "/info":
                return self.reply(200, {"runDir": root, "repoDir": os.path.dirname(root), "watching": watching(root), "skill": SKILL, "paseoServer": paseo_server(),
                                        "lastUse": {"ago": round(time.time() - SEEN["at"]), "by": SEEN["by"]}})
            if self.path == "/git":
                return self.reply(200, GIT)
            if self.path.startswith("/prompt/"):
                return self.prompt(*([p for p in self.path.split("/") if p][1:] + [None, None])[:2])
            if self.path == "/human":
                return self.reply(200, availability(root, self.podium()))
            if os.path.basename(self.path.split("?")[0]) in EMPTY_WHEN_MISSING and not os.path.exists(self.translate_path(self.path)):
                return self.empty(EMPTY_WHEN_MISSING[os.path.basename(self.path.split("?")[0])])
            if self.path.startswith("/repo/"):
                return self.repo_file(self.path[len("/repo/"):].split("?")[0])
            if self.path.split("?")[0] in ("/", "/index.html", "/podium.html"):
                with open(PAGE, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            super().do_GET()

        def repo_file(self, rel):
            """A file of the repo the run dir sits in, read-only: a mock kept outside the run dir."""
            base = os.path.realpath(os.path.dirname(root))
            full = os.path.realpath(os.path.join(base, urllib.parse.unquote(rel)))
            if not full.startswith(base + os.sep) or not os.path.isfile(full):
                return self.send_error(404)
            with open(full, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(full)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            url = urlparse(self.path)
            first = ([p for p in url.path.split("/") if p] or [""])[0]
            if not url.path.startswith("/human/") and first not in QUEUED and not watching(root):
                return self.reply(409, {"error": "no orchestrator is watching"})
            if url.path.startswith("/handoff/"):
                return self.handoff(url.path[len("/handoff/"):], take=True)
            if url.path.startswith("/human/"):
                return self.toggle(url.path[len("/human/"):], parse_qs(url.query).get("until", [None])[0])
            parts = [p for p in url.path.split("/") if p]
            action = parts[0] if parts else ""
            if action == "asana":
                return self.link_asana(parts[1] if len(parts) > 1 else None, parse_qs(url.query).get("url", [""])[0].strip())
            if action == "asana-done":
                return self.asana_done(parts[1] if len(parts) > 1 else "", parse_qs(url.query).get("choice", [""])[0])
            story = parts[1] if len(parts) > 1 else None
            if action not in ACTIONS or (action in ID_ACTIONS) != (story is not None):
                return self.reply(404, {"error": "unknown action"})
            if story is not None:
                if not STORY_ID.match(story) or story not in self.known_ids(action):
                    return self.reply(404, {"error": "unknown id"})
            line = {"action": action, "story": story,
                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            note = (parse_qs(url.query).get("note", [""])[0] or "").strip()[:500]
            if action in SETTLE and note:
                line["note"] = note
            with open(os.path.join(podium_dir(root), "requests.jsonl"), "a") as f:
                f.write(json.dumps(line) + "\n")
            self.reply(202, {"queued": line})

        def do_DELETE(self):
            if self.path.startswith("/handoff/"):
                return self.handoff(self.path[len("/handoff/"):], take=False)
            self.reply(404, {"error": "unknown action"})

        def handoff(self, sid, take):
            _, active = load_run(root)
            story = next((s for s in (active or {}).get("stories", []) if s.get("id") == sid), None)
            if not story or (take and story.get("status") != "todo"):
                return self.reply(404, {"error": "no story to hand off" if take else "unknown id"})
            path, key = os.path.join(podium_dir(root), "handoffs.json"), f"{active['id']}/{sid}"
            taken = handoffs(root)
            if take:
                taken[key] = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            else:
                taken.pop(key, None)
            with open(path + ".tmp", "w") as f:
                json.dump(taken, f, indent=1)
            os.replace(path + ".tmp", path)
            if not take:
                return self.reply(200, {"released": key})
            self.text(story_prompt(root, active, story))

        def text(self, text):
            data = text.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def prompt(self, action, id_):
            milestones, active = load_run(root)
            if action == "plan" and id_ in {m.get("id") for m in milestones}:
                text = f"/{SKILL} {id_}\n"
            elif action == "assign" and active and id_ in {s.get("id") for s in active.get("stories", [])}:
                text = story_prompt(root, active, next(s for s in active["stories"] if s.get("id") == id_))
            else:
                return self.reply(404, {"error": "unknown id"})
            self.text(text)

        def podium(self):
            try:
                with open(os.path.join(podium_dir(root), "podium.json")) as f:
                    return json.load(f)
            except (OSError, ValueError):
                return {}

        def toggle(self, mode, until):
            """Override the hours until `until` (HH:MM, the next one) or the next change of hours; `auto` clears it."""
            path = os.path.join(podium_dir(root), "human.json")
            if mode == "auto":
                if os.path.exists(path):
                    os.remove(path)
                return self.reply(200, availability(root, self.podium()))
            if mode not in ("available", "unavailable"):
                return self.reply(404, {"error": "unknown mode"})
            now = datetime.now()
            if until:
                if not re.fullmatch(r"\d\d:\d\d", until):
                    return self.reply(400, {"error": "until is HH:MM"})
                end = datetime.combine(now.date(), datetime.strptime(until, "%H:%M").time())
                end += timedelta(days=end <= now)
            else:
                hours = {**HOURS, **((self.podium().get("human") or {}).get("hours") or {})}
                end = next_change(hours, now) or now + timedelta(days=1)
            with open(path + ".tmp", "w") as f:
                json.dump({"mode": mode, "until": end.astimezone().isoformat(timespec="minutes"),
                           "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}, f)
            os.replace(path + ".tmp", path)
            self.reply(200, availability(root, self.podium()))

        def link_asana(self, epic, link):
            """POST /asana[/<epic>]?url=<Asana link>: queue a link for the orchestrator to map
            (an epic id links that epic to a task; none links a project or a task as a new epic)."""
            if not ASANA_URL.match(link):
                return self.reply(400, {"error": "not an Asana link"})
            if epic is not None:
                try:
                    with open(os.path.join(podium_dir(root), "podium.json")) as f:
                        epics = {e.get("id") for e in json.load(f).get("epics", [])}
                except (OSError, ValueError):
                    epics = set()
                if not STORY_ID.match(epic) or epic not in epics:
                    return self.reply(404, {"error": "unknown epic"})
            line = {"action": "asana", "story": epic, "note": link,
                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            with open(os.path.join(podium_dir(root), "requests.jsonl"), "a") as f:
                f.write(json.dumps(line) + "\n")
            self.reply(202, {"queued": line})

        def asana_done(self, mid, choice):
            """POST /asana-done/<milestone>?choice=<drop|keep>: the user's answer for a milestone
            completed in Asana but not landed here (skip building it, or keep it)."""
            milestones, _ = load_run(root)
            if choice not in ("drop", "keep") or mid not in {m.get("id") for m in milestones}:
                return self.reply(404, {"error": "unknown milestone or choice"})
            line = {"action": "asana-done", "story": mid, "note": choice,
                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            with open(os.path.join(podium_dir(root), "requests.jsonl"), "a") as f:
                f.write(json.dumps(line) + "\n")
            self.reply(202, {"queued": line})

        def known_ids(self, action):
            """plan → milestone ids; assign → story ids of the active milestone; confirm and
            reverse → the indexes of the open assumptions."""
            if action in SETTLE:
                try:
                    with open(os.path.join(podium_dir(root), "podium.json")) as f:
                        assumed = json.load(f).get("assumptions") or []
                except (OSError, ValueError):
                    return set()
                return {str(i) for i, a in enumerate(assumed) if a.get("status") == "open"}
            milestones, active = load_run(root)
            if action == "plan":
                return {m.get("id") for m in milestones}
            return {s.get("id") for s in (active or {}).get("stories", [])}

        def empty(self, body):
            data = json.dumps(body).encode() if isinstance(body, dict) else body.encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json" if isinstance(body, dict) else "text/plain")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def reply(self, code, body):
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def free_port(start):
    for port in range(start, start + 20):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    sys.exit(f"no free port in {start}-{start + 19}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=".deep-plan")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--idle", type=float, default=60, help="minutes without activity before stopping; 0 = never")
    ap.add_argument("--detach", action="store_true", help="print the URL, then keep serving in the background")
    ap.add_argument("--git-every", type=float, default=5, help="minutes between fetches for GET /git; 0 = never")
    args = ap.parse_args()
    root = os.path.abspath(args.dir)
    port = free_port(args.port)
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(root))
    print(f"http://127.0.0.1:{port}/", flush=True)
    if args.detach:
        if os.fork():
            os._exit(0)  # the port is bound; the child serves it
        os.setsid()
        log = open(os.path.join(podium_dir(root), "server.log"), "a")
        os.dup2(log.fileno(), sys.stdout.fileno())
        os.dup2(log.fileno(), sys.stderr.fileno())
        os.dup2(os.open(os.devnull, os.O_RDONLY), sys.stdin.fileno())
        print(f"{datetime.now():%H:%M} serving http://127.0.0.1:{port}/", flush=True)
    if args.git_every > 0:
        threading.Thread(target=watch_git, args=(root, args.git_every), daemon=True).start()
    if args.idle > 0:
        threading.Thread(target=stop_when_idle, args=(server, root, args.idle), daemon=True).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
