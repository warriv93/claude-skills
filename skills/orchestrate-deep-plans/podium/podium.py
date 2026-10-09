#!/usr/bin/env python3
"""Read and change `podium.json` without loading it into the agent's context.

Every write is atomic (temp file, then rename) and stamps `updatedAt`.
The files live in the run dir's `podium/` folder (podium_dir).
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
        (agent.id=x), and a number into a list (assumptions.0.status=x).
        key+=value appends to a list or adds to a number.
        A story set to status=failed blocks every story that depends on it,
        directly or through others. --event appends one events.jsonl line
        with `at`, `milestone` and `story` filled in from the target.
    ready
        The active milestone's ready story ids, space-separated. A story the
        user handed off to a session of their own (handoffs.json) is never ready.
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
    human
        Whether the user is available or unavailable, until when, and why:
        their hours (podium.json human.hours, default Mon-Fri 07:00-17:00
        local time) or the Podium's toggle (human.json, written by the server,
        holding until the next change of hours). Change it through the Podium:
        its toggle, or `curl -s -X POST <podium>/human/<available|unavailable|auto>`
        (`?until=HH:MM` for another end).
    assume <question> <choice> <why> [--story ID]
        Record an assumption made while the user is unavailable: appends
        {at, milestone, story, question, choice, why, status: open} to the
        project's assumptions and an `assumed` event.
    assumptions
        The open assumptions, numbered by their index in the list
        (settle one with `set . assumptions.<n>.status=confirmed|reversed`).
    prs [<milestone>]
        Refresh the state of the milestone's `pr` (every milestone's when none
        is named) with `gh pr view`. Merged PRs are final and skipped. One line
        per PR: `<milestone> #<n> <state> [(was <old>)]`, or `error: <message>`.
        A changed state is written back with a `pr` event. Exits 1 on any error.
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
from datetime import datetime, time, timedelta, timezone

NOW = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
UTC = lambda epoch: datetime.fromtimestamp(int(epoch), timezone.utc).isoformat()
GENERATED = {"planned", "commit", "landed"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HOURS = {"days": "Mon-Fri", "from": "07:00", "to": "17:00"}


def podium_dir(root):
    """The orchestrator's own folder in the run dir, `<run dir>/podium/`; a run begun before it keeps its files in
    the run dir itself (podium.json at the top) and is read there until they are moved."""
    d = os.path.join(root, "podium")
    legacy = not os.path.exists(os.path.join(d, "podium.json")) and os.path.exists(os.path.join(root, "podium.json"))
    return root if legacy else d


class Podium:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.dir = podium_dir(self.root)
        self.path = os.path.join(self.dir, "podium.json")
        self.repo = os.path.dirname(self.root)
        try:
            with open(self.path) as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}

    def save(self):
        self.data["updatedAt"] = NOW()
        os.makedirs(self.dir, exist_ok=True)
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
        with open(os.path.join(self.dir, "events.jsonl"), "a") as f:
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

    def handed_off(self, m):
        """Ids of m's stories the user took to a session of their own (handoffs.json, the Podium's copy button)."""
        try:
            with open(os.path.join(self.dir, "handoffs.json")) as f:
                return {k.split("/", 1)[1] for k in json.load(f) if k.startswith(m["id"] + "/")}
        except (OSError, ValueError):
            return set()

    def ready(self, m):
        done = {s["id"] for s in m.get("stories", []) if s.get("status") == "done"}
        away = self.handed_off(m)
        return [s["id"] for s in m.get("stories", [])
                if s.get("status") == "todo" and s["id"] not in away
                and set(s.get("deps", []) + s.get("overlapAfter", [])) <= done]

    def git(self, *args, check=True):
        r = subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True)
        if check and r.returncode:
            sys.exit(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r


# --- the human ----------------------------------------------------------------
def day_set(spec):
    """'Mon-Fri' or 'Mon,Wed,Fri-Sun' → weekday numbers (Mon = 0)."""
    out = set()
    for part in spec.split(","):
        a, _, b = part.strip().partition("-")
        i, j = DAYS.index(a), DAYS.index(b or a)
        out |= {d % 7 for d in range(i, j + 1 if j >= i else j + 8)}
    return out


def in_hours(hours, t):
    return t.weekday() in day_set(hours["days"]) and hours["from"] <= t.strftime("%H:%M") < hours["to"]


def next_change(hours, t):
    """The first local time after t at which the hours start or end, or None."""
    now = in_hours(hours, t)
    for d in range(8):
        day = (t + timedelta(days=d)).date()
        for hm in sorted((hours["from"], hours["to"])):
            c = datetime.combine(day, time.fromisoformat(hm))
            if c > t and in_hours(hours, c) != now:
                return c
    return None


def local(iso):
    return datetime.fromisoformat(iso).astimezone().replace(tzinfo=None)


def availability(root, data, t=None):
    """{mode, until, source, hours}: mode `available` or `unavailable`, until a local ISO time or None,
    source `toggle` while human.json's override holds, else `hours`. Times are naive local."""
    t = t or datetime.now()
    hours = {**HOURS, **((data.get("human") or {}).get("hours") or {})}
    try:
        with open(os.path.join(podium_dir(root), "human.json")) as f:
            o = json.load(f)
    except (OSError, ValueError):
        o = None
    if o and o.get("mode") in ("available", "unavailable") and o.get("until") and local(o["until"]) > t:
        return {"mode": o["mode"], "until": local(o["until"]).isoformat(timespec="minutes"), "source": "toggle", "hours": hours}
    nxt = next_change(hours, t)
    return {"mode": "available" if in_hours(hours, t) else "unavailable",
            "until": nxt and nxt.isoformat(timespec="minutes"), "source": "hours", "hours": hours}


