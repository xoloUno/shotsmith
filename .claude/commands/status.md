Quick session orientation for shotsmith — run at the start of every session.

Steps:
1. Run `git branch --show-current` and `git status --short` — current branch +
   dirty state
2. Run `git log --oneline -5` — recent commits
3. Run `git rev-list --left-right --count origin/main...HEAD 2>/dev/null` to
   show ahead/behind state vs. origin/main
4. Check the latest CI run for the current branch:
   `gh run list --branch "$(git branch --show-current)" --limit 1 --json status,conclusion,workflowName,createdAt`
   — show pass/fail of the most recent run (✅ / ❌ / 🟡 pending)
5. Check open PRs in this repo: `gh pr list --state open`
6. Show the current version from `VERSION` and the most recent tag
   (`git describe --tags --abbrev=0`)
7. If `CHANGELOG.md` has an unreleased section (lines after the
   `# shotsmith Changelog` header but before the first `## vN.N.N` heading),
   summarize what's queued

Present as a concise briefing — not a wall of text:

```
## shotsmith Session Briefing

**Branch:** <branch> | **Version:** <VERSION> | **Last tag:** <tag>
**vs origin/main:** <N ahead, M behind>
**CI:** ✅ passing / ❌ failing / 🟡 pending (run #<N> on <branch>)

### Recent commits
<git log --oneline -5 output>

### Open PRs
- #<N> <title> — <status>

### Flags
- ⚠️ <any uncommitted changes, failing CI, ahead-of-origin without push>
- ✓ Clean — no flags <if nothing to report>
```

After presenting, ask: "What would you like to work on?"
