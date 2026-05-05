End-of-session wrap-up for shotsmith — commit cleanly, push, leave the repo in good shape.

Steps:
1. Run `git status` — review staged, unstaged, untracked
2. Show the user a concise summary of what changed this session
3. **Run tests if Python source changed:** `pytest tests/ -q`. Failures must be
   fixed or explicitly acknowledged before committing.
4. **Stage selectively** — never `git add .` blindly. Group related changes into
   logical commits if multiple concerns were worked on.
5. **Write conventional commit message(s):**
   - Format: `type(scope): short description`
   - Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`
   - Include `Co-Authored-By: Claude <noreply@anthropic.com>`
6. **Update `CHANGELOG.md`** if the change is user-facing — new feature, behavior
   change, schema change, dependency change, breaking change. Trivial
   doc/test/internal-refactor commits don't need a CHANGELOG entry.
7. **Schema-breaking changes:** bump the major version in `VERSION`,
   `pyproject.toml`, and `shotsmith/__init__.py` (must stay in sync) and add a
   clear entry to `CHANGELOG.md`.
8. **Branch routing:**
   - If on `main`: do **NOT** push directly by default. The repo's branch
     protection forbids it for most session work. Create a feature branch
     (`feat/<short-slug>`, `fix/<slug>`, `docs/<slug>`, etc.) from HEAD, push
     that, and open a PR via `gh pr create`. Report the PR URL.
   - If on a feature branch: push with `git push -u origin <branch>`. If no
     PR exists yet, offer to create one.
   - Exception: routine docs/CI/internal-only changes that the maintainer
     explicitly authorized for direct-push (e.g. "push directly"). Always wait
     for explicit authorization — "push" alone in chat is not specific
     authorization for the default branch.
9. Confirm to the user: what was committed, what branch, PR URL (if applicable),
   what's next.

If there are no changes to commit, say so and skip to step 9.

Notes:
- Don't `git push --force` without explicit user request.
- For multi-file changes, prefer one commit per logical unit. Don't bundle a
  CHANGELOG update with an unrelated bug fix.
