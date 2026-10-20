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
