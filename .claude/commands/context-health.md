Check session health — gauge how heavy this session is and whether to checkpoint.

**Important caveat:** Claude Code does not expose token counts or context window
usage directly. This command uses observable proxy signals to estimate session
weight and recommend action.

Steps:
1. **Uncommitted changes:** `git status` and `git diff --stat` to count:
   - Number of files modified (staged + unstaged)
   - Number of untracked files
   - Total lines changed (insertions + deletions)
2. **Session activity:** `git log --oneline --since="8 hours ago"` to see how many
   commits have been made in the current working session
3. **Branch state:** Check if the current branch is ahead of its upstream:
   `git rev-list --count @{upstream}..HEAD 2>/dev/null`
4. **Stale uncommitted work:** If there are uncommitted changes, check when the
   last commit was made. If >30 min of work is uncommitted, flag it.

Present as a compact dashboard:

```
## Session Health

| Signal | Status |
|---|---|
| Uncommitted files | 3 modified, 1 untracked |
| Uncommitted lines | +142 / -38 |
| Session commits | 4 (last: 12 min ago) |
| Unpushed commits | 2 ahead of origin |

### Recommendation
- ✓ Healthy — session is clean, keep going
  OR
- ⚠️ Checkpoint recommended — significant uncommitted work. Consider committing
  current progress before continuing.
  OR
- 🔴 Checkpoint now — large amount of uncommitted changes at risk. Commit and
  push before doing more work.
```

Recommendation thresholds:
- **Healthy:** <3 uncommitted files AND <100 uncommitted lines AND pushed recently
- **Checkpoint recommended:** 3-8 uncommitted files OR 100-300 uncommitted lines
  OR unpushed commits >3 OR last commit >30 min ago with changes
- **Checkpoint now:** >8 uncommitted files OR >300 uncommitted lines OR
  uncommitted changes with no commits in >1 hour

After showing the dashboard, if recommendation is not "Healthy", offer to run `/wrapup`.
