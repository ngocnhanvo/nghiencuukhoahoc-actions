#!/usr/bin/env python3
"""Remove ONLY completed/skipped NCKH Actions runs. Never delete active or useful CI logs."""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

REPO = "ngocnhanvo/nghiencuukhoahoc-actions"
ROOT = "/repos/" + REPO
TOKEN = os.environ.get("GITHUB_TOKEN", "")
BEGAN = time.monotonic()
CUTOFF = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
MAX_SECONDS = 2700
MAX_DELETIONS = 1600
FLOWS = ".github/workflows/nckh-delete-skipped-runs.yml"
SNAPSHOT = Path("docs/nckh-protected-action-runs-2026-10-19.json")


def call(method: str, path: str, data: dict | None = None):
    if (os.environ.get("GITHUB_REPOSITORY") != REPO
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or not TOKEN or not path.startswith(ROOT + "/")):
        raise RuntimeError("STOP: repository, branch, GitHub token or API allowlist mismatch")
    raw = json.dumps(data).encode() if data is not None else None
    for attempt in range(6):
        req = urllib.request.Request(
            "https://api.github.com" + path,
            data=raw, method=method,
            headers={"Authorization": "Bearer " + TOKEN,
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28",
                     "User-Agent": "NCKH-SkipOnlyCleanup",
                     **({"Content-Type": "application/json"} if raw is not None else {})})
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                body = response.read(3200000)
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and method in ("DELETE", "GET"):
                return None
            if exc.code not in (403, 429, 500, 502, 503, 504):
                raise RuntimeError("GitHub API HTTP " + str(exc.code) + " during " + method) from None
            remaining = exc.headers.get("X-RateLimit-Remaining", "")
            reset = int(exc.headers.get("X-RateLimit-Reset", "0"))
            retry = exc.headers.get("Retry-After", "")
            if remaining == "0":
                sleep = max(30, min(2400, reset - time.time() + 10))
            elif retry.isdigit():
                sleep = min(900, max(10, int(retry)))
            else:
                sleep = min(240, 20 * (attempt + 1))
            print("GitHub API busy or throttled, HTTP", exc.code,
                  "retry in", int(sleep), "sec", flush=True)
            if time.monotonic() + sleep > BEGAN + MAX_SECONDS:
                raise TimeoutError("Safe cleanup window exceeded while waiting for GitHub")
            time.sleep(sleep)
        except urllib.error.URLError as exc:
            if attempt == 5:
                raise RuntimeError("GitHub API network unavailable") from exc
            time.sleep(min(30, 5 * (attempt + 1)))
    raise RuntimeError("GitHub API retry limit exceeded")


def main():
    manifest = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if manifest["repository"] != REPO or len(manifest["protected_run_ids"]) < 126:
        raise RuntimeError("Original queued run snapshot missing/invalid: STOP")
    protected = {int(i) for i in manifest["protected_run_ids"]}
    protected.add(int(os.environ.get("GITHUB_RUN_ID", "0")))
    candidates = []
    near_now_skipped = 0
    scanned = 0

    # Snapshot first: deleting while paginating could skip unrelated records.
    # Dynamic active runs are protected as well as the original queued IDs.
    for page in range(1, 151):
        payload = call("GET", ROOT + "/actions/runs?per_page=100&page=" + str(page))
        runs = (payload or {}).get("workflow_runs", [])
        if not isinstance(runs, list):
            raise RuntimeError("Unexpected GitHub Actions response")
        for run in runs:
            scanned += 1
            rid = int(run.get("id", 0))
            if run.get("status") != "completed":
                protected.add(rid)
                continue
            if run.get("conclusion") != "skipped" or rid in protected:
                continue
            if run.get("created_at", "") > CUTOFF:
                near_now_skipped += 1
                continue
            if rid > 0:
                candidates.append(rid)
        if len(runs) < 100:
            break
    else:
        raise RuntimeError("More than 15,000 runs; pagination snapshot incomplete. STOP")

    print("SAFE PREVIEW: scanned", scanned, "protected", len(protected),
          "completed skipped eligible", len(candidates),
          "recent skipped deferred", near_now_skipped, flush=True)
    deleted = 0
    for rid in candidates:
        if deleted >= MAX_DELETIONS or time.monotonic() - BEGAN > MAX_SECONDS - 45:
            break
        if rid in protected:
            continue
        current = call("GET", ROOT + "/actions/runs/" + str(rid))
        if (not current or current.get("status") != "completed"
                or current.get("conclusion") != "skipped"
                or current.get("created_at", "") > CUTOFF):
            continue
        # GitHub returns 204; only an explicitly revalidated skipped run can be deleted.
        call("DELETE", ROOT + "/actions/runs/" + str(rid))
        deleted += 1
        if deleted % 100 == 0:
            print("Deleted", deleted, "completed/skipped-only runs; saved all meaningful CI", flush=True)
        time.sleep(1.35)

    remaining = max(0, len(candidates) - deleted)
    summary = (
        "### NCKH skipped-only Actions cleanup\n\n"
        f"Scanned **{scanned}** runs; eligible completed+skipped **{len(candidates)}**; "
        f"deleted **{deleted}** in this pass; remaining candidates **{remaining}**; "
        f"newest skipped deferred **{near_now_skipped}**.\n\n"
        "Preserved: all queued/pending/waiting/requested/in-progress, the original "
        "126 queued run IDs, and every successful/failed/cancelled job including "
        "PHP/Astro deployments and test evidence.\n\n"
        "No FTP, source code, staging database or production content modified.\n"
    )
    print(summary, flush=True)
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf8") as summary_file:
        summary_file.write(summary)
    try:
        call("POST", ROOT + "/issues/302/comments", {"body": summary})
    except Exception as exc:
        print("Notice: unable to publish optional cleanup issue comment:", type(exc).__name__, flush=True)

    if remaining == 0 and near_now_skipped == 0:
        call("PUT", ROOT + "/actions/workflows/" + FLOWS.split("/")[-1] + "/disable")
        print("Cleanup complete: temporary cleanup workflow disabled.", flush=True)
    else:
        print("More skipped runs remain. Safe two-hour scheduled pass retained.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("STOP: no unverified deletion allowed:", type(error).__name__, str(error), file=sys.stderr)
        raise