def human_line(a):
    until = datetime.fromisoformat(a["until"]).strftime("%a %H:%M") if a["until"] else "further notice"
    h = a["hours"]
    why = "Podium toggle; " if a["source"] == "toggle" else ""
    return f"{a['mode']} until {until} ({why}hours {h['days']} {h['from']}-{h['to']})"


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
        obj = obj[int(k)] if isinstance(obj, list) else obj.setdefault(k, {})
    if isinstance(obj, list):
        sys.exit(f"{key}: set a field of the item (key.<n>.field=value)")
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
    print(f"human: {human_line(availability(p.root, d))}")
    if d.get("needsYou"):
        print(f"needsYou: {json.dumps(d['needsYou'], ensure_ascii=False)}")
    open_ = [a for a in d.get("assumptions", []) if a.get("status") == "open"]
    if open_:
        print(f"assumptions: {len(open_)} open")
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
    away = p.handed_off(m)
    for s in m.get("stories", []):
        extra = ["handed off" if s["id"] in away and s.get("status") == "todo" else "",f"deps {','.join(s['deps'])}" if s.get("deps") else "",
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


def cmd_human(p, _):
    print(human_line(availability(p.root, p.data)))


def cmd_assume(p, args):
    story = args[args.index("--story") + 1] if "--story" in args else None
    rest = [a for a in args if a not in ("--story", story)]
    if len(rest) != 3:
        sys.exit("assume <question> <choice> <why> [--story ID]")
    question, choice, why = rest
    mid = (p.data.get("active") or {}).get("milestone")
    a = {"at": NOW(), "milestone": mid, "story": story, "question": question, "choice": choice, "why": why, "status": "open"}
    p.data.setdefault("assumptions", []).append({k: v for k, v in a.items() if v is not None})
    p.event("assumed", mid, story, question=question, choice=choice)
    p.save()
    print(f"assumption {len(p.data['assumptions']) - 1}")


def cmd_assumptions(p, _):
    for i, a in enumerate(p.data.get("assumptions", [])):
        if a.get("status") == "open":
            where = "/".join(x for x in (a.get("milestone"), a.get("story")) if x)
            print(f"{i} [{where}] {a['question']} → {a['choice']} ({a['why']})")


def cmd_prs(p, args):
    errors = changed = 0
    for m in [p.milestone(args[0])] if args else p.milestones():
        pr = m.get("pr")
        if not pr or pr.get("state") == "merged":
            continue
        out = subprocess.run(["gh", "pr", "view", str(pr["number"]), "--json", "state,isDraft,url"],
                             cwd=p.repo, capture_output=True, text=True)
        if out.returncode:
            errors += 1
            print(f"{m['id']} #{pr['number']} error: {(out.stderr.strip().splitlines() or ['gh failed'])[-1]}")
            continue
        got = json.loads(out.stdout)
        state = "draft" if got.get("isDraft") and got["state"] == "OPEN" else got["state"].lower()
        old = pr.get("state")
        pr.update(state=state, url=got.get("url") or pr.get("url"))
        if state != old:
            changed += 1
            p.event("pr", m["id"], number=pr["number"], state=state, was=old, url=pr["url"])
        print(f"{m['id']} #{pr['number']} {state}" + (f" (was {old})" if state != old else ""))
    if changed:
        p.save()
    if errors:
        sys.exit(1)


def cmd_backfill(p, _):
    events_path = os.path.join(p.dir, "events.jsonl")
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
            "commits": cmd_commits, "merge": cmd_merge, "human": cmd_human, "assume": cmd_assume,
            "assumptions": cmd_assumptions, "prs": cmd_prs, "backfill": cmd_backfill}


def main(argv):
    root = ".deep-plan"
    if argv[:1] == ["--dir"]:
        root, argv = argv[1], argv[2:]
    if not argv or argv[0] not in COMMANDS:
        sys.exit(__doc__)
    COMMANDS[argv[0]](Podium(root), argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
