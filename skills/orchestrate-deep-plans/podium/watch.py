#!/usr/bin/env python3
"""The Podium watcher, run by the orchestrator under the Monitor tool.

Prints one line per event the orchestrator must act on:

    REQUEST <action> [<id>]         a Podium button (requests.jsonl)
    PROGRESS <story> <line>         a story agent's COMMITTED or FAILED line (stories/<milestone>/<story>.progress);
                                    the other stages only feed the Podium, so they stay out of the agent's context
    PERMISSION <story> <tool>       a Paseo agent waits for approval   (--paseo)
    PERMISSION-CLEARED <story>      that approval was answered          (--paseo)
    IDLE <story>                    a working story's Paseo agent went idle (--paseo)
    HUMAN <available|unavailable>   the user's availability flipped (hours or the Podium toggle)

It also rewrites watcher.json ({pid, at}) every few seconds, its heartbeat:
the Podium server takes requests only while it is fresh.

    python3 watch.py [--dir .deep-plan] [--paseo /path/to/paseo]
"""
import argparse
import glob
import json
import os
import subprocess
import time

from podium import availability  # one reading of the user's availability
from server import load_run  # one reader for podium.json, shared with the server


def emit(line):
    print(line, flush=True)


def paseo_json(bin_, *args):
    try:
        out = subprocess.run([bin_, *args, "--json"], capture_output=True, text=True, timeout=20)
        return json.loads(out.stdout or "[]")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=".deep-plan")
    ap.add_argument("--paseo")
    args = ap.parse_args()
    root = os.path.abspath(args.dir)

    offsets = {}
    def watched():
        return [os.path.join(root, "requests.jsonl"), *glob.glob(os.path.join(root, "stories", "*", "*.progress"))]

    for path in watched():
        if not os.path.exists(path):
            continue
        offsets[path] = os.path.getsize(path)  # start at the end: only new lines are events

    def human():
        try:
            with open(os.path.join(root, "podium.json")) as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        return availability(root, data)["mode"]

    waiting, idle = set(), set()
    last_paseo = last_human = 0.0
    mode = human()
    last_beat = 0.0
    while True:
        if time.time() - last_beat > 5:
            last_beat = time.time()
            with open(os.path.join(root, "watcher.json.tmp"), "w") as f:
                json.dump({"pid": os.getpid(), "at": last_beat}, f)
            os.replace(os.path.join(root, "watcher.json.tmp"), os.path.join(root, "watcher.json"))

        for path in watched():
            if not os.path.exists(path):
                continue
            with open(path) as f:
                f.seek(offsets.get(path, 0))
                chunk = f.read()
                offsets[path] = f.tell()
            for line in chunk.splitlines():
                if not line.strip():
                    continue
                if path.endswith("requests.jsonl"):
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    emit(f"REQUEST {r.get('action')} {r.get('story') or ''}".rstrip())
                elif line.split()[1:2] in (["COMMITTED"], ["FAILED"]):
                    emit(f"PROGRESS {os.path.basename(path)[:-len('.progress')]} {line}")

        if time.time() - last_human > 15:
            last_human = time.time()
            now_mode = human()
            if now_mode != mode:
                emit(f"HUMAN {now_mode}")
            mode = now_mode

        if args.paseo and time.time() - last_paseo > 10:
            last_paseo = time.time()
            stories = (load_run(root)[1] or {}).get("stories", [])
            by_agent = {s["agent"]["id"]: s for s in stories if s.get("agent", {}).get("backend") == "paseo"}
            now_waiting = {}
            for p in paseo_json(args.paseo, "permit", "ls"):
                s = by_agent.get(p.get("agentId"))
                if s:
                    now_waiting[s["id"]] = p.get("name", "tool")
            for sid, tool in now_waiting.items():
                if sid not in waiting:
                    emit(f"PERMISSION {sid} {tool}")
            for sid in waiting - now_waiting.keys():
                emit(f"PERMISSION-CLEARED {sid}")
            waiting = set(now_waiting)
            working = {s["agent"]["id"]: s["id"] for s in stories if s.get("status") == "working" and s.get("agent", {}).get("backend") == "paseo"}
            now_idle = {working[a["id"]] for a in paseo_json(args.paseo, "ls", "-g") if a.get("id") in working and a.get("status") == "idle"}
            for sid in now_idle - idle:
                emit(f"IDLE {sid}")
            idle = now_idle

        time.sleep(1)


if __name__ == "__main__":
    main()
