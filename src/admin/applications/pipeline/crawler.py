#!/usr/bin/env python3
"""
PROJEKT-CRAWLER
===============
Scraped Freelance-Portale nach neuen Projekten.

Unterstützte Portale:
- freelancermap.de
- freelance.de
- gulp.de

Usage:
    python crawler.py
    python crawler.py --portal freelancermap --keywords "kubernetes devops"
    python crawler.py --all
"""

import re
import json
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, quote_plus

import requests
from bs4 import BeautifulSoup

# ══════════════════════════════════════════════════════════════════════════════
# KONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

# Cache für bereits gesehene Projekte
CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_FILE = CACHE_DIR / "seen_projects.json"

# Rate Limiting
REQUEST_DELAY = 2.0  # Sekunden zwischen Requests


# ══════════════════════════════════════════════════════════════════════════════
# DATENMODELL
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Project:
    """Ein gefundenes Freelance-Projekt."""
    id: str
    title: str
    portal: str
    url: str
    
    # Details
    company: str = ""
    location: str = ""
    remote: str = ""  # "100%", "50%", "vor Ort", etc.
    start_date: str = ""
    duration: str = ""
    rate: str = ""
    workload: str = ""  # "Vollzeit", "Teilzeit", "20h/Woche"
    
    # Beschreibung
    description: str = ""
    requirements: str = ""
    
    # Kontakt
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    
    # Meta
    posted_date: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def __hash__(self):
        return hash(self.id)
    
    @property
    def full_text(self) -> str:
        """Kombinierter Text für Matching."""
        return f"{self.title} {self.description} {self.requirements} {self.location}"


# ══════════════════════════════════════════════════════════════════════════════
# CACHE
# ══════════════════════════════════════════════════════════════════════════════

