#!/usr/bin/env python3
"""Read and change `podium.json` without loading it into the agent's context.

Every write is atomic (temp file, then rename) and stamps `updatedAt`.
Git commands run in the repo, the run directory's parent.

TARGETS
    .                  the project (top level)
    epic:<id>          an epic
    milestone:<id>     a milestone; `milestone:` alone is the active one
    <story>            a story of the active milestone
    <milestone>/<story>

COMMANDS
    status [--all] [--milestone ID]
        Compact view: active milestone, needsYou, each epic's milestone counts,
        and the active (or named) milestone's stories with the ready ones.
        --all lists every milestone.
    get <target>
        The target as compact JSON (a milestone without its stories).
    set <target> [key=value ...] [--event TYPE [key=value ...]]
        value is JSON when it parses, else a string; `now` is the current ISO
        time, `@file` reads JSON from a file. Dotted keys reach into objects
        (agent.id=x). key+=value appends to a list or adds to a number.
        A story set to status=failed blocks every story that depends on it,
        directly or through others. --event appends one events.jsonl line
        with `at`, `milestone` and `story` filled in from the target.
    ready
        The active milestone's ready story ids, space-separated.
    commits <git log args> [--into <target>] [--no-stats]
        Each non-merge commit the args select (a range, or --no-walk <sha>...),
        oldest first, as {sha, subject, plus, minus, at}. --into writes them
        to that target's `commits` and prints a one-line summary instead.
        --no-stats leaves out plus and minus.
    merge <story>
        Merge story/<id> into the active milestone's branch (--no-ff) in the
        repo checkout, then run the milestone's contract (quality.contract[].cmd)
        to .deep-plan/contract.log. Prints one of:
          MERGED <id> <n> commits; ready: <ids>   story done, commits recorded
          CONFLICT <id> <n>                        merge aborted; n = conflicts so far
          RED <id> <cmd> + the log's last 40 lines merge undone (reset --hard ORIG_HEAD)
    backfill
        Rebuild the planned, commit and landed lines of events.jsonl from the
        milestones' commits, brief dates and landedSha, keep every other line,
        and sort by time.

    python3 podium.py [--dir .deep-plan] <command> ...
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

NOW = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
UTC = lambda epoch: datetime.fromtimestamp(int(epoch), timezone.utc).isoformat()
GENERATED = {"planned", "commit", "landed"}


class Podium:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.path = os.path.join(self.root, "podium.json")
        self.repo = os.path.dirname(self.root)
        try:
            with open(self.path) as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}

    def save(self):
        self.data["updatedAt"] = NOW()
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, self.path)

    def event(self, type_, milestone=None, story=None, **fields):
        line = {"at": fields.pop("at", None) or NOW(), "type": type_, **fields}
        if milestone:
            line["milestone"] = milestone
        if story:
            line["story"] = story
        with open(os.path.join(self.root, "events.jsonl"), "a") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

    # --- lookup -------------------------------------------------------------
    def epics(self):
        return self.data.get("epics", [])

    def milestones(self):
        return [m for e in self.epics() for m in e.get("milestones", [])]

    def milestone(self, mid=None):
        mid = mid or (self.data.get("active") or {}).get("milestone")
        m = next((m for m in self.milestones() if m.get("id") == mid), None)
        if not m:
            sys.exit(f"no milestone {mid!r}" if mid else "no active milestone")
        return m

    def story(self, sid, mid=None):
        m = self.milestone(mid)
        s = next((s for s in m.get("stories", []) if s.get("id") == sid), None)
        if not s:
            sys.exit(f"no story {sid!r} in {m['id']}")
        return m, s

    def resolve(self, target):
        """(object, milestone id, story id) for a target."""
        if target == ".":
            return self.data, (self.data.get("active") or {}).get("milestone"), None
        if target.startswith("epic:"):
            e = next((e for e in self.epics() if e.get("id") == target[5:]), None)
            if not e:
                sys.exit(f"no epic {target[5:]!r}")
            return e, None, None
        if target.startswith("milestone:"):
            m = self.milestone(target[10:] or None)
            return m, m["id"], None
        mid, _, sid = target.rpartition("/")
        m, s = self.story(sid, mid or None)
        return s, m["id"], s["id"]

    def ready(self, m):
        done = {s["id"] for s in m.get("stories", []) if s.get("status") == "done"}
        return [s["id"] for s in m.get("stories", [])
                if s.get("status") == "todo" and set(s.get("deps", []) + s.get("overlapAfter", [])) <= done]

    def git(self, *args, check=True):
        r = subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True)
        if check and r.returncode:
            sys.exit(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r


# --- values -------------------------------------------------------------------
def parse_value(raw):
    if raw == "now":
        return NOW()
    if raw.startswith("@"):
        with open(raw[1:]) as f:
            return json.load(f)
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def assign(obj, item):
    key, eq, raw = item.partition("=")
    if not eq:
        sys.exit(f"expected key=value, got {item!r}")
    op = "+=" if key.endswith("+") else "="
    key = key.rstrip("+")
    *path, last = key.split(".")
    for k in path:
        obj = obj.setdefault(k, {})
    value = parse_value(raw)
    if op == "+=":
        cur = obj.get(last)
        if isinstance(cur, list) or cur is None and not isinstance(value, (int, float)):
            obj.setdefault(last, []).append(value)
        else:
            obj[last] = (cur or 0) + value
    else:
        obj[last] = value


def pairs(items):
    out = {}
    for item in items:
        assign(out, item)
    return out


# --- commands -----------------------------------------------------------------
def cmd_status(p, args):
    all_ = "--all" in args
    named = args[args.index("--milestone") + 1] if "--milestone" in args else None
    d = p.data
    act = d.get("active") or {}
    print(f"{(d.get('project') or {}).get('title', '?')} · active {act.get('epic', '-')}/{act.get('milestone', '-')}"
          f" · buildAll {d.get('buildAll', False)} · dispatcher {d.get('dispatcher', '-')}")
    if d.get("needsYou"):
        print(f"needsYou: {json.dumps(d['needsYou'], ensure_ascii=False)}")
    for e in p.epics():
        ms = e.get("milestones", [])
        counts = {}
        for m in ms:
            counts[m.get("status")] = counts.get(m.get("status"), 0) + 1
        print(f"epic {e['id']}: " + ", ".join(f"{n} {s}" for s, n in counts.items()))
        if all_:
            for m in ms:
                print(f"  {m['id']} {m.get('status')} {m.get('phase', '')} {m.get('title', '')}"
                      f" ({len(m.get('stories', []))} stories)")
    mid = named or act.get("milestone")
    if not mid:
        return
    m = p.milestone(mid)
    print(f"\n{m['id']} {m.get('title', '')} · {m.get('status')} · phase {m.get('phase')} · branch {m.get('branch', '-')}")
    for s in m.get("stories", []):
        extra = [f"deps {','.join(s['deps'])}" if s.get("deps") else "",
                 f"after {','.join(s['overlapAfter'])}" if s.get("overlapAfter") else "",
                 f"att {s['attempts']}" if s.get("attempts") else "",
                 f"failure: {s['failure']}" if s.get("failure") else ""]
        print(f"  {s['id']:<5} {s.get('status', '?'):<8} " + " · ".join(x for x in extra if x))
    print(f"ready: {' '.join(p.ready(m)) or '-'}")


def cmd_get(p, args):
    obj, _, _ = p.resolve(args[0])
    if "stories" in obj:
        obj = {**obj, "stories": f"<{len(obj['stories'])} stories>"}
    if "epics" in obj:
        obj = {**obj, "epics": [e["id"] for e in obj["epics"]]}
    print(json.dumps(obj, ensure_ascii=False))


def cascade_block(m, failed):
    blocked, frontier = [], {failed}
    while frontier:
        nxt = {s["id"] for s in m.get("stories", [])
               if set(s.get("deps", [])) & frontier and s.get("status") in ("todo", "blocked") and s["id"] not in blocked}
        blocked += sorted(nxt)
        frontier = nxt
    for s in m.get("stories", []):
        if s["id"] in blocked:
            s["status"] = "blocked"
    return blocked


def cmd_set(p, args):
    target, rest = args[0], args[1:]
    ev = rest.index("--event") if "--event" in rest else len(rest)
    obj, mid, sid = p.resolve(target)
    for item in rest[:ev]:
        assign(obj, item)
    if sid and obj.get("status") == "failed":
        blocked = cascade_block(p.milestone(mid), sid)
        if blocked:
            print(f"blocked: {' '.join(blocked)}")
    if rest[ev:]:
        p.event(rest[ev + 1], mid, sid, **pairs(rest[ev + 2:]))
    p.save()


def cmd_ready(p, _):
    print(" ".join(p.ready(p.milestone())))


def git_commits(p, rng, stats=True):
    rng = [rng] if isinstance(rng, str) else rng
    fmt = "--format=\x1e%H\x1f%s\x1f%ct"
    out = p.git("log", "--reverse", "--no-merges", fmt, *(["--shortstat"] if stats else []), *rng).stdout
    commits = []
    for block in out.split("\x1e")[1:]:
        head, _, tail = block.partition("\n")
        sha, subject, at = head.split("\x1f")
        c = {"sha": sha[:10], "subject": subject, "at": UTC(at)}
        if stats:
            words = tail.replace(",", "").split()
            c["plus"] = next((int(words[i - 1]) for i, w in enumerate(words) if w.startswith("insertion")), 0)
            c["minus"] = next((int(words[i - 1]) for i, w in enumerate(words) if w.startswith("deletion")), 0)
        commits.append(c)
    return commits


def cmd_commits(p, args):
    into = args[args.index("--into") + 1] if "--into" in args else None
    rng = [a for a in args if a not in ("--into", into, "--no-stats")]
    commits = git_commits(p, rng, "--no-stats" not in args)
    if into:
        obj, _, _ = p.resolve(into)
        obj["commits"] = [{k: v for k, v in c.items() if k != "at"} for c in commits]
        p.save()
        print(f"{len(commits)} commits into {into}")
    else:
        for c in commits:
            print(json.dumps(c, ensure_ascii=False))


def cmd_merge(p, args):
    m, s = p.story(args[0])
    branch, story_branch = m.get("branch"), f"story/{s['id']}"
    if not branch:
        sys.exit(f"{m['id']} has no branch")
    if p.git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() != branch:
        p.git("switch", branch)
    commits = git_commits(p, f"{branch}..{story_branch}")
    if p.git("merge", "--no-ff", "--no-edit", story_branch, check=False).returncode:
        p.git("merge", "--abort", check=False)
        s["conflicts"] = s.get("conflicts", 0) + 1
        p.event("conflict", m["id"], s["id"])
        p.save()
        print(f"CONFLICT {s['id']} {s['conflicts']}")
        sys.exit(2)
    log = os.path.join(p.root, "contract.log")
    results = []
    open(log, "w").close()
    for c in m.get("quality", {}).get("contract", []):
        with open(log, "a") as f:
            f.write(f"$ {c['cmd']}\n")
            f.flush()
            ok = subprocess.run(c["cmd"], shell=True, cwd=p.repo, stdout=f, stderr=subprocess.STDOUT).returncode == 0
        results.append({"cmd": c["cmd"], "ok": ok, "at": NOW()})
        if not ok:
            p.git("reset", "--hard", "ORIG_HEAD")
            m["quality"]["contract"] = results + m["quality"]["contract"][len(results):]
            p.save()
            with open(log) as f:
                tail = f.read().splitlines()[-40:]
            print(f"RED {s['id']} {c['cmd']}\n" + "\n".join(tail))
            sys.exit(3)
    m.setdefault("quality", {})["contract"] = results
    s.update(status="done", commits=[{k: v for k, v in c.items() if k != "at"} for c in commits], finishedAt=NOW())
    for c in commits:
        p.event("commit", m["id"], s["id"], at=c["at"], sha=c["sha"], subject=c["subject"])
    p.event("merged", m["id"], s["id"], into=branch)
    p.save()
    print(f"MERGED {s['id']} {len(commits)} commits; ready: {' '.join(p.ready(m)) or '-'}")


def cmd_backfill(p, _):
    events_path = os.path.join(p.root, "events.jsonl")
    kept = []
    if os.path.exists(events_path):
        with open(events_path) as f:
            kept = [json.loads(l) for l in f if l.strip()]
        kept = [e for e in kept if e.get("type") not in GENERATED]
    shas = {c["sha"] for m in p.milestones() for s in m.get("stories", []) for c in s.get("commits", [])}
    shas |= {m["landedSha"] for m in p.milestones() if m.get("landedSha")}
    when = {}
    if shas:
        for line in p.git("log", "--no-walk=unsorted", "--format=%H %ct", *shas).stdout.splitlines():
            full, at = line.split()
            for sha in shas:
                if full.startswith(sha):
                    when[sha] = UTC(at)
    new = []
    for m in p.milestones():
        commits = [(c, s["id"]) for s in m.get("stories", []) for c in s.get("commits", [])]
        if not commits:
            continue
        times = [when[c["sha"]] for c, _ in commits if c["sha"] in when]
        brief = m.get("brief")
        if brief:
            added = p.git("log", "--diff-filter=A", "--format=%ct", "--", os.path.join(p.root, brief), check=False)
            times += [UTC(t) for t in added.stdout.split()[-1:]]
        if times:
            new.append({"at": min(times), "type": "planned", "milestone": m["id"]})
        seen = set()
        for c, sid in commits:
            if c["sha"] in seen or c["sha"] == m.get("landedSha") or c["sha"] not in when:
                continue
            seen.add(c["sha"])
            new.append({"at": when[c["sha"]], "type": "commit", "milestone": m["id"], "story": sid,
                        "sha": c["sha"], "subject": c["subject"]})
        if m.get("landedSha") in when:
            subject = p.git("show", "-s", "--format=%s", m["landedSha"]).stdout.strip()
            new.append({"at": when[m["landedSha"]], "type": "landed", "milestone": m["id"],
                        "sha": m["landedSha"], "subject": subject})
    rows = sorted(kept + new, key=lambda e: e.get("at", ""))
    with open(events_path + ".tmp", "w") as f:
        f.writelines(json.dumps(e, ensure_ascii=False) + "\n" for e in rows)
    os.replace(events_path + ".tmp", events_path)
    missing = len(shas) - len(when)
    print(f"{len(new)} generated + {len(kept)} kept = {len(rows)} events" + (f"; {missing} shas not in git" if missing else ""))


COMMANDS = {"status": cmd_status, "get": cmd_get, "set": cmd_set, "ready": cmd_ready,
            "commits": cmd_commits, "merge": cmd_merge, "backfill": cmd_backfill}


def main(argv):
    root = ".deep-plan"
    if argv[:1] == ["--dir"]:
        root, argv = argv[1], argv[2:]
    if not argv or argv[0] not in COMMANDS:
        sys.exit(__doc__)
    COMMANDS[argv[0]](Podium(root), argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
