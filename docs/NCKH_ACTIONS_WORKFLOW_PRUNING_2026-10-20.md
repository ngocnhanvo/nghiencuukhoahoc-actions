# NCKH Actions workflow consolidation — 2026-10-20

- Repository: `ngocnhanvo/nghiencuukhoahoc-actions`, target branch `main`; prior head: `605a7ee02171eb146d8aad91a3d1bc90b1525937`.
- Active workflow definitions before: **73**; retained: **25**; removed: **48**.
- Reason: one-shot migration/setup/diagnostic runs and legacy issue-triggered probes created hundreds of unrelated skipped runs every time a GitHub issue was opened.
- Preserved core staging Astro/PHP CI and deployment, protected skipped-only cleanup worker, one-task push dispatcher, SSE network probe, Google OAuth, teacher approval, backup, rest profiling, WordPress trigger and Node diagnostic.
- Protected queued/in-progress workflows at commit time: nckh-notebook-feature-check.yml, nckh-delete-skipped-runs.yml. **No workflow runs were cancelled or deleted by this source commit.** Completed/skipped-run history deletion is handled separately by the already-running protected worker.
- No Astro `master`, other projects, production FTP or live WordPress were touched.

## Removed redundant definitions

- `.github/workflows/bootstrap-nckh.yml`
- `.github/workflows/diagnose-source-repo-pat.yml`
- `.github/workflows/import-blue-sea-baseline.yml`
- `.github/workflows/nckh-api-root-redirect-probe.yml`
- `.github/workflows/nckh-api-root-redirect-staging-fix.yml`
- `.github/workflows/nckh-archive-legacy.yml`
- `.github/workflows/nckh-astro-syntax.yml`
- `.github/workflows/nckh-backed-up-schema-install.yml`
- `.github/workflows/nckh-check-job-status.yml`
- `.github/workflows/nckh-check-wp-trigger.yml`
- `.github/workflows/nckh-ci-status.yml`
- `.github/workflows/nckh-clean-home-editor-header.yml`
- `.github/workflows/nckh-cookie-redirect-isolation.yml`
- `.github/workflows/nckh-debug-trigger-guard.yml`
- `.github/workflows/nckh-deploy-trigger-guard.yml`
- `.github/workflows/nckh-enable-wp-trigger.yml`
- `.github/workflows/nckh-existing-redirect-compare.yml`
- `.github/workflows/nckh-google-auth-html-readonly.yml`
- `.github/workflows/nckh-google-route-isolation.yml`
- `.github/workflows/nckh-home-cta-inspect.yml`
- `.github/workflows/nckh-home-nav-live-qa.yml`
- `.github/workflows/nckh-launch-via-wp-trigger.yml`
- `.github/workflows/nckh-live-brand-consistency-qa.yml`
- `.github/workflows/nckh-menu-cta-fix.yml`
- `.github/workflows/nckh-nav-production-target-inspect.yml`
- `.github/workflows/nckh-posts-classify.yml`
- `.github/workflows/nckh-private-oauth-diagnose.yml`
- `.github/workflows/nckh-production-qa.yml`
- `.github/workflows/nckh-public-menu-cache-compare.yml`
- `.github/workflows/nckh-remove-redundant-intro-header.yml`
- `.github/workflows/nckh-stage-asset-integrity-readonly.yml`
- `.github/workflows/nckh-stage-clean-duplicate-root.yml`
- `.github/workflows/nckh-stage-core-root-isolation.yml`
- `.github/workflows/nckh-stage-final-client-asset-check.yml`
- `.github/workflows/nckh-stage-ftproot-dedup.yml`
- `.github/workflows/nckh-stage-relocate-env.yml`
- `.github/workflows/nckh-stage-root-audit.yml`
- `.github/workflows/nckh-stage-static-asset-isolation.yml`
- `.github/workflows/nckh-stage-static-isolation.yml`
- `.github/workflows/nckh-staging-auth-readonly-check.yml`
- `.github/workflows/nckh-staging-static-routing-fingerprint.yml`
- `.github/workflows/nckh-trigger-audit-status.yml`
- `.github/workflows/nckh-trigger-readonly-config.yml`
- `.github/workflows/nckh-ui-preview-readonly.yml`
- `.github/workflows/nckh-wordpress-live-header-menu.yml`
- `.github/workflows/nckh-wordpress-menu-native-import.yml`
- `.github/workflows/nckh-wordpress-nav-api-preflight.yml`
- `.github/workflows/set-master-default.yml`

## Recovery

GitHub source history preserves every removed definition at previous Actions `main` commit `605a7ee02171eb146d8aad91a3d1bc90b1525937`; restore only a required workflow from that SHA after review.


## Historical run cleanup: explicit approval on 20 Oct 2026

- User authorized removing **all completed Actions runs created through 19 Oct 2026 23:59:59 Asia/Ho_Chi_Minh** (UTC `2026-10-19T16:59:59Z`) in repository `ngocnhanvo/nghiencuukhoahoc-actions`; includes success, failure, skipped, and cancelled conclusions, rather than only skipped runs.
- **Never delete:** any currently `queued`, `waiting`, `requested`, `pending`, `in_progress` run; or any run dated 20 Oct 2026 or later (Vietnam time). Previous frozen snapshot of 126 originally queued runs remains on disk for provenance but does not indefinitely exempt them after completion, in accordance with the new explicit instruction.
- Script commit `130a3d3ff162e80cd3e489fc60a1f6cc22c4dbc7`: `scripts/nckh-delete-skipped-runs.py` now inventories once, rechecks completion and creation timestamp immediately before each deletion, then emits precise count/partial continuation to existing issue #302 and GitHub Step Summary. It limits deletion rates and respects GitHub API throttling. The existing filename is retained to avoid workflow trigger disruption.
- Workflow commit `cc44b4a6b462576990e0d8b5a14ca1b4f9cd1ee3`: `.github/workflows/nckh-delete-skipped-runs.yml` self-triggered on push, hourly schedule with serialized concurrency and no cancellation of running cleanup jobs; automatically disables itself after all eligible historical completed runs are gone.
- Independent read-only audit commit `2a40998437416dffdff50698b241b55248bb1ee5` posted to issue #302: **8,242** total Actions runs versus previous **8,974** (net decrease **732**, actual deletion count not independently broken down); latest newly requested cleanup [run 39354641502](https://github.com/ngocnhanvo/nghiencuukhoahoc-actions/actions/runs/39354641502) was **Pending** when sampled. This is **NOT YET a completed historical purge**; do not claim the backlog is empty until runner summary and final API count confirm it.
- This maintenance is **Actions repo only**. Astro `github`, PHP `master`, production and staging FTP contents were not changed by the cleanup.

Code mode: `auto`.
