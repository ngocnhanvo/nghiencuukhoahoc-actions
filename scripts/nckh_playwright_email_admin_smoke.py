#!/usr/bin/env python3
"""Read-mostly Playwright E2E for the staging-only NCKH teacher email selector.
Uses an approved existing WP admin secret; never sends mail, prints email, or stores screenshots.
"""
import os
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, expect

BASE = "https://api-nghiencuukhoahoc.webnvn.com"
PAGE = BASE + "/wp-admin/tools.php?page=nckh-invite-email"

def ensure_staging(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "api-nghiencuukhoahoc.webnvn.com":
        raise RuntimeError("STOP: Playwright left the permitted WordPress staging host")

def main():
    username = os.environ.get("WP_ADMIN_USERNAME", "")
    password = os.environ.get("WP_ADMIN_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("STOP: Existing WP staging admin secrets missing; no test session started")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=False, locale="vi-VN", accept_downloads=False)
        page = context.new_page()
        page.set_default_timeout(20000)
        ensure_staging(BASE)
        page.goto(BASE + "/wp-login.php", wait_until="domcontentloaded", timeout=45000)
        ensure_staging(page.url)
        page.locator("#user_login").fill(username)
        page.locator("#user_pass").fill(password)
        page.locator("#wp-submit").click()
        page.wait_for_url("**/wp-admin/**", timeout=45000)
        ensure_staging(page.url)
        print("PASS: Chromium signed into existing WordPress staging administrator")

        page.goto(PAGE, wait_until="domcontentloaded", timeout=45000)
        ensure_staging(page.url)
        if urlparse(page.url).path != "/wp-admin/tools.php":
            raise RuntimeError("Admin teacher email page not available")
        expect(page.locator("#nckh-test-teacher")).to_be_visible()
        expect(page.locator('form input[name="action"][value="nckh_invite_email_test_teacher"]')).to_have_count(1)
        expect(page.locator('form input[name="_wpnonce"]')).to_have_count(1)

        # No selection occurs if server flag is on. This action must not send a real email.
        if "ĐANG TẮT (an toàn)" not in page.locator("body").inner_text():
            raise RuntimeError("STOP: Outbound email appears enabled; will not change selection")

        choices = page.locator("#nckh-test-teacher option")
        available = [v for v in choices.evaluate_all("(els) => els.map(el => el.value)") if v and v != "0"]
        if not available:
            raise RuntimeError("No verified Google-linked teacher is listed on NCKH Email page")
        print(f"PASS: WordPress selector shows {len(available)} verified Google-linked teacher account(s)")

        selected = page.locator("#nckh-test-teacher").input_value()
        if selected in available:
            print("PASS: An approved verified teacher is already selected; no admin write needed")
        elif len(available) == 1:
            page.locator("#nckh-test-teacher").select_option(available[0])
            page.locator('form input[name="submit"]').click()
            page.wait_for_url("**/wp-admin/tools.php?page=nckh-invite-email&saved=1", timeout=40000)
            ensure_staging(page.url)
            expect(page.locator("#nckh-test-teacher")).to_have_value(available[0])
            print("PASS: Selected the sole verified teacher via nonce-protected staging admin UI")
        else:
            print("SAFE SKIP: Multiple verified teachers; requires explicit selection by admin")

        page.reload(wait_until="domcontentloaded", timeout=45000)
        ensure_staging(page.url)
        expect(page.locator("#nckh-test-teacher")).to_be_visible()
        if "ĐANG TẮT (an toàn)" not in page.locator("body").inner_text():
            raise RuntimeError("STOP: outbound flag unexpectedly active after selection")
        print("PASS: Admin selector persists and automatic invitation mail remains OFF")

        anon = browser.new_context(ignore_https_errors=False)
        anon_page = anon.new_page()
        anon_page.goto(PAGE, wait_until="domcontentloaded", timeout=45000)
        ensure_staging(anon_page.url)
        if anon_page.locator("#nckh-test-teacher").count():
            raise RuntimeError("SECURITY FAIL: Anonymous visitor can view teacher selector")
        print("PASS: Anonymous visitor cannot read privileged teacher selector")
        anon.close()
        context.close()
        browser.close()

    print("PASS: Playwright NCKH staging teacher email admin E2E; no SMTP send, no real student data")

if __name__ == "__main__":
    main()
