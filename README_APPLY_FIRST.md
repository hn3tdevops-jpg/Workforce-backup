# Workforce Repo Base — Apply First

This scaffold is intended to be copied into the **existing Workforce repository** as the project-control and architecture baseline.

It is designed to be **additive**:
- planning and control files
- Copilot instructions
- repo safety / recovery helpers
- architecture and domain-model docs

It deliberately avoids making assumptions about your existing runtime code.

## Recommended apply order

1. Create a branch:
   ```bash
   git switch -c foundation-freeze
   ```

2. Copy these files into the repo root.

3. Review and adjust these first:
   - `docs/plans/HN3T_MASTER_PLAN.md`
   - `docs/ROADMAP.md`
   - `docs/DOMAIN_MODEL.md`
   - `docs/TODO.md`

4. Commit the repo base:
   ```bash
   git add .
   git commit -m "Add repo operating system and foundation docs"
   ```

5. Tag a restore point after the repo still boots:
   ```bash
   git tag foundation-v0.1
   ```

6. Push the branch and tag:
   ```bash
   git push -u origin foundation-freeze
   git push origin foundation-v0.1
   ```

## Ground rule

Do not start new feature work until:
- this scaffold is in the repo,
- the app still boots,
- the current runtime target is documented,
- a restore tag exists.

## What belongs where

- `docs/` = source of truth for architecture, backlog, worklog, decisions
- `.github/` = Copilot behavior, PR workflow, setup steps
- `scripts/` = repeatable repo-safety helpers
- `templates/` = ADR / worklog / task entry templates
