---
name: newchat
description: Close out this chat and prepare a verified handoff for the next one.
argument-hint: "[quiz] [notes for the next session]"
disable-model-invocation: true
---

# Close out this chat

Arguments: $ARGUMENTS

If the first word is `quiz`, run the quiz step. Treat any other text as the user's notes or preferred goal for the next session.

The goal is that the next chat knows where we are, how we know it, and where we want to be when that session ends. Follow CLAUDE.md throughout.

## Limits
- Don't run `git add`, `git commit`, `git push`, or any command that changes git state. The user commits.
- Don't write, fix, or finish project code. Report problems instead.
- Don't connect to Snowflake or run `dbt` or a load. Read-only git commands and offline checks are fine, such as `uv run python -m ingestion.run_dq_cases` when ingestion changed.
- Don't read files that `.claude/settings.json` denies, and never print secrets.
- Don't change dates, budgets, or scope in the docs.
- Before the user replies to the checkpoint in step 3, change no files.

## 1. Inspect
Read the current state instead of relying on the conversation.

**Git:** `git status -sb`, `git diff`, `git diff --cached`, `git log --oneline -15`, and unpushed commits. Read untracked files that look like project work. Note anything that shouldn't be committed: credentials, scratch files, debug prints, half-finished code.

**Memory:** `MEMORY.md` and every file it lists, including `project-status.md`, `learning-weak-spots.md`, and `final-stop-date.md`.

**Docs:** read `docs/PLAN.md` and `docs/BUDGET.md`. Read `docs/STRUCTURE.md` and the relevant parts of `docs/DECISIONS.md` if this session changed layout, flow, or a decision. Look only for:
- statements this session made wrong
- PLAN checkboxes now met, with the evidence
- decisions made but not recorded
- time left before the stop date against the work left, using today's date

**Conversation:** collect:
- questions either of us asked that were never answered
- bugs or risks found and not fixed
- goals or requirements that are still vague
- decisions, with the reason and rejected options
- claims nobody verified
- misconceptions, corrections, and things the user explained well
- preferences or corrections about how Claude should work

If part of the conversation was summarized, say so, because details may be missing.

## 2. Reconcile
Compare the conversation with the open items in memory. For each old item, decide: **resolved** (with evidence), **still open**, or **can't tell** (ask). Don't drop an item silently.

Label every "done" claim:
- **checked**: Claude ran it or read the result this session
- **reported**: the user said so
- **unverified**: neither

An earlier check counts only for code that hasn't changed since. Carry forward a label and its date; never upgrade one without new evidence. Code being written is not the same as code working.

## 3. Checkpoint
Show this and stop for a reply. Leave out empty sections, and keep each item to a line or two.

1. **Where we are:** what got done, with labels.
2. **Git:** uncommitted and unpushed work, and anything that shouldn't be committed.
3. **Unresolved:** questions for the user, bugs, vague goals, and unverified claims. Mark which ones block the next session. Number them so the user can answer by number.
4. **Docs:** the exact proposed edits, or "no changes needed". A DECISIONS entry must use the user's reasoning; if that's missing, ask for it.
5. **Schedule:** time left against work left. Say plainly if it doesn't fit, and point to the cut order in BUDGET. Ask for available hours if they're unknown.
6. **Learning:** proposed changes to `learning-weak-spots.md`.
7. **Next session goal:**
   - **Goal:** one outcome that fits the time available and serves an unchecked PLAN item. If it isn't in PLAN, flag it.
   - **Done when:** a check with an observable result.
   - **First step:** one concrete action.
   - **Cut first:** what to drop if time runs short.
   - **Decide first:** any modeling decision in the way. Don't pick an answer for the user.
8. **Quiz**, only if requested: one explain-back question on something this session changed or the user got wrong. Don't give the answer or hint at it.

End by asking for answers, corrections, and approval of the doc edits and goal. The user may leave questions open; record those as open.

If this was a quiz, assess the answer honestly after the reply. If it's wrong or partial, explain briefly and record it. Don't start another round unless asked.

## 4. Save
After the reply:

1. Make only the approved doc edits.
2. Rewrite `project-status.md` in the project memory directory. Keep its frontmatter `name` and refresh the description and date. Use these sections:
   - **Dates and time left**
   - **Where we are** (with labels and dates)
   - **Next session** (goal, done when, first step, cut first, decide first)
   - **Open questions and decisions**
   - **Bugs and risks**
   - **Unverified claims**
   - **Context not in the repo** (decisions, reasons, setup facts)
3. Update `learning-weak-spots.md`. Add evidence to existing items instead of duplicating them. Remove a weakness only after the user has explained it correctly without help, and say that you removed it.
4. Save new working preferences as `feedback` memories if they should outlive this session.
5. Fix `MEMORY.md` pointers that are now wrong.

Prune as you rewrite: remove resolved items, anything the repo or docs already record, and session narrative. Keep `project-status.md` under about 60 lines. If open items don't fit, keep them and cut background. Use absolute dates. Don't store a HEAD hash or say work is committed, since the user commits after this step.

Reread the saved files and confirm every open item from the checkpoint is in memory or the docs, or was resolved.

## 5. Commit plan
Run `git status` again so this includes the doc edits. Group changes by purpose and give one block per commit, in order:

```bash
git add path/one path/two
git commit -m "type: concise description"
```

- Use concise Conventional Commits with no AI attribution or co-author lines, on main.
- Name files explicitly. Don't use `git add .` or `-A`.
- If one file has changes for two commits, say so and recommend `git add -p` or one combined commit.
- Flag anything already staged, since a commit would include it.
- List files to leave out, and why.
- Don't present unfinished or broken work as complete in a message.
- If there's nothing to commit, say so. If commits will be unpushed, mention `git push` separately.

Memory files and `.claude/skills/` are outside these commits unless git shows them.

## 6. Handoff
End with one block to paste into the next chat, filled in and under 12 lines:

```text
Read project memory, starting with project-status.md, then check git status and recent commits. Trust the repo over memory and tell me about any mismatch.
Expected commits from last session: <messages, or none>
Goal: <goal>
Done when: <check>
First step: <step>
Decide or answer first: <items, or none>
Before starting, summarize where we are in a few lines and tell me if the goal no longer fits the time left.
```

It must work if pasted as is. Print nothing after it.
