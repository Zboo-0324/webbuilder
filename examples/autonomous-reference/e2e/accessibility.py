"""Deterministic baseline accessibility checks run against a live Playwright page.

Each public function returns a list of human-readable failure strings.
An empty list means the check passed.  These are *not* full axe-core scans;
they cover the structural basics that every page must satisfy.
"""

from __future__ import annotations

from playwright.sync_api import Page


# -- JavaScript snippets executed in the browser context --------------------

_LANG_CHECK = """() => {
    const lang = document.documentElement.getAttribute('lang');
    if (!lang || !lang.trim()) return 'document element missing lang attribute';
    return null;
}"""

_MAIN_AND_H1_CHECK = """() => {
    const failures = [];
    if (!document.querySelector('main')) failures.push('page missing <main> landmark');
    const h1s = document.querySelectorAll('h1');
    if (h1s.length === 0) failures.push('page missing <h1>');
    return failures;
}"""

_IMG_ALT_CHECK = """() => {
    const failures = [];
    for (const img of document.querySelectorAll('img')) {
        if (!img.hasAttribute('alt')) {
            failures.push('img missing alt: ' + (img.src || '(no src)'));
        }
    }
    return failures;
}"""

_CONTROL_NAME_CHECK = """() => {
    const failures = [];
    for (const el of document.querySelectorAll('button, a[href], [role="button"], [role="link"]')) {
        const name = (el.textContent || '').trim() || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.getAttribute('title');
        if (!name) {
            const tag = el.tagName.toLowerCase();
            const id = el.id ? '#' + el.id : '';
            failures.push('control missing accessible name: <' + tag + id + '>');
        }
    }
    return failures;
}"""

_LABEL_CHECK = """() => {
    const failures = [];
    for (const input of document.querySelectorAll('input, select, textarea')) {
        if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button') continue;
        const id = input.id;
        const hasLabel = id && document.querySelector('label[for="' + id + '"]');
        const hasAria = input.getAttribute('aria-label') || input.getAttribute('aria-labelledby');
        const wrappedInLabel = input.closest('label');
        if (!hasLabel && !hasAria && !wrappedInLabel) {
            const desc = input.tagName.toLowerCase() + (id ? '#' + id : '') + (input.name ? '[name=' + input.name + ']' : '');
            failures.push('input missing associated label: ' + desc);
        }
    }
    return failures;
}"""

_HEADING_SKIP_CHECK = """() => {
    const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
    const failures = [];
    for (let i = 1; i < headings.length; i++) {
        const prev = parseInt(headings[i - 1].tagName[1], 10);
        const curr = parseInt(headings[i].tagName[1], 10);
        if (curr > prev + 1) {
            failures.push('heading level skip: h' + prev + ' -> h' + curr);
        }
    }
    return failures;
}"""

_DUPLICATE_ID_CHECK = """() => {
    const seen = {};
    const failures = [];
    for (const el of document.querySelectorAll('[id]')) {
        const id = el.id;
        if (!id) continue;
        if (seen[id]) {
            failures.push('duplicate id: ' + id);
        }
        seen[id] = true;
    }
    return failures;
}"""

_HIDDEN_FOCUSABLE_CHECK = """() => {
    const failures = [];
    for (const el of document.querySelectorAll('a[href], button, input, select, textarea, [tabindex]')) {
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') {
            const tabindex = el.getAttribute('tabindex');
            if (tabindex !== null && parseInt(tabindex, 10) >= 0) {
                const desc = el.tagName.toLowerCase() + (el.id ? '#' + el.id : '');
                failures.push('focusable element hidden by CSS: ' + desc);
            }
        }
    }
    return failures;
}"""


# -- Public API -------------------------------------------------------------

def baseline_accessibility_failures(page: Page) -> list[str]:
    """Run all baseline checks and return a flat list of failure strings."""
    failures: list[str] = []

    result = page.evaluate(_LANG_CHECK)
    if result:
        failures.append(result)

    for item in page.evaluate(_MAIN_AND_H1_CHECK):
        failures.append(item)

    for item in page.evaluate(_IMG_ALT_CHECK):
        failures.append(item)

    for item in page.evaluate(_CONTROL_NAME_CHECK):
        failures.append(item)

    for item in page.evaluate(_LABEL_CHECK):
        failures.append(item)

    for item in page.evaluate(_HEADING_SKIP_CHECK):
        failures.append(item)

    for item in page.evaluate(_DUPLICATE_ID_CHECK):
        failures.append(item)

    for item in page.evaluate(_HIDDEN_FOCUSABLE_CHECK):
        failures.append(item)

    return failures
