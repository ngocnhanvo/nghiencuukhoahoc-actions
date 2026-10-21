#!/usr/bin/env python3
"""Read-only post-deploy Lighthouse regression checks in real mobile Chromium."""
import re

from playwright.sync_api import sync_playwright

ORIGIN = "https://nghiencuukhoahoc.webnvn.com"


def relative_luminance(css_rgb):
    parts = [float(x) for x in re.findall(r"[\d.]+", css_rgb)[:3]]
    assert len(parts) == 3, css_rgb
    def linear(x):
        v = x / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return sum(x * linear(v) for x, v in zip((0.2126, 0.7152, 0.0722), parts))


def contrast(foreground, background):
    a, b = sorted((relative_luminance(foreground), relative_luminance(background)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def main():
    checks = [
        ("header brand subtitle", "#main-header .research-brand-subtitle", "rgb(255,255,255)"),
        ("notebook paragraph", ".nd-document .nd-paper-p", "rgb(255,255,255)"),
        ("notebook date", ".nd-document .nd-doc-foot span", "rgb(255,255,255)"),
        ("demo label", ".nd-demo-label", "rgb(255,255,255)"),
        ("footer copyright", ".nd-copyright span:first-child", "rgb(248,249,252)"),
        ("footer notice", ".nd-copyright span:last-child", "rgb(248,249,252)"),
    ]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            viewport={"width": 412, "height": 915},
            device_scale_factor=1,
            extra_http_headers={"Cache-Control": "no-cache"},
        )
        page = context.new_page()
        response = page.goto(ORIGIN + "/?nckh_qa=lighthouse_20261021", wait_until="domcontentloaded", timeout=60000)
        assert response and response.status == 200, f"Homepage HTTP {response.status if response else 'none'}"
        page.wait_for_selector(".nd-document-body", timeout=25000)
        for label, selector, bg in checks:
            element = page.locator(selector).first
            assert element.count() == 1, f"Missing {label} on live page"
            fg = element.evaluate("(el) => getComputedStyle(el).color")
            score = contrast(fg, bg)
            print(f"POST-DEPLOY {label}: {score:.2f}:1")
            assert score >= 4.5, f"WCAG contrast failure {label}: {score:.2f}:1"
        assert page.locator(".nd-document-body > h3").count() == 0, "H3 preview still skips H2"
        assert page.locator(".nd-document-body > h2").count() == 1, "Preview H2 missing"
        assert page.locator("h1").count() >= 1, "Page H1 missing"
        for name in ("llms.txt", "robots.txt", "sitemap.xml"):
            r = context.request.get(ORIGIN + "/" + name, headers={"Cache-Control": "no-cache"}, timeout=30000)
            assert r.status == 200, f"{name} HTTP {r.status}"
            body = r.text()
            assert "nghiencuukhoahoc.id.vn" not in body, f"Retired origin in {name}"
            if name == "llms.txt":
                assert re.search(r"^# ", body, re.M), "llms.txt missing H1"
                assert len(re.findall(r"\[[^\]]+\]\(https://[^)]+\)", body)) >= 2, "llms.txt missing Markdown links"
            elif name == "robots.txt":
                assert "Disallow: /" in body and ORIGIN + "/sitemap.xml" in body
            elif name == "sitemap.xml":
                assert "<loc>" + ORIGIN + "/</loc>" in body
            print(f"POST-DEPLOY {name}: HTTP 200, correct canonical content")
        print("PASS: live staging mobile Chromium accessibility and llms.txt/sitemap/robots smoke.")
        print("READ ONLY: no WordPress writes, no authentication, no FTP, no master merge.")
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
