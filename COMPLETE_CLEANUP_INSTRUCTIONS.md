# Complete Repository Cleanup Instructions

## Current Status

### ✅ COMPLETED (By Claude)
1. **Merged 46 out of 51 branches** into a single consolidated commit
   - 5 branches skipped (already merged into main)
   - 151 commits consolidated
   - All conflicts resolved using `-X theirs` strategy
2. **Created squashed commit** with all changes
3. **Pushed to branch:** `claude/merge-all-prs-final-011CUp7WpQC3pD3sBjBEE15V`

### ❌ BLOCKED (Permission Restrictions)
1. **Cannot push to main** - 403 Forbidden error
2. **Cannot delete remote branches** - 403 Forbidden error

Main branch is protected and requires admin permissions.

---

## What YOU Need to Do

### Step 1: Merge the Consolidated PR into Main

**Option A: Via GitHub UI (Recommended)**
1. Go to: https://github.com/Anthony5265/Windows-AI/pull/new/claude/merge-all-prs-final-011CUp7WpQC3pD3sBjBEE15V
2. Create the Pull Request
3. Review the changes (46 PRs merged, 151 commits)
4. **Merge** or **Squash and Merge** into main

**Option B: Via Command Line (if you have admin access)**
```bash
# Clone/update repo
git fetch origin
git checkout main
git pull origin main

# Merge the consolidated branch
git merge --ff-only origin/claude/merge-all-prs-final-011CUp7WpQC3pD3sBjBEE15V

# Push to main
git push origin main
```

---

### Step 2: Delete ALL 51 Remote Branches

After merging to main, delete all branches:

```bash
# Delete all codex branches (40 branches)
git push origin --delete \
  chore/bootstrap-skeleton \
  codex/add-accessibility-features-and-guidelines \
  codex/add-dockerfile-and-devcontainer-configuration \
  codex/add-heartbeat-and-auto-reconnect-in-mesh \
  codex/add-heartbeat-and-reconnection-logic \
  codex/add-json-serialization-for-permissions \
  codex/add-logging-and-tests-for-system-info \
  codex/add-new-feature-for-user-profiles \
  codex/add-new-feature-for-user-profiles-iq7hsg \
  codex/add-new-feature-for-user-profiles-qm2xlk \
  codex/add-preprocessing-and-execution-logic \
  codex/add-save-and-load-methods-for-permissions \
  codex/add-snapshot-utilities-for-rollback \
  codex/add-stale-action-workflow-and-documentation \
  codex/add-uninstall-method-to-plugin-manager \
  codex/add-uninstall-method-to-plugin-manager-wugigz \
  codex/add-unregister-methods-to-input-manager-0g9wh7 \
  codex/add-user-authentication-feature \
  codex/add-user-authentication-feature-aum6u1 \
  codex/add-windows-support-for-command-execution \
  codex/add-zeroconf-adapter-and-tests \
  codex/add-zeroconf-adapter-for-discovery \
  codex/add-zeroconf-adapter-for-discovery-sgtcq5 \
  codex/create-pull-request-template-and-contrib-docs \
  codex/define-rest-endpoints-for-pairing-and-control \
  codex/define-rest-endpoints-for-pairing-and-control-qo31jj \
  codex/develop-agents-package-and-examples \
  codex/enhance-download_model-with-retries-and-timeout \
  codex/expand-tests-for-new-modules \
  codex/extend-build_installer.ps1-for-python-runtime \
  codex/extend-ecoscheduler-to-support-time-windows-islj0w \
  codex/fix-all-pull-requests \
  codex/fix-all-pull-requests-o9vtql \
  codex/implement-cloud_sync-module-for-backup \
  codex/implement-energy-usage-tracking-and-scheduling \
  codex/modify-analyze_processes-to-collect-metrics \
  codex/no-task-prompt-provided \
  codex/no-task-prompt-provided-ydhqpl \
  codex/read-environment-variables-and-enhance-error-handling \
  codex/replace-xor-with-hmac-encryption-eiy5mg \
  codex/setup-commitlint-with-git-hook \
  codex/standardize-apis-across-modules \
  codex/update-file-handling-in-explorer.py \
  codex/update-file-handling-in-explorer.py-fa1tq7 \
  codex/update-test-script-and-ci-configuration

# Delete dependabot branches (6 branches)
git push origin --delete \
  dependabot/npm_and_yarn/apps/gui/electron-38.4.0 \
  dependabot/npm_and_yarn/electron-38.4.0 \
  dependabot/npm_and_yarn/mobile/react-native-0.82.1 \
  dependabot/npm_and_yarn/react-native-0.82.1 \
  dependabot/npm_and_yarn/windows-ai-agent/openai-6.7.0 \
  dependabot/npm_and_yarn/windows-ai-tray/electron-38.4.0

# Delete the claude consolidation branch
git push origin --delete claude/merge-all-prs-final-011CUp7WpQC3pD3sBjBEE15V
```

**Alternative: Delete via GitHub UI**
1. Go to: https://github.com/Anthony5265/Windows-AI/branches
2. Click "Delete" on each branch
3. Or use the bulk delete feature if available

---

### Step 3: Close Any Remaining Open PRs

All PRs should auto-close when branches are deleted, but verify:

```bash
# Check for open PRs (requires gh CLI)
gh pr list --state open

# Close any remaining PRs
gh pr close <PR_NUMBER> --comment "Merged via consolidated PR"
```

---

### Step 4: Verify Clean State

```bash
# Verify only main branch remains
git fetch origin --prune
git branch -r

# Should see only:
# origin/main
# origin/HEAD -> origin/main

# Verify no open PRs
gh pr list --state open

# Should see:
# (no results)
```

---

## What Was Merged

### Summary
- **46 PRs merged** (5 already in main, 151 commits total)
- **27 files changed**
- **931 insertions, 2,035 deletions**

### Categories
1. **Dependency Updates** (6): Electron, React Native, OpenAI SDK
2. **Infrastructure** (7): Docker, Commitlint, CI/CD, tests
3. **Security** (3): Permissions, snapshots, encryption
4. **Features** (12): Accessibility, Windows support, IoT, mobile
5. **Plugin System** (2): Uninstall, input manager
6. **Bug Fixes** (8): Logging, error handling, timeouts
7. **Documentation** (6): PR templates, guides
8. **Large Consolidations** (2): codex/fix-all-pull-requests (119 commits)

---

## Troubleshooting

### If merge conflicts occur
```bash
# Reset and try again
git checkout main
git reset --hard origin/main
git merge --no-ff origin/claude/merge-all-prs-final-011CUp7WpQC3pD3sBjBEE15V

# If conflicts, accept all incoming changes
git checkout --theirs .
git add -A
git commit -m "Merge all PRs: resolve conflicts"
git push origin main
```

### If branches won't delete
```bash
# Force delete
git push origin --delete --force <branch-name>

# Or delete via GitHub API
curl -X DELETE \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/Anthony5265/Windows-AI/git/refs/heads/<branch-name>
```

---

## Final Goal Achieved

After completing the above steps:
- ✅ 0 branches (except main)
- ✅ 0 open PRs
- ✅ All work consolidated in main
- ✅ Clean repository ready for development

---

## Files Generated by This Process

1. `COMPLETE_CLEANUP_INSTRUCTIONS.md` - This file
2. `PR_REVIEW_REPORT.md` - Detailed analysis of all PRs
3. `FIX_ALL_BRANCHES_INVESTIGATION.md` - Investigation of large branches
4. All merged in branch: `claude/merge-all-prs-final-011CUp7WpQC3pD3sBjBEE15V`

---

*Generated by Claude Code - November 5, 2025*
