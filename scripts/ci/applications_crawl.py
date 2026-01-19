#!/usr/bin/env python3
"""
Applications Pipeline - Crawl Job
Crawls freelancermap.de for projects
"""

import os
import sys
import json
import re
import time

sys.path.insert(0, os.getcwd())

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "de-DE,de;q=0.9",
}

def crawl_freelancermap(keyword, max_pages=2):
    """Crawlt freelancermap.de nach Projekten."""
    projects = []
    base_url = "https://www.freelancermap.de/projektboerse.html"
    
    for page in range(1, max_pages + 1):
        print(f"  📄 Seite {page}...")
        params = {"query": keyword, "sort": "1", "pagenr": page}
        
        try:
            resp = requests.get(base_url, headers=HEADERS, params=params, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            
            cards = soup.select("div.project-card")
            if not cards:
                break
                
            for card in cards:
                project = parse_card(card)
                if project:
                    projects.append(project)
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"  ❌ Error page {page}: {e}")
            break
    
    return projects

def parse_card(card):
    """Parst eine Projekt-Karte."""
    try:
        # Titel & URL
        title_elem = card.select_one("a[data-id='project-card-title'], a[href*='/projekt/']")
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        url = "https://www.freelancermap.de" + title_elem.get("href", "")
        
        # Company
        company_elem = card.select_one("div.project-info > div:first-child")
        company = company_elem.get_text(strip=True) if company_elem else ""
        
        # Location
        city_elem = card.select_one("[data-testid='city'] a, a[data-id='project-card-city']")
        location = city_elem.get_text(strip=True).rstrip(", ") if city_elem else ""
        
        # Remote %
        remote_elem = card.select_one("[data-testid='remoteInPercent']")
        remote_percent = 0
        if remote_elem:
            text = remote_elem.get_text()
            match = re.search(r"(\d+)\s*%", text)
            if match:
                remote_percent = int(match.group(1))
        
        # Duration
        duration_elem = card.select_one("[data-testid='duration']")
        duration = duration_elem.get_text(strip=True) if duration_elem else ""
        
        # Start
        start_elem = card.select_one("[data-testid='beginningMonth']")
        start_date = start_elem.get_text(strip=True) if start_elem else ""
        
        return {
            "title": title,
            "url": url,
            "company": company,
            "location": location,
            "remote_percent": remote_percent,
            "duration": duration,
            "start_date": start_date,
            "source": "freelancermap",
        }
        
    except Exception as e:
        print(f"    ⚠️ Parse error: {e}")
        return None

def main():
    keywords = os.environ.get("KEYWORDS", "DevOps,Python,AI").split(",")
    min_remote = int(os.environ.get("MIN_REMOTE", "0"))  # Default 0 = alle
    max_pages = int(os.environ.get("MAX_PAGES", "2"))
    
    all_projects = []
    
    for kw in keywords:
        kw = kw.strip()
        print(f"🔍 Searching: {kw}")
        
        projects = crawl_freelancermap(kw, max_pages=max_pages)
        print(f"   → {len(projects)} raw results")
        
        # Filter by remote
        if min_remote > 0:
            projects = [p for p in projects if p.get("remote_percent", 0) >= min_remote]
            print(f"   → {len(projects)} after remote filter (>={min_remote}%)")
        
        all_projects.extend(projects)
    
    # Deduplicate
    seen = set()
    unique = []
    for p in all_projects:
        if p["url"] not in seen:
            seen.add(p["url"])
            unique.append(p)
    
    os.makedirs("output", exist_ok=True)
    with open("output/projects.json", "w") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(unique)} unique projects saved to output/projects.json")
    
    # Show top 5
    for p in unique[:5]:
        print(f"  • {p['title'][:50]}... ({p['remote_percent']}% remote)")

if __name__ == "__main__":
    main()
