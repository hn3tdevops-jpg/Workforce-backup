# Recovery Playbook

## Branch discipline
- `main` = safest known branch
- phase branches = controlled integration branches
- feature branches = single units of work

## Restore checkpoints
Create a tag before risky changes and after stable milestones.

Examples:
- `foundation-v0.1`
- `tenant-rbac-v0.1`
- `schedule-core-v0.1`

## If current work should be thrown away
```bash
git restore .
git clean -fd
```

## If you need to reset to a known good point
```bash
git switch main
git reset --hard foundation-v0.1
```
