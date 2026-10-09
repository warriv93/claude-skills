#!/usr/bin/env python3
"""orchestrate-plan Podium server.

Serves `podium.html` (next to this file) plus the run directory (default
`.deep-plan/`) on 127.0.0.1, and turns the
Podium's buttons into lines in `requests.jsonl`, which the orchestrator
watches. The browser only ever sends an action and a story id; prompts are
built by the orchestrator from the story brief.

    python3 server.py [--dir .deep-plan] [--port 8765]
"""
import argparse
import json
import os
import re
import socket
import sys
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from podium import HOURS, availability, next_change  # one reading of the user's availability

STORY_ID = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
ACTIONS = {"assign", "plan", "build-all", "stop"}  # assign and plan take an id


def load_run(root):
    """The run's milestones (across every epic) and the active milestone, from podium.json or an older epic.json."""
    for name in ("podium.json", "epic.json"):
        try:
            with open(os.path.join(root, name)) as f:
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


def make_handler(root):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=root, **kw)

        def log_message(self, *_):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def do_GET(self):
            if self.path == "/info":
                return self.reply(200, {"runDir": root, "repoDir": os.path.dirname(root)})
            if self.path == "/human":
                return self.reply(200, availability(root, self.podium()))
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

        def do_POST(self):
            url = urlparse(self.path)
            if url.path.startswith("/human/"):
                return self.toggle(url.path[len("/human/"):], parse_qs(url.query).get("until", [None])[0])
            parts = [p for p in self.path.split("/") if p]
            action = parts[0] if parts else ""
            story = parts[1] if len(parts) > 1 else None
            if action not in ACTIONS or (action in ("assign", "plan")) != (story is not None):
                return self.reply(404, {"error": "unknown action"})
            if story is not None:
                if not STORY_ID.match(story) or story not in self.known_ids(action):
                    return self.reply(404, {"error": "unknown id"})
            line = {"action": action, "story": story,
                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            with open(os.path.join(root, "requests.jsonl"), "a") as f:
                f.write(json.dumps(line) + "\n")
            self.reply(202, {"queued": line})

        def podium(self):
            try:
                with open(os.path.join(root, "podium.json")) as f:
                    return json.load(f)
            except (OSError, ValueError):
                return {}

        def toggle(self, mode, until):
            """Override the hours until `until` (HH:MM, the next one) or the next change of hours; `auto` clears it."""
            path = os.path.join(root, "human.json")
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

        def known_ids(self, action):
            """plan → milestone ids; assign → story ids of the active milestone."""
            milestones, active = load_run(root)
            if action == "plan":
                return {m.get("id") for m in milestones}
            return {s.get("id") for s in (active or {}).get("stories", [])}

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
    args = ap.parse_args()
    root = os.path.abspath(args.dir)
    port = free_port(args.port)
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(root))
    print(f"http://127.0.0.1:{port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
