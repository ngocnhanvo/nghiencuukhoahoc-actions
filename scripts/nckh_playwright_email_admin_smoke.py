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


def verify_additional_admin_modules(page, browser):
    """Read-only Chromium QA for independently gated NCKH WordPress admin modules."""
    protected = [
        "/wp-admin/tools.php?page=nckh-rubric",
        "/wp-admin/tools.php?page=nckh-private-files",
        "/wp-admin/users.php?page=nckh-teacher-approval",
    ]
    rubric_url, files_url, teacher_url = [BASE + path for path in protected]

    page.goto(rubric_url, wait_until="domcontentloaded", timeout=45000)
    ensure_staging(page.url)
    if urlparse(page.url).path != "/wp-admin/tools.php":
        raise RuntimeError("Rubric WordPress admin page not accessible")
    expect(page.get_by_role("heading", name="Rubric NCKH — Quản lý phiên bản")).to_be_visible()
    keys = ["problem_solving", "data_analysis", "theory_application", "presentation"]
    criteria = page.locator('input[type="text"][name^="criterion["]')
    expect(criteria).to_have_count(20)
    for key in keys:
        for level in range(1, 6):
            field = page.locator(f'input[name="criterion[{key}][{level}]"]')
            expect(field).to_have_count(1)
            if not field.input_value().strip():
                raise RuntimeError("Rubric draft has an empty required level descriptor")
    if "CHƯA BẬT công bố rubric" not in page.locator("body").inner_text():
        raise RuntimeError("STOP: Rubric publication gate unexpectedly enabled")
    if page.locator('form input[name="action"][value="nckh_rubric_approve"]').count():
        raise RuntimeError("Rubric approval form must remain disabled on staging")
    print("PASS: Rubric editor renders 4x5 descriptors; publication remains OFF")

    page.goto(files_url, wait_until="domcontentloaded", timeout=45000)
    ensure_staging(page.url)
    expect(page.get_by_role("heading", name="Tệp riêng tư EduResearch — staging")).to_be_visible()
    body = page.locator("body").inner_text()
    if "Lưu tệp thật: ĐANG TẮT" not in body:
        raise RuntimeError("STOP: Real private file upload unexpectedly enabled")
    if "public_html" not in body:
        raise RuntimeError("Private storage policy warning was removed")
    marker = "Kiểm tra thư mục ngoài webroot và quyền ghi PHP:"
    if marker not in body:
        raise RuntimeError("D2 PHP-local storage diagnostic absent after staging release")
    if "CHƯA SẴN SÀNG" in body:
        print("BLOCKED D2: PHP reports storage path or write permissions are not ready")
    elif "SẴN SÀNG" in body:
        print("PASS D2: PHP confirms private directory path, no symlink and writable access")
    else:
        raise RuntimeError("D2 PHP directory diagnostic has unknown state")
    print("PASS: Private attachments remain disabled; file backup still unverified")

    page.goto(teacher_url, wait_until="domcontentloaded", timeout=45000)
    ensure_staging(page.url)
    if urlparse(page.url).path != "/wp-admin/users.php":
        raise RuntimeError("Teacher approval admin page not accessible")
    expect(page.get_by_role("heading", name="EduResearch Hub — Duyệt giáo viên")).to_be_visible()
    if "Chỉ tài khoản đã liên kết Google thật" not in page.locator("body").inner_text():
        raise RuntimeError("Teacher approval prerequisite warning is missing")
    forms = page.locator('form input[name="action"][value="nckh_teacher_approval"]')
    if forms.count() == 0 and "Chưa có tài khoản EduResearch" not in page.locator("body").inner_text():
        raise RuntimeError("No teacher approval form or documented empty state")
    print("PASS: Teacher approval UI visible with Google-linked identity guard; roles unchanged")

    anon = browser.new_context(ignore_https_errors=False, accept_downloads=False)
    anon_page = anon.new_page()
    for path in protected:
        anon_page.goto(BASE + path, wait_until="domcontentloaded", timeout=45000)
        ensure_staging(anon_page.url)
        if anon_page.locator('input[name^="criterion["]').count() or (
            anon_page.locator('input[name="action"][value="nckh_teacher_approval"]').count()
        ) or anon_page.locator("h1").filter(has_text="Tệp riêng tư EduResearch — staging").count():
            raise RuntimeError("SECURITY FAIL: Anonymous context can view private NCKH admin module")
    anon.close()
    print("PASS: Anonymous browser cannot access rubric/files/teacher private admin")



def audit_wordpress_home_ctas(page, context):
    """Discover the exact WP-owned home page before any content edit."""
    nonce_response = context.request.get(BASE + "/wp-admin/admin-ajax.php?action=rest-nonce", timeout=30000)
    if not nonce_response.ok:
        raise RuntimeError("Home page audit: WordPress REST nonce not available")
    nonce = nonce_response.text().strip()
    if not (8 <= len(nonce) <= 20):
        raise RuntimeError("Home page audit: invalid nonce")
    headers = {"X-WP-Nonce": nonce, "Accept": "application/json"}
    response = context.request.get(BASE + "/wp-json/wp/v2/pages?context=edit&per_page=100", headers=headers, timeout=40000)
    if not response.ok:
        raise RuntimeError(f"Home page audit: WordPress pages list HTTP {response.status}")
    pages = response.json()
    if not isinstance(pages, list):
        raise RuntimeError("Home page audit: WP pages result is not a list")
    markers = ("Hai phân hệ trong cùng một không gian học tập", "Bắt đầu hành trình nghiên cứu của bạn")
    identified = []
    for item in pages:
        content = item.get("content", {})
        html = content.get("raw", "") if isinstance(content, dict) else ""
        if all(marker in html for marker in markers):
            identified.append((item.get("id"), item.get("slug"), html))
    if len(identified) != 1:
        print(f"HOME AUDIT: {len(identified)} matching WordPress pages among {len(pages)} returned; no content changed")
        return
    page_id, slug, content = identified[0]
    print(f"PASS HOME AUDIT: exactly one matching WordPress home page, id={page_id}, slug={slug}")
    print(f"HOME AUDIT: legacy '#khong-gian' CTA occurrences={content.count('href=\\"#khong-gian\\"')}")
    print("HOME AUDIT: read-only; no homepage content changed by this browser run")

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
        verify_additional_admin_modules(page, browser)
        audit_wordpress_home_ctas(page, context)
        context.close()
        browser.close()

    print("PASS: Playwright NCKH multi-module staging admin E2E; no SMTP send, no private upload, no rubric publish")

if __name__ == "__main__":
    main()
