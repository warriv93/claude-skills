# Phase 3 — Sequential Inline Execution & Quality Gates

Execute `tasks.md` **slice by slice sequentially inline** in the main window:

- **Slice-Isolated Task Loading:** Extract and load ONLY the specific task lines for the current slice from `tasks.md` into memory. Do not load the entire `tasks.md` file on every slice.
- Execute each slice using `/tdd` discipline: failing tests first (RED), minimum implementation (GREEN), refactor (IMPROVE).
- **One passing slice = one commit** on feature branch with conventional commit message. Never commit red.
- **Update `.deep-plan/state.md` with 1 line per slice** (`- [x] <slice> — <sha> — PASS`). Keep `state.md` strictly under 60 lines total.
- **Mid-Phase Compaction:** Run `/compact` every 3–4 completed slices (or whenever context window exceeds ~50k tokens) during Phase 3 inline execution.

## Phase 3 Code Quality Gate

All slices committed and green ≠ done. Record current commit SHA as `<phase-3-end-sha>`.

1. **Run Matt Pocock's dual-axis `code-review` skill** (Standards + Spec axes) using subagents on the **Strong Model** (`opus`/`pro`).
2. **Subagent Protocol & Prompt Cache Alignment:**
   - Place static rules/standards at the TOP prefix of subagent prompts; place diffs at the bottom for 90%+ prompt cache hits.
   - Mandate **`NO_PREAMBLE`**: subagents return raw findings markdown table only, zero conversational intro or concluding remarks.
3. Fixed point = branch point (`git merge-base main HEAD`). Subagents run `git diff --stat` first to identify modified files before fetching full line diffs.
4. **Fix what it finds:** standards violations, missing spec items, scope creep, code smells. Refactor under green tests (`/tdd` IMPROVE); commit as `refactor:` / `fix:`.
   - **Write detailed finding notes and explanations of skipped findings to `.deep-plan/state-findings.md`**.
   - In `state.md`, record only high-level status line (`Quality gate: PASS with N findings in state-findings.md`).
5. Re-run verification contract. Phase 3 closes only when green after fixes. Record `<phase-3-end-sha>`.
6. Update `.deep-plan/state.md` and execute `/compact` before Phase 4.
