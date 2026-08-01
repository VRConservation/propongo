# Team Collaboration with GitHub

Propongo saves each proposal as a single JSON file under `data/proposals/`. Because these files are plain text, a team can use **git and GitHub** as a shared, versioned workspace: everyone edits proposals on their own machine, then syncs with the rest of the team. This is not live (real-time) collaboration, but it gives you change history, conflict tracking, and a single source of truth.

This guide assumes you are starting from scratch: no GitHub account, no git, and no editor installed.

## How it works

- Each proposal lives in its own file, e.g. `data/proposals/abcd1234.json`.
- Git tracks every change to those files, so you can always see who changed what and when, and restore any past version.
- Team members `pull` the latest files before working and `push` their own changes when done.
- Because Propongo saves as you work, your files are always in sync with your last edit — git just records the checkpoints.

!!! warning "Not real-time"
    Two people editing the **same proposal at the same time** will eventually hit a merge conflict when they push. The simple rule is: one person owns a proposal at a time. See [Team workflow](#team-workflow) below.

## 1. Create a GitHub account

1. Go to https://github.com and click **Sign up**.
2. Enter an email, a password, and a username, then follow the verification steps.

## 2. Install git

**Mac:**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install git
```

**Windows:** install Git for Windows from https://git-scm.com/download/win (accept the defaults; it includes Git Bash and Git GUI).

**Tell git who you are** (this labels your commits):
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## 3. Install VS Code

Download from https://code.visualstudio.com and install it. VS Code includes:
- an **integrated terminal**, so you can run Propongo without leaving the editor, and
- a built-in **Source Control** panel for git, so you don't need to type git commands.

## 4. Create a shared repository

Your team needs a repository that everyone can push to. The simplest option is to **fork** the Propongo repository:

1. Go to https://github.com/VRConservation/propongo.
2. Click **Fork** (top-right) → **Create fork**. This copies the repository (including its `data/` folder) to your own account — that becomes your team's shared repo.

!!! tip "Only the owner pushes to GitHub"
    Everyone on the team works with their **own local clone** and pushes to the shared repository. If a teammate isn't a collaborator on the fork, have them fork it too and open a **pull request** instead.

## 5. Clone the repository

1. On your fork's GitHub page, click the green **Code** button and copy the URL (e.g. `https://github.com/yourname/propongo.git`).
2. In VS Code: press `Ctrl+Shift+P` (`Cmd+Shift+P` on Mac) → type **Git: Clone** → paste the URL → choose where to save it.
3. Open the cloned folder: **File → Open Folder**, then select the `propongo` folder.

## 6. Install and run Propongo

Install it locally (see [Installation](../installation.md) for all options):

```bash
cd propongo
pip install -e .
propongo
```

Open [http://localhost:5000](http://localhost:5000) and create a proposal as usual. The proposal is saved immediately as a JSON file in `data/proposals/`.

!!! info "Running in VS Code"
    Use VS Code's integrated terminal (**View → Terminal**) for the commands above, so your editor and the running app stay in one window.

## 7. Example session (a team of two)

Ana and Ben both cloned the shared repository. Here is a complete round-trip.

### Ana creates a proposal

1. Ana runs `propongo` and creates **"Riparian Restoration – Smith Creek"**.
2. Propongo writes `data/proposals/8f2a…e41.json` (the exact id is random).
3. In VS Code, Ana opens the **Source Control** panel (icon on the left, or `Ctrl+Shift+G`). The new file shows under **Changes**.
4. She clicks the **+** on the file to stage it, types a message like `Add Smith Creek proposal`, and clicks **Commit**, then **Sync Changes** (or the push icon) to send it to GitHub.

### Ben picks it up

1. Ben opens his clone in VS Code and clicks **Sync Changes** (or runs `git pull`).
2. The proposal file appears in his `data/proposals/` folder.
3. Ben runs `propongo` and edits the Budget tab.
4. Ben commits and pushes — same Source Control steps. Ana's next `git pull` brings his edits in.

Git now has a complete history of the proposal: every commit shows who changed which file and when, and any version can be restored.

## 8. Branch-based workflow (optional but recommended)

For larger teams or several proposals in flight, work on a **branch per proposal** so work doesn't collide on `main`:

```bash
git checkout -b proposal/smith-creek
```

- Do all edits to that proposal on the branch and push it: `git push -u origin proposal/smith-creek`.
- When the proposal is finished, open a **pull request** on GitHub so a teammate can review, then merge it into `main`.

## 9. Resolving conflicts

If two people edit the same file and both push, git will refuse the second push. To fix it, pull the latest and merge:

```bash
git pull --rebase
```

If the same lines changed on both sides, git reports a **conflict** and marks it in the file. In VS Code, the file shows merge markers (e.g. `<<<<<<<` and `>>>>>>>`); click **Accept Current** / **Accept Incoming** / **Accept Both**, save, then stage and commit. This is exactly why the "one owner per proposal" rule keeps life simple.

## 10. Team workflow (recommended conventions)

- **One owner per proposal at a time.** Write the owner's name in the proposal title or keep a short `TEAM.md` list. This eliminates most conflicts.
- **Pull before you start, push when you finish.** Never leave unsynced changes behind.
- **Commit in natural chunks**, not per keystroke. A message like `Draft budget for Smith Creek` is better than `Update proposal`.
- **Keep exports out of git.** Generated PDF/HTML exports in `data/exports/` are re-creatable; the included `.gitignore` already excludes them. Track the source JSON, not the artifacts.
- **Use templates.** Save a finished proposal as a [template](../examples/templates.md) so the team shares a consistent starting point.

## 11. Optional: one-command sync script

A helper script is included at `scripts/propongo-sync.sh`. It pulls the latest work, starts Propongo, and on exit commits and pushes your changes — all in one command:

```bash
# work on a specific proposal branch
scripts/propongo-sync.sh proposal/smith-creek

# or just sync whatever branch you are on
scripts/propongo-sync.sh
```

The script uses `data/` in the repository you are working from. If your data lives elsewhere, point it there:

```bash
PROPONGO_REPO_DIR=/path/to/team-repo scripts/propongo-sync.sh
```

## Next Steps

- Once a proposal is funded, use the [Project Tracker](../examples/tracker.md) to manage progress and spending — the tracker data is saved the same way, so it syncs through git too.
