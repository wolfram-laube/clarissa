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
            # Pass keywords as list, disable remote_only to get all projects
            projects = scraper.search(keywords=[kw], remote_only=False, max_pages=max_pages)
            print(f"   → {len(projects)} raw results")
            
            # Convert Project objects to dicts if needed
            project_dicts = []
            for p in projects:
                if hasattr(p, '__dict__'):
                    # It's a dataclass/object
                    d = {
                        'title': getattr(p, 'title', ''),
                        'url': getattr(p, 'url', ''),
                        'company': getattr(p, 'company', ''),
                        'location': getattr(p, 'location', ''),
                        'remote_percent': getattr(p, 'remote_percent', 0),
                        'rate': getattr(p, 'rate', ''),
                        'start_date': getattr(p, 'start_date', ''),
                        'duration': getattr(p, 'duration', ''),
                        'skills': getattr(p, 'skills', []),
                        'description': getattr(p, 'description', ''),
                    }
                    project_dicts.append(d)
                elif isinstance(p, dict):
                    project_dicts.append(p)
            
            # Filter by min remote percentage
            filtered = [p for p in project_dicts if p.get('remote_percent', 0) >= min_remote]
            print(f"   → {len(filtered)} after remote filter (>={min_remote}%)")
            
            all_projects.extend(filtered)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Deduplicate by URL
    seen = set()
    unique = []
    for p in all_projects:
        url = p.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(p)
    
    os.makedirs("output", exist_ok=True)
    with open("output/projects.json", "w") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(unique)} unique projects saved to output/projects.json")

if __name__ == "__main__":
    main()
