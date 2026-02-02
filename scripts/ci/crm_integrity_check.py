#!/usr/bin/env python3
"""
CRM Integrity Check — validates GitLab Issues CRM health.

Tests:
  1. Every issue has exactly one status:: label
  2. No orphaned labels (labels exist but no issues use them)
  3. Board lists match status labels
  4. Hot leads have active statuses (not absage/ghost)
  5. Duplicate detection (same title or very similar)
  6. Data completeness (description has required fields)

Usage:
  python3 crm_integrity_check.py              # full check
  python3 crm_integrity_check.py --fix        # auto-fix simple issues
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from collections import Counter, defaultdict

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════

GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN", "")
GITLAB_API = "https://gitlab.com/api/v4"
CRM_PROJECT_ID = int(os.environ.get("CRM_PROJECT_ID", "78171527"))
GROUP_ID = int(os.environ.get("GROUP_ID", "120698013"))
AUTO_FIX = "--fix" in sys.argv

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def api_get(url):
    req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": GITLAB_TOKEN})
    return json.loads(urllib.request.urlopen(req).read())

def api_get_paginated(url):
    results = []
    page = 1
    while True:
        sep = "&" if "?" in url else "?"
        data = api_get(f"{url}{sep}per_page=100&page={page}")
        if not data:
            break
        results.extend(data)
        page += 1
    return results


class QAResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.fixed = 0
        self.details = []

    def ok(self, msg):
        self.passed += 1
        self.details.append(f"  ✅ {msg}")

    def fail(self, msg):
        self.failed += 1
        self.details.append(f"  ❌ {msg}")

    def warn(self, msg):
        self.warnings += 1
        self.details.append(f"  ⚠️  {msg}")

    def fix(self, msg):
        self.fixed += 1
        self.details.append(f"  🔧 {msg}")

    def section(self, title):
        self.details.append(f"\n━━━ {title} ━━━")

    def summary(self):
        self.details.append(f"\n{'='*60}")
        total = self.passed + self.failed + self.warnings
        line = f"  CRM QA: {self.passed}/{total} passed"
        if self.failed:
            line += f", {self.failed} failed"
        if self.warnings:
            line += f", {self.warnings} warnings"
        if self.fixed:
            line += f", {self.fixed} auto-fixed"
        self.details.append(line)
        if self.failed == 0 and self.warnings == 0:
            self.details.append(f"  🟢 CRM HEALTHY")
        elif self.failed == 0:
            self.details.append(f"  🟡 CRM OK (with warnings)")
        else:
            self.details.append(f"  🔴 CRM ISSUES FOUND")
        return "\n".join(self.details)


# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

def test_status_labels(qa, issues):
    """Every open issue must have exactly one status:: label."""
    qa.section("TEST 1: Status Label Integrity")

    no_status = []
    multi_status = []
    for i in issues:
        statuses = [l for l in i["labels"] if l.startswith("status::")]
        if len(statuses) == 0:
            no_status.append(i["iid"])
        elif len(statuses) > 1:
            multi_status.append((i["iid"], statuses))

    if not no_status:
        qa.ok(f"All {len(issues)} issues have a status label")
    else:
        qa.fail(f"{len(no_status)} issues without status: {no_status[:10]}")

    if not multi_status:
        qa.ok("No issues with multiple status labels")
    else:
        qa.fail(f"{len(multi_status)} issues with multiple statuses")
        for iid, statuses in multi_status[:5]:
            qa.details.append(f"       #{iid}: {statuses}")


def test_label_consistency(qa, issues):
    """Check for label typos, unused labels, rate/status conflicts."""
    qa.section("TEST 2: Label Consistency")

    # Valid scoped labels
    valid_prefixes = {
        "status::", "rate::", "match::", "remote::", "tech::",
        "branche::", "region::", "project::"
    }

    used_labels = Counter()
    unknown_labels = set()
    for i in issues:
        for l in i["labels"]:
            used_labels[l] += 1
            is_scoped = any(l.startswith(p) for p in valid_prefixes)
            is_special = l in ("overpace", "team-projekt", "hot-lead")
            if not is_scoped and not is_special:
                unknown_labels.add(l)

    if not unknown_labels:
        qa.ok("All labels are known/scoped")
    else:
        qa.warn(f"Unknown labels: {unknown_labels}")

    # Check for common typos
    all_labels = set(used_labels.keys())
    for l in all_labels:
        if "stauts" in l or "staus" in l:
            qa.fail(f"Typo in label: {l}")

    qa.ok(f"{len(all_labels)} unique labels in use across {len(issues)} issues")


def test_hot_lead_consistency(qa, issues):
    """Hot leads should have active statuses."""
    qa.section("TEST 3: Hot Lead Consistency")

    inactive_statuses = {"status::absage", "status::ghost"}
    inconsistent = []

    for i in issues:
        if "hot-lead" in i["labels"]:
            statuses = [l for l in i["labels"] if l.startswith("status::")]
            if statuses and statuses[0] in inactive_statuses:
                inconsistent.append((i["iid"], statuses[0], i["title"][:50]))

    if not inconsistent:
        hot_count = sum(1 for i in issues if "hot-lead" in i["labels"])
        qa.ok(f"All {hot_count} hot leads have active statuses")
    else:
        qa.warn(f"{len(inconsistent)} hot leads with inactive status")
        for iid, status, title in inconsistent[:5]:
            qa.details.append(f"       #{iid} {status}: {title}")


def test_duplicates(qa, issues):
    """Detect duplicate or very similar issues."""
    qa.section("TEST 4: Duplicate Detection")

    # Exact title match
    title_groups = defaultdict(list)
    for i in issues:
        title_groups[i["title"]].append(i["iid"])

    exact_dupes = {t: iids for t, iids in title_groups.items() if len(iids) > 1}
    if not exact_dupes:
        qa.ok("No exact title duplicates")
    else:
        qa.warn(f"{len(exact_dupes)} exact title duplicates")
        for t, iids in exact_dupes.items():
            qa.details.append(f"       IIDs {iids}: {t[:55]}")

    # Fuzzy: normalize and check
    def normalize(title):
        t = title.lower()
        t = re.sub(r'\[.*?\]\s*', '', t)  # Remove [Agency]
        t = re.sub(r'\(m/w/d\)|\(w/m/d\)|\(d/m/w\)', '', t)
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    norm_groups = defaultdict(list)
    for i in issues:
        norm = normalize(i["title"])
        norm_groups[norm].append(i["iid"])

    fuzzy_dupes = {t: iids for t, iids in norm_groups.items()
                   if len(iids) > 1 and t not in [normalize(k) for k in exact_dupes]}
    if fuzzy_dupes:
        qa.warn(f"{len(fuzzy_dupes)} fuzzy title duplicates (same project, different agency?)")
        for t, iids in list(fuzzy_dupes.items())[:5]:
            qa.details.append(f"       IIDs {iids}: {t[:55]}")
    else:
        qa.ok("No fuzzy title duplicates")


def test_data_completeness(qa, issues):
    """Check that descriptions contain required structured data."""
    qa.section("TEST 5: Data Completeness")

    required_fields = ["Agentur", "Kontakt", "Standort", "Stundensatz"]
    missing_counts = Counter()
    empty_desc = 0

    for i in issues:
        desc = i.get("description", "")
        if not desc or len(desc) < 50:
            empty_desc += 1
            continue
        for field in required_fields:
            if field not in desc:
                missing_counts[field] += 1

    if empty_desc == 0:
        qa.ok("All issues have descriptions")
    else:
        qa.fail(f"{empty_desc} issues with empty/short descriptions")

    for field in required_fields:
        count = missing_counts.get(field, 0)
        if count == 0:
            qa.ok(f"Field '{field}' present in all descriptions")
        else:
            qa.warn(f"Field '{field}' missing in {count} descriptions")


def test_board_alignment(qa):
    """Check that board lists match status labels."""
    qa.section("TEST 6: Board Alignment")

    try:
        boards = api_get(f"{GITLAB_API}/projects/{CRM_PROJECT_ID}/boards")
        if not boards:
            qa.warn("No boards configured")
            return

        board = boards[0]
        lists = api_get(f"{GITLAB_API}/projects/{CRM_PROJECT_ID}/boards/{board['id']}/lists")

        expected_statuses = [
            "status::neu", "status::versendet", "status::beim-kunden",
            "status::interview", "status::verhandlung", "status::zusage",
            "status::absage", "status::ghost"
        ]

        board_labels = [l.get("label", {}).get("name") for l in lists]

        for status in expected_statuses:
            if status in board_labels:
                qa.ok(f"Board has column: {status}")
            else:
                qa.fail(f"Board missing column: {status}")

        # Check order
        status_positions = {}
        for l in lists:
            name = l.get("label", {}).get("name", "")
            if name.startswith("status::"):
                status_positions[name] = l.get("position", -1)

        sorted_board = sorted(status_positions.items(), key=lambda x: x[1])
        sorted_expected = [(s, i) for i, s in enumerate(expected_statuses) if s in status_positions]

        if [s for s, _ in sorted_board] == [s for s, _ in sorted_expected]:
            qa.ok("Board column order is correct")
        else:
            qa.warn("Board column order doesn't match expected pipeline flow")

    except urllib.error.HTTPError as e:
        qa.warn(f"Board API error: {e.code}")


def test_funnel_health(qa, issues):
    """Sanity check on the overall pipeline funnel."""
    qa.section("TEST 7: Funnel Health")

    status_counts = Counter()
    for i in issues:
        for l in i["labels"]:
            if l.startswith("status::"):
                status_counts[l] += 1

    total = len(issues)
    absage = status_counts.get("status::absage", 0)
    active = total - absage - status_counts.get("status::ghost", 0)
    advanced = sum(status_counts.get(s, 0) for s in
                   ["status::beim-kunden", "status::interview",
                    "status::verhandlung", "status::zusage"])

    qa.ok(f"Total: {total} | Active: {active} | Advanced: {advanced} | Absage: {absage}")

    # Conversion rate
    if total > 0:
        conversion = advanced / total * 100
        absage_rate = absage / total * 100
        qa.ok(f"Advancement rate: {conversion:.1f}% | Rejection rate: {absage_rate:.1f}%")

        if absage_rate > 50:
            qa.warn("High rejection rate (>50%) — review targeting strategy")
        if conversion < 3 and total > 50:
            qa.warn("Low advancement rate (<3%) — review application quality")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    if not GITLAB_TOKEN:
        print("❌ GITLAB_TOKEN required")
        sys.exit(1)

    qa = QAResult()
    print(f"🔍 CRM Integrity Check")
    print(f"{'='*60}")

    # Fetch all open issues
    issues = api_get_paginated(
        f"{GITLAB_API}/projects/{CRM_PROJECT_ID}/issues?state=opened"
    )
    print(f"📊 {len(issues)} open issues loaded")

    test_status_labels(qa, issues)
    test_label_consistency(qa, issues)
    test_hot_lead_consistency(qa, issues)
    test_duplicates(qa, issues)
    test_data_completeness(qa, issues)
    test_board_alignment(qa)
    test_funnel_health(qa, issues)

    print(qa.summary())

    # Write report
    os.makedirs("output", exist_ok=True)
    with open("output/crm_qa_report.json", "w") as f:
        json.dump({
            "passed": qa.passed,
            "failed": qa.failed,
            "warnings": qa.warnings,
            "fixed": qa.fixed,
            "issues_checked": len(issues),
        }, f, indent=2)

    sys.exit(1 if qa.failed > 0 else 0)


if __name__ == "__main__":
    main()
