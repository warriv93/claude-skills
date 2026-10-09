# Screenshots of UI changes

Step 5 of `/create-pr`. The goal is that a reviewer sees each changed screen the way a user would, with the change on it.

## 1. Pick the screens

From the diff, list each screen where the change shows up and the state that makes it visible. Changes often sit behind a guard: a feature flag, a role, a config value or a data condition. For each one, note what turns it on. Drop files that change nothing visible, such as a type-only refactor. If nothing is left, record that in the report and skip the rest.

## 2. Get the app running on this branch

An instance that's already running counts only if it serves this checkout and started after HEAD was committed. To check:

1. Find the port's process with `lsof -ti :<port> -sTCP:LISTEN`.
2. Get its working directory with `lsof -a -p <pid> -d cwd` and its start time with `ps -o lstart= -p <pid>`.
3. Compare them with the repo root and `git log -1 --format=%cd`.

If it doesn't count, find the **run recipe**: how this repo boots in dev, where it serves, and how to log in. Look in this order, taking the first that answers:

1. A project skill or `/run` that covers launching the app.
2. The README, `CONTRIBUTING.md` and `docs/`.
3. `.claude/launch.json`, `.run/` and `.vscode/launch.json`.
4. The `dev`/`start` scripts in `package.json`, a `Makefile`, `docker-compose*`.

For login and data, prefer what the repo already has: dev users in its docs or seed data, or an existing Playwright/e2e setup with fake-auth fixtures and API mocks. With such a setup, write a throwaway spec that uses those fixtures and calls `page.screenshot({ path })` with scratchpad paths, run it through the repo's e2e command, and delete it afterwards. That replaces the MCP capture in section 3, but the read-back check there still applies.

Start the app in the background, logging to a file. Poll its URL until it answers, for at most 10 minutes. If the recipe needs secrets, a VPN or a cluster port-forward you can't set up, or the boot fails, skip the screenshots and name the blocker in the report. Once you're done, stop what you started and leave anything that was already running.

## 3. Capture

Use the Playwright MCP tools:

1. Set the viewport to 1440x900 with `browser_resize`.
2. Navigate to the page and log in.
3. Set up the state from section 1.
4. Take the shot with `browser_take_screenshot`. Give it an absolute scratchpad `filename`, so the PNGs stay out of the working tree, and name each file after the screen and state, like `settings-billing-address.png`.

Prefer an element screenshot of the changed region, together with its surrounding form or table, over a full page. Read each PNG back and retake it until it shows the change. A login page, an error page or an empty state doesn't count.

## 4. Post

```bash
<this skill's folder>/scripts/post-screenshots.sh <repo-root> <png>...
```

The script commits the PNGs to the repo's `pr-screenshots` orphan branch, in a folder named after the PR branch, and pushes it. It prints one markdown image line per file, pinned to that commit, and leaves the working tree, index and current branch alone. Put the lines in the PR's Screenshots section.
