# Phase 2 — Break the milestone into stories

1. **One story per user-story slice** of `tasks.md`, ids `S1`, `S2`, … in task order: `title`, a one-line `summary`, `files` (every path its tasks touch).
2. **Dependencies:** a story depends on another only when it needs that story's code — an interface, a migration, a module. Write each one into `deps`. The graph is acyclic.
3. **File overlap:** two stories with no dependency path between them that share a file → the later id gets `overlapAfter: [<earlier id>]`, so they land in different waves.
4. **Model:** `opus` for correctness-critical stories (money, dates and time zones, concurrency, auth, migrations, core algorithms), `sonnet` for the rest.
5. **Write each brief** to `podium/stories/<milestone>/<id>.md`. The brief is self-contained: the story's agent reads it and the files it names, nothing else.

   ```markdown
   # <id> · <title>
   ## Goal
   ## Acceptance        ← this story's task lines from tasks.md, as checkboxes; tests first
   ## Files in scope
   ## Context           ← the architecture.md interfaces and seams it builds on, quoted
   ## Contract          ← the pinned commands from the ledger
   ## Done when         ← one commit on story/<id> with trailer `Story: <id>`, contract green, `COMMITTED <sha>` logged
   ```

6. **Publish:** write the stories (`status: "todo"`, `attempts: 0`, `brief`, `model`) to a file, then `podium.py set milestone: stories=@<file> phase=build quality.contract=<the ledger's contract commands as [{"cmd"}]> --event phase phase=build`. `merge` runs that contract.
7. **Hand over:** start the watcher (SKILL.md, Podium) and tell the user in one message: the Podium link, N stories in M waves, and that they can assign stories one by one or press Build all. End the turn; the watcher wakes you.

Done when every story in `tasks.md` has a brief and a `podium.json` entry, the graph is acyclic with no shared file inside one wave, and the user has the link.
