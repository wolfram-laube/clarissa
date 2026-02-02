#!/usr/bin/env python3
"""
Applications Pipeline QA — Validates crawl & match outputs before Gmail drafts.

Tests:
  1. Crawl output: valid JSON, schema, reasonable counts
  2. Match output: valid JSON, scores in range, required fields
  3. CRM dedup: flags projects already tracked as GitLab Issues
  4. Data quality: rate parseable, remote %, no empty titles

Exit codes:
  0 = all checks passed
  1 = critical failure (blocks pipeline)
  2 = warnings only (non-blocking)

Usage:
  python3 applications_qa.py                    # validate crawl + match
  python3 applications_qa.py --crm-dedup        # also check CRM duplicates
  python3 applications_qa.py --report-only      # warnings don't block
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════

CRAWL_OUTPUT = os.environ.get("CRAWL_OUTPUT", "output/projects.json")
MATCH_OUTPUT = os.environ.get("MATCH_OUTPUT", "output/matches.json")
CRM_PROJECT_ID = int(os.environ.get("CRM_PROJECT_ID", "78171527"))
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN", "")
GITLAB_API = "https://gitlab.com/api/v4"
CRM_DEDUP = "--crm-dedup" in sys.argv
REPORT_ONLY = "--report-only" in sys.argv

# ═══════════════════════════════════════════════════════════════
# TEST INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════

class QAResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
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

    def section(self, title):
        self.details.append(f"\n━━━ {title} ━━━")

    def summary(self):
        self.details.append(f"\n{'='*60}")
        total = self.passed + self.failed + self.warnings
        self.details.append(
            f"  QA: {self.passed}/{total} passed, "
            f"{self.failed} failed, {self.warnings} warnings"
        )
        if self.failed == 0:
            self.details.append(f"  🟢 PIPELINE OK")
        elif REPORT_ONLY:
            self.details.append(f"  🟡 WARNINGS (report-only mode, not blocking)")
        else:
            self.details.append(f"  🔴 PIPELINE BLOCKED — fix issues before drafts")
        return "\n".join(self.details)

    @property
    def exit_code(self):
        if self.failed > 0 and not REPORT_ONLY:
            return 1
        if self.warnings > 0:
            return 2
        return 0


# ═══════════════════════════════════════════════════════════════
# TEST 1: CRAWL OUTPUT VALIDATION
# ═══════════════════════════════════════════════════════════════

def test_crawl(qa):
    qa.section("TEST 1: Crawl Output")

    if not os.path.exists(CRAWL_OUTPUT):
        qa.fail(f"Crawl output not found: {CRAWL_OUTPUT}")
        return None

    try:
        with open(CRAWL_OUTPUT) as f:
            data = json.load(f)
        qa.ok(f"Valid JSON ({os.path.getsize(CRAWL_OUTPUT)} bytes)")
    except json.JSONDecodeError as e:
        qa.fail(f"Invalid JSON: {e}")
        return None

    # Must be a list
    if not isinstance(data, list):
        qa.fail(f"Expected list, got {type(data).__name__}")
        return None
    qa.ok(f"{len(data)} projects crawled")

    # Reasonable count
    if len(data) == 0:
        qa.fail("No projects crawled — crawler may be broken or blocked")
        return data
    elif len(data) < 10:
        qa.warn(f"Only {len(data)} projects — unusually low")
    elif len(data) > 500:
        qa.warn(f"{len(data)} projects — unusually high, check for pagination bug")
    else:
        qa.ok(f"Reasonable project count ({len(data)})")

    # Schema validation
    required_fields = ["title", "url"]
    optional_fields = ["description", "location", "remote", "start", "duration", "rate"]
    
    missing_required = 0
    empty_titles = 0
    has_description = 0
    has_rate = 0
    
    for i, project in enumerate(data):
        if not isinstance(project, dict):
            qa.fail(f"Project #{i} is not a dict")
            continue
        for field in required_fields:
            if field not in project or not project[field]:
                missing_required += 1
        if not project.get("title", "").strip():
            empty_titles += 1
        if project.get("description"):
            has_description += 1
        if project.get("rate"):
            has_rate += 1

    if missing_required == 0:
        qa.ok("All projects have required fields (title, url)")
    else:
        qa.fail(f"{missing_required} projects missing required fields")

    if empty_titles == 0:
        qa.ok("No empty titles")
    else:
        qa.warn(f"{empty_titles} projects with empty titles")

    desc_pct = has_description / len(data) * 100 if data else 0
    if desc_pct > 70:
        qa.ok(f"Description coverage: {desc_pct:.0f}%")
    else:
        qa.warn(f"Low description coverage: {desc_pct:.0f}% — detail fetch may have failed")

    # Duplicate URLs
    urls = [p.get("url", "") for p in data]
    unique_urls = set(urls)
    if len(urls) == len(unique_urls):
        qa.ok("No duplicate URLs")
    else:
        dupes = len(urls) - len(unique_urls)
        qa.warn(f"{dupes} duplicate URLs in crawl output")

    return data


# ═══════════════════════════════════════════════════════════════
# TEST 2: MATCH OUTPUT VALIDATION
# ═══════════════════════════════════════════════════════════════

def test_match(qa):
    qa.section("TEST 2: Match Output")

    if not os.path.exists(MATCH_OUTPUT):
        qa.fail(f"Match output not found: {MATCH_OUTPUT}")
        return None

    try:
        with open(MATCH_OUTPUT) as f:
            data = json.load(f)
        qa.ok(f"Valid JSON ({os.path.getsize(MATCH_OUTPUT)} bytes)")
    except json.JSONDecodeError as e:
        qa.fail(f"Invalid JSON: {e}")
        return None

    # Must be a dict with profile keys
    if not isinstance(data, dict):
        qa.fail(f"Expected dict, got {type(data).__name__}")
        return None

    expected_profiles = ["wolfram", "ian", "michael"]
    for profile in expected_profiles:
        if profile not in data:
            qa.warn(f"Profile '{profile}' missing from match output")
        else:
            matches = data[profile]
            if not isinstance(matches, list):
                qa.fail(f"Profile '{profile}': expected list, got {type(matches).__name__}")
                continue
            
            qa.ok(f"Profile '{profile}': {len(matches)} matches")

            # Validate scores
            bad_scores = 0
            no_title = 0
            for m in matches:
                score = m.get("score", -1)
                if not (0 <= score <= 100):
                    bad_scores += 1
                if not m.get("title"):
                    no_title += 1

            if bad_scores > 0:
                qa.fail(f"Profile '{profile}': {bad_scores} matches with invalid scores")
            if no_title > 0:
                qa.warn(f"Profile '{profile}': {no_title} matches without title")

            # Check score distribution
            if matches:
                scores = [m.get("score", 0) for m in matches]
                avg = sum(scores) / len(scores)
                hot = sum(1 for s in scores if s >= 70)
                qa.ok(f"Profile '{profile}': avg score {avg:.0f}%, {hot} HOT (≥70%)")

    return data


# ═══════════════════════════════════════════════════════════════
# TEST 3: CRM DUPLICATE CHECK
# ═══════════════════════════════════════════════════════════════

def test_crm_dedup(qa, match_data):
    qa.section("TEST 3: CRM Duplicate Check")

    if not CRM_DEDUP:
        qa.ok("CRM dedup skipped (use --crm-dedup to enable)")
        return

    if not GITLAB_TOKEN:
        qa.warn("GITLAB_TOKEN not set — cannot check CRM")
        return

    if not match_data:
        qa.warn("No match data to check against CRM")
        return

    # Fetch all open CRM issue titles
    crm_titles = set()
    page = 1
    while True:
        try:
            req = urllib.request.Request(
                f"{GITLAB_API}/projects/{CRM_PROJECT_ID}/issues?"
                f"state=opened&per_page=100&page={page}",
                headers={"PRIVATE-TOKEN": GITLAB_TOKEN}
            )
            issues = json.loads(urllib.request.urlopen(req).read())
            if not issues:
                break
            for i in issues:
                # Extract project name from "[Agency] Project Title" format
                title = i["title"]
                if "] " in title:
                    title = title.split("] ", 1)[1]
                crm_titles.add(title.lower().strip())
            page += 1
        except urllib.error.HTTPError as e:
            qa.warn(f"CRM API error: {e.code}")
            return

    qa.ok(f"Loaded {len(crm_titles)} open CRM issues")

    # Check each match profile for duplicates
    total_dupes = 0
    for profile, matches in match_data.items():
        if not isinstance(matches, list):
            continue
        dupes = []
        for m in matches:
            title = m.get("title", "").lower().strip()
            # Fuzzy: check if CRM already has something very similar
            for crm_t in crm_titles:
                # Exact match or significant overlap
                if title == crm_t:
                    dupes.append(m.get("title", "?"))
                    break
                # Check if >60% of words overlap
                title_words = set(title.split())
                crm_words = set(crm_t.split())
                if title_words and crm_words:
                    overlap = len(title_words & crm_words) / max(len(title_words), len(crm_words))
                    if overlap > 0.6:
                        dupes.append(f"{m.get('title', '?')} ≈ CRM")
                        break

        if dupes:
            total_dupes += len(dupes)
            qa.warn(f"Profile '{profile}': {len(dupes)} matches already in CRM")
            for d in dupes[:3]:
                qa.details.append(f"       → {d[:60]}")

    if total_dupes == 0:
        qa.ok("No duplicates with existing CRM issues")
    else:
        qa.warn(f"Total: {total_dupes} potential CRM duplicates — review before sending")


# ═══════════════════════════════════════════════════════════════
# TEST 4: DATA QUALITY
# ═══════════════════════════════════════════════════════════════

def test_data_quality(qa, crawl_data):
    qa.section("TEST 4: Data Quality")

    if not crawl_data:
        qa.warn("No crawl data for quality check")
        return

    # Rate parseability
    parseable_rates = 0
    total_with_rate = 0
    for p in crawl_data:
        rate = p.get("rate", "")
        if rate:
            total_with_rate += 1
            if re.search(r'\d+', str(rate)):
                parseable_rates += 1

    if total_with_rate > 0:
        pct = parseable_rates / total_with_rate * 100
        if pct > 80:
            qa.ok(f"Rate parseability: {pct:.0f}% ({parseable_rates}/{total_with_rate})")
        else:
            qa.warn(f"Low rate parseability: {pct:.0f}%")
    else:
        qa.warn("No projects have rate information")

    # Remote field
    has_remote = sum(1 for p in crawl_data if p.get("remote") or p.get("location"))
    remote_pct = has_remote / len(crawl_data) * 100
    if remote_pct > 50:
        qa.ok(f"Remote/location coverage: {remote_pct:.0f}%")
    else:
        qa.warn(f"Low remote/location coverage: {remote_pct:.0f}%")

    # Title diversity (not all the same)
    titles = [p.get("title", "") for p in crawl_data]
    unique_ratio = len(set(titles)) / len(titles) if titles else 0
    if unique_ratio > 0.8:
        qa.ok(f"Title diversity: {unique_ratio:.0%} unique")
    else:
        qa.warn(f"Low title diversity: {unique_ratio:.0%} — possible crawl issue")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    qa = QAResult()
    print(f"🔍 Applications Pipeline QA")
    print(f"{'='*60}")

    crawl_data = test_crawl(qa)
    match_data = test_match(qa)
    test_crm_dedup(qa, match_data)
    test_data_quality(qa, crawl_data)

    print(qa.summary())

    # Write report as artifact
    report_path = "output/qa_report.json"
    os.makedirs("output", exist_ok=True)
    with open(report_path, "w") as f:
        json.dump({
            "passed": qa.passed,
            "failed": qa.failed,
            "warnings": qa.warnings,
            "details": qa.details,
            "exit_code": qa.exit_code,
        }, f, indent=2)
    print(f"\n📄 Report: {report_path}")

    sys.exit(qa.exit_code)


if __name__ == "__main__":
    main()
