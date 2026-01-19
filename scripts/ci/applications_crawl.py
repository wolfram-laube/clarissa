#!/usr/bin/env python3
"""
Applications Pipeline - Crawl Job
Crawls freelancermap.de for projects
"""

import os
import sys
import json

sys.path.insert(0, os.getcwd())

from src.admin.applications.pipeline.crawler import FreelancermapScraper

def main():
    keywords = os.environ.get("KEYWORDS", "DevOps,Python,AI").split(",")
    min_remote = int(os.environ.get("MIN_REMOTE", "50"))
    max_pages = int(os.environ.get("MAX_PAGES", "2"))
    
    scraper = FreelancermapScraper()
    all_projects = []
    
    for kw in keywords:
        kw = kw.strip()
        print(f"🔍 Searching: {kw}")
        try:
            projects = scraper.search(kw, max_pages=max_pages)
            # Filter by remote percentage
            projects = [p for p in projects if p.get("remote_percent", 0) >= min_remote]
            all_projects.extend(projects)
            print(f"   → {len(projects)} found")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Deduplicate by URL
    seen = set()
    unique = []
    for p in all_projects:
        url = p.get("url") or p.get("link", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(p)
    
    os.makedirs("output", exist_ok=True)
    with open("output/projects.json", "w") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(unique)} unique projects saved to output/projects.json")

if __name__ == "__main__":
    main()