def load_cache() -> Set[str]:
    """Lädt gesehene Projekt-IDs."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                data = json.load(f)
                return set(data.get("seen_ids", []))
        except:
            pass
    return set()


def save_cache(seen_ids: Set[str]):
    """Speichert gesehene Projekt-IDs."""
    CACHE_DIR.mkdir(exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump({"seen_ids": list(seen_ids), "updated": datetime.now().isoformat()}, f)


# ══════════════════════════════════════════════════════════════════════════════
# FREELANCERMAP SCRAPER
# ══════════════════════════════════════════════════════════════════════════════

class FreelancermapScraper:
    """Scraper für freelancermap.de"""
    
    BASE_URL = "https://www.freelancermap.de"
    SEARCH_URL = "https://www.freelancermap.de/projektboerse.html"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def search(self, keywords: List[str] = None, remote_only: bool = True, 
               max_pages: int = 3) -> List[Project]:
        """Sucht Projekte auf freelancermap."""
        projects = []
        
        # Suchparameter
        params = {
            "sort": "1",  # Nach Datum sortiert
            "pagenr": 1,
        }
        
        if keywords:
            params["query"] = " ".join(keywords)
        
        if remote_only:
            params["remotePercent[100]"] = "100"
        
        for page in range(1, max_pages + 1):
            params["pagenr"] = page
            print(f"  📄 Seite {page}...")
            
            try:
                resp = self.session.get(self.SEARCH_URL, params=params, timeout=30)
                resp.raise_for_status()
                
                page_projects = self._parse_search_results(resp.text)
                if not page_projects:
                    break
                
                projects.extend(page_projects)
                time.sleep(REQUEST_DELAY)
                
            except Exception as e:
                print(f"  ❌ Fehler auf Seite {page}: {e}")
                break
        
        return projects
    
    def _parse_search_results(self, html: str) -> List[Project]:
        """Parst Suchergebnisse."""
        soup = BeautifulSoup(html, "html.parser")
        projects = []
        
        # Projekt-Karten finden
        cards = soup.select("div.project-card, div.card.project, article.project")
        
        if not cards:
            # Alternative Selektoren
            cards = soup.select("div[data-project-id], div.search-result")
        
        for card in cards:
            try:
                project = self._parse_project_card(card)
                if project:
                    projects.append(project)
            except Exception as e:
                print(f"    ⚠️ Parse-Fehler: {e}")
                continue
        
        return projects
    
    def _parse_project_card(self, card) -> Optional[Project]:
        """Parst eine Projekt-Karte."""
        # Titel und URL
        title_elem = card.select_one("a.project-title, h2 a, h3 a, a[href*='/projekt/']")
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        url = urljoin(self.BASE_URL, title_elem.get("href", ""))
        
        # ID aus URL extrahieren
        project_id = hashlib.md5(url.encode()).hexdigest()[:12]
        
        # Weitere Felder
        description = ""
        desc_elem = card.select_one("div.description, p.teaser, div.project-description")
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        
        # Remote-Status
        remote = ""
        remote_elem = card.select_one("span.remote, div.remote-info, *[class*='remote']")
        if remote_elem:
            remote = remote_elem.get_text(strip=True)
        elif "100% remote" in card.get_text().lower():
            remote = "100%"
        elif "remote" in card.get_text().lower():
            remote = "teilweise"
        
        # Location
        location = ""
        loc_elem = card.select_one("span.location, div.location, *[class*='location']")
        if loc_elem:
            location = loc_elem.get_text(strip=True)
        
        # Start/Duration
        start_date = ""
        duration = ""
        for text in card.stripped_strings:
            if "start" in text.lower() or "ab " in text.lower():
                start_date = text
            if "monat" in text.lower() or "jahr" in text.lower():
                duration = text
        
        return Project(
            id=f"fm_{project_id}",
            title=title,
            portal="freelancermap",
            url=url,
            description=description,
            remote=remote,
            location=location,
            start_date=start_date,
            duration=duration,
        )
    
    def get_details(self, project: Project) -> Project:
        """Lädt Detail-Informationen für ein Projekt."""
        try:
            resp = self.session.get(project.url, timeout=30)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Vollständige Beschreibung
            desc = soup.select_one("div.project-description, div.description-full")
            if desc:
                project.description = desc.get_text(strip=True)
            
            # Requirements
            req = soup.select_one("div.requirements, div.skills, ul.skill-list")
            if req:
                project.requirements = req.get_text(strip=True)
            
            # Kontakt
            contact = soup.select_one("div.contact-info, div.recruiter")
            if contact:
                name = contact.select_one("*[class*='name']")
                if name:
                    project.contact_name = name.get_text(strip=True)
            
            # Rate
            rate = soup.select_one("*[class*='rate'], *[class*='budget']")
            if rate:
                project.rate = rate.get_text(strip=True)
            
            time.sleep(REQUEST_DELAY)
            
        except Exception as e:
            print(f"    ⚠️ Details laden fehlgeschlagen: {e}")
        
        return project


# ══════════════════════════════════════════════════════════════════════════════
# FREELANCE.DE SCRAPER
# ══════════════════════════════════════════════════════════════════════════════

class FreelanceDeScraper:
    """Scraper für freelance.de"""
    
    BASE_URL = "https://www.freelance.de"
    SEARCH_URL = "https://www.freelance.de/search/project.php"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def search(self, keywords: List[str] = None, max_pages: int = 3) -> List[Project]:
        """Sucht Projekte auf freelance.de"""
        projects = []
        
        # Search URLs für verschiedene Kategorien
        search_urls = [
            f"{self.BASE_URL}/Projekte/K/IT-Entwicklung-Programmierung-0",
            f"{self.BASE_URL}/Projekte/K/IT-Architektur-Projektmanagement-0",
        ]
        
        if keywords:
            query = "+".join(keywords)
            search_urls = [f"{self.SEARCH_URL}?search_query={quote_plus(' '.join(keywords))}"]
        
        for search_url in search_urls:
            print(f"  🔍 {search_url[:60]}...")
            
            try:
                resp = self.session.get(search_url, timeout=30)
                resp.raise_for_status()
                
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Projekt-Links finden
                links = soup.select("a[href*='/Projekt/']")
                
                for link in links[:20]:  # Max 20 pro Kategorie
                    title = link.get_text(strip=True)
                    url = urljoin(self.BASE_URL, link.get("href", ""))
                    
                    if title and len(title) > 10:
                        project_id = hashlib.md5(url.encode()).hexdigest()[:12]
                        projects.append(Project(
                            id=f"fde_{project_id}",
                            title=title,
                            portal="freelance.de",
                            url=url,
                        ))
                
                time.sleep(REQUEST_DELAY)
                
            except Exception as e:
                print(f"  ❌ Fehler: {e}")
        
        return projects


# ══════════════════════════════════════════════════════════════════════════════
# GULP SCRAPER
# ══════════════════════════════════════════════════════════════════════════════

class GulpScraper:
    """Scraper für gulp.de"""
    
    BASE_URL = "https://www.gulp.de"
    SEARCH_URL = "https://www.gulp.de/gulp2/g/projekte"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def search(self, keywords: List[str] = None, max_pages: int = 2) -> List[Project]:
        """Sucht Projekte auf gulp.de"""
        projects = []
        
        # GULP nutzt viel JavaScript, daher limitiert
        search_url = self.SEARCH_URL
        if keywords:
            search_url += f"?q={quote_plus(' '.join(keywords))}"
        
        print(f"  🔍 GULP suchen...")
        
        try:
            resp = self.session.get(search_url, timeout=30)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Projekt-Elemente (GULP hat eine komplexe Struktur)
            cards = soup.select("div.project-card, article.project, div[class*='project']")
            
            for card in cards[:15]:
                title_elem = card.select_one("a[href*='projekt'], h2, h3")
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get("href", "")
                    url = urljoin(self.BASE_URL, href) if href else ""
                    
                    if title and len(title) > 5:
                        project_id = hashlib.md5((url or title).encode()).hexdigest()[:12]
                        projects.append(Project(
                            id=f"gulp_{project_id}",
                            title=title,
                            portal="gulp",
                            url=url,
                        ))
            
        except Exception as e:
            print(f"  ❌ GULP Fehler: {e}")
        
        return projects


# ══════════════════════════════════════════════════════════════════════════════
# HAUPT-CRAWLER
# ══════════════════════════════════════════════════════════════════════════════

class ProjectCrawler:
    """Kombinierter Crawler für alle Portale."""
    
    def __init__(self):
        self.scrapers = {
            "freelancermap": FreelancermapScraper(),
            "freelance.de": FreelanceDeScraper(),
            "gulp": GulpScraper(),
        }
        self.seen_ids = load_cache()
    
    def crawl(self, 
              portals: List[str] = None,
              keywords: List[str] = None,
              remote_only: bool = True,
              fetch_details: bool = False,
              only_new: bool = True) -> List[Project]:
        """
        Crawlt alle/ausgewählte Portale.
        
        Args:
            portals: Liste der Portale (None = alle)
            keywords: Suchbegriffe
            remote_only: Nur Remote-Projekte
            fetch_details: Details für jedes Projekt laden
            only_new: Nur noch nicht gesehene Projekte
        
        Returns:
            Liste von Projekten
        """
        if portals is None:
            portals = list(self.scrapers.keys())
        
        all_projects = []
        
        for portal in portals:
            if portal not in self.scrapers:
                print(f"⚠️ Unbekanntes Portal: {portal}")
                continue
            
            print(f"\n🔍 Crawle {portal}...")
            scraper = self.scrapers[portal]
            
            try:
                if portal == "freelancermap":
                    projects = scraper.search(keywords, remote_only=remote_only)
                else:
                    projects = scraper.search(keywords)
                
                print(f"   → {len(projects)} Projekte gefunden")
                
                # Neue filtern
                if only_new:
                    projects = [p for p in projects if p.id not in self.seen_ids]
                    print(f"   → {len(projects)} neue Projekte")
                
                # Details laden
                if fetch_details and hasattr(scraper, 'get_details'):
                    print(f"   → Lade Details...")
                    for i, p in enumerate(projects):
                        print(f"      [{i+1}/{len(projects)}] {p.title[:40]}...")
                        scraper.get_details(p)
                
                # IDs merken
                for p in projects:
                    self.seen_ids.add(p.id)
                
                all_projects.extend(projects)
                
            except Exception as e:
                print(f"   ❌ Fehler: {e}")
        
        # Cache speichern
        save_cache(self.seen_ids)
        
        return all_projects
    
    def crawl_with_keywords(self, keyword_sets: List[List[str]], **kwargs) -> List[Project]:
        """Crawlt mit mehreren Keyword-Sets."""
        all_projects = {}
        
        for keywords in keyword_sets:
            print(f"\n{'='*60}")
            print(f"Keywords: {', '.join(keywords)}")
            print(f"{'='*60}")
            
            projects = self.crawl(keywords=keywords, **kwargs)
            
            # Deduplizieren
            for p in projects:
                if p.id not in all_projects:
                    all_projects[p.id] = p
        
        return list(all_projects.values())


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Freelance-Portal Crawler")
    parser.add_argument("--portal", "-p", choices=["freelancermap", "freelance.de", "gulp", "all"],
                        default="all", help="Portal zum Crawlen")
    parser.add_argument("--keywords", "-k", help="Suchbegriffe (kommasepariert)")
    parser.add_argument("--remote", action="store_true", default=True, help="Nur Remote")
    parser.add_argument("--details", action="store_true", help="Details laden")
    parser.add_argument("--all-results", action="store_true", help="Auch bereits gesehene")
    parser.add_argument("--output", "-o", help="Output JSON-Datei")
    
    args = parser.parse_args()
    
    crawler = ProjectCrawler()
    
    portals = None if args.portal == "all" else [args.portal]
    keywords = args.keywords.split(",") if args.keywords else None
    
    print("🚀 Starte Crawler...")
    print(f"   Portale: {portals or 'alle'}")
    print(f"   Keywords: {keywords or 'keine'}")
    print(f"   Remote only: {args.remote}")
    
    projects = crawler.crawl(
        portals=portals,
        keywords=keywords,
        remote_only=args.remote,
        fetch_details=args.details,
        only_new=not args.all_results,
    )
    
    print(f"\n{'='*60}")
    print(f"✅ {len(projects)} Projekte gefunden")
    print(f"{'='*60}")
    
    for p in projects[:10]:
        print(f"\n📋 {p.title[:60]}")
        print(f"   🔗 {p.url}")
        print(f"   📍 {p.location or 'k.A.'} | 🏠 {p.remote or 'k.A.'}")
    
    if len(projects) > 10:
        print(f"\n... und {len(projects) - 10} weitere")
    
    # Output speichern
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in projects], f, indent=2, ensure_ascii=False)
        print(f"\n💾 Gespeichert: {args.output}")
    
    return projects


if __name__ == "__main__":
    main()
