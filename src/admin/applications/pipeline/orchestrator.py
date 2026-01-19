#!/usr/bin/env python3
"""
FREELANCER PIPELINE
===================
Orchestriert den kompletten Workflow:
1. Crawl → Projekte von Portalen holen
2. Match → Gegen Profile scoren
3. Draft → Gmail-Entwürfe erstellen

Usage:
    python pipeline.py                    # Interaktiver Modus
    python pipeline.py --auto             # Vollautomatisch
    python pipeline.py --crawl-only       # Nur crawlen
    python pipeline.py --match-only       # Nur matchen (braucht projects.json)
    python pipeline.py --draft-only       # Nur drafts (braucht matches.json)

Scheduled (via cron/GitLab CI):
    python pipeline.py --auto --notify    # Mit Email-Benachrichtigung
"""

import os
import sys
import json
import argparse
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Lokale Imports
from crawler import ProjectCrawler, Project
from matcher import ProjectMatcher, MatchResult, format_result
from drafter import create_drafts_batch, generate_email
from profiles import PROFILES, WOLFRAM, IAN, MICHAEL

# ══════════════════════════════════════════════════════════════════════════════
# KONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

ROOT_DIR = Path(__file__).parent
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Standard-Keywords für die Suche
DEFAULT_KEYWORD_SETS = [
    # Wolfram
    ["DevOps", "Kubernetes", "AWS"],
    ["Java", "Spring Boot", "Architekt"],
    ["Python", "Cloud", "Terraform"],
    ["AI", "ML", "MLOps"],
    
    # Ian
    ["LLM", "RAG", "Python"],
    ["Machine Learning", "PyTorch"],
    ["AI Engineer", "NLP"],
    
    # Michael
    ["Project Manager", "Technical"],
    ["Digital Transformation"],
]

# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE SCHRITTE
# ══════════════════════════════════════════════════════════════════════════════

def step_crawl(keyword_sets: List[List[str]] = None,
               portals: List[str] = None,
               remote_only: bool = True) -> List[Project]:
    """
    Schritt 1: Projekte crawlen.
    """
    print("\n" + "="*60)
    print("🔍 SCHRITT 1: CRAWLING")
    print("="*60)
    
    if keyword_sets is None:
        keyword_sets = DEFAULT_KEYWORD_SETS
    
    crawler = ProjectCrawler()
    projects = crawler.crawl_with_keywords(
        keyword_sets,
        portals=portals,
        remote_only=remote_only,
        only_new=True,
    )
    
    # Speichern
    output_file = OUTPUT_DIR / f"projects_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in projects], f, indent=2, ensure_ascii=False)
    
    # Symlink auf latest
    latest = OUTPUT_DIR / "projects_latest.json"
    if latest.exists():
        latest.unlink()
    latest.symlink_to(output_file.name)
    
    print(f"\n✅ {len(projects)} Projekte gecrawlt")
    print(f"   💾 {output_file}")
    
    return projects


def step_match(projects: List[Project] = None,
               min_percentage: int = 40,
               include_teams: bool = True) -> List[MatchResult]:
    """
    Schritt 2: Projekte matchen.
    """
    print("\n" + "="*60)
    print("📊 SCHRITT 2: MATCHING")
    print("="*60)
    
    # Projekte laden wenn nicht übergeben
    if projects is None:
        latest = OUTPUT_DIR / "projects_latest.json"
        if not latest.exists():
            print("❌ Keine Projekte gefunden. Erst crawlen!")
            return []
        
        with open(latest) as f:
            data = json.load(f)
            projects = [Project(**p) for p in data]
    
    print(f"   Matche {len(projects)} Projekte...")
    
    matcher = ProjectMatcher()
    results = matcher.match_projects(
        projects,
        include_teams=include_teams,
        min_percentage=min_percentage,
    )
    
    # Zusammenfassung
    summary = matcher.get_summary(results)
    print(f"\n   📈 Ergebnisse:")
    print(f"      🔥 HOT:   {summary['by_recommendation'].get('HOT', 0)}")
    print(f"      ✅ GOOD:  {summary['by_recommendation'].get('GOOD', 0)}")
    print(f"      🤔 MAYBE: {summary['by_recommendation'].get('MAYBE', 0)}")
    
    # Speichern
    output_file = OUTPUT_DIR / f"matches_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in results], f, indent=2, ensure_ascii=False, default=str)
    
    # Symlink
    latest = OUTPUT_DIR / "matches_latest.json"
    if latest.exists():
        latest.unlink()
    latest.symlink_to(output_file.name)
    
    # Auch Drafter-Format speichern
    drafter_file = OUTPUT_DIR / "for_drafter.json"
    drafter_data = []
    for r in results:
        drafter_data.append({
            "project_id": r.project.id,
            "project_title": r.project.title,
            "project_url": r.project.url,
            "portal": r.project.portal,
            "profile_key": r.profile_key,
            "profile_name": r.profile_name,
            "is_team": r.is_team,
            "percentage": r.percentage,
            "recommendation": r.recommendation,
            "contact_email": r.project.contact_email,
            "contact_name": r.project.contact_name,
        })
    with open(drafter_file, "w", encoding="utf-8") as f:
        json.dump(drafter_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(results)} Matches gefunden")
    print(f"   💾 {output_file}")
    
    return results


def step_draft(matches: List[Dict] = None,
               dry_run: bool = False,
               hot_only: bool = False,
               max_drafts: int = 10) -> int:
    """
    Schritt 3: Gmail Drafts erstellen.
    """
    print("\n" + "="*60)
    print("📧 SCHRITT 3: DRAFTING")
    print("="*60)
    
    # Matches laden wenn nicht übergeben
    if matches is None:
        drafter_file = OUTPUT_DIR / "for_drafter.json"
        if not drafter_file.exists():
            print("❌ Keine Matches gefunden. Erst matchen!")
            return 0
        
        with open(drafter_file) as f:
            matches = json.load(f)
    
    # Filtern
    if hot_only:
        matches = [m for m in matches if m.get("recommendation") == "HOT"]
    
    print(f"   Erstelle Drafts für {min(len(matches), max_drafts)} Matches...")
    if dry_run:
        print("   (DRY RUN - keine echten Drafts)")
    
    created = create_drafts_batch(matches, dry_run=dry_run, max_drafts=max_drafts)
    
    print(f"\n✅ {created} Drafts {'würden erstellt' if dry_run else 'erstellt'}")
    
    return created


# ══════════════════════════════════════════════════════════════════════════════
# VOLLSTÄNDIGE PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_full_pipeline(dry_run: bool = False,
                      hot_only: bool = False,
                      min_percentage: int = 50,
                      max_drafts: int = 10,
                      fetch_details: bool = True) -> Dict:
    """
    Führt die komplette Pipeline VOLLAUTOMATISCH aus.
    
    1. Crawl: Projekte von allen Portalen holen (mit Details!)
    2. Match: Gegen alle Profile scoren
    3. Draft: Gmail-Entwürfe mit Attachments erstellen
    
    Returns:
        Dict mit Statistiken
    """
    print("\n" + "🚀"*30)
    print("   FREELANCER PIPELINE - VOLLAUTOMATISCH")
    print("🚀"*30)
    print(f"   Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Min Score: {min_percentage}%")
    print(f"   Max Drafts: {max_drafts}")
    print(f"   Dry-Run: {dry_run}")
    
    stats = {
        "started": datetime.now().isoformat(),
        "projects_crawled": 0,
        "matches_found": 0,
        "hot_matches": 0,
        "good_matches": 0,
        "drafts_created": 0,
    }
    
    # ══════════════════════════════════════════════════════════════
    # 1. CRAWL - Projekte von allen Portalen
    # ══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("🔍 SCHRITT 1: CRAWLING")
    print("="*60)
    
    crawler = ProjectCrawler()
    projects = crawler.crawl_with_keywords(
        DEFAULT_KEYWORD_SETS,
        portals=None,  # Alle Portale
        remote_only=True,
        only_new=False,  # Auch bekannte, für besseres Matching
    )
    
    stats["projects_crawled"] = len(projects)
    
    if not projects:
        print("\n⚠️  Keine Projekte gefunden. Pipeline beendet.")
        return stats
    
    # Speichern
    output_file = OUTPUT_DIR / f"projects_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in projects], f, indent=2, ensure_ascii=False)
    print(f"\n   💾 {len(projects)} Projekte → {output_file.name}")
    
    # ══════════════════════════════════════════════════════════════
    # 2. MATCH - Gegen alle Profile scoren
    # ══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("📊 SCHRITT 2: MATCHING")
    print("="*60)
    
    matcher = ProjectMatcher()
    results = matcher.match_projects(
        projects,
        include_teams=True,
        min_percentage=min_percentage,
    )
    
    # Nur beste Matches pro Projekt (nicht 7x das gleiche Projekt)
    seen_projects = set()
    unique_results = []
    for r in results:
        if r.project.id not in seen_projects:
            seen_projects.add(r.project.id)
            unique_results.append(r)
    
    results = unique_results
    
    # Statistiken
    stats["matches_found"] = len(results)
    stats["hot_matches"] = sum(1 for r in results if r.recommendation == "HOT")
    stats["good_matches"] = sum(1 for r in results if r.recommendation == "GOOD")
    
    print(f"\n   📈 {len(results)} einzigartige Matches:")
    print(f"      🔥 HOT:  {stats['hot_matches']}")
    print(f"      ✅ GOOD: {stats['good_matches']}")
    
    if not results:
        print("\n⚠️  Keine Matches gefunden. Pipeline beendet.")
        return stats
    
    # Filter: Nur HOT wenn gewünscht
    if hot_only:
        results = [r for r in results if r.recommendation == "HOT"]
        print(f"\n   → Nur HOT: {len(results)} Matches")
    
    # Speichern
    matches_file = OUTPUT_DIR / f"matches_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(matches_file, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in results], f, indent=2, ensure_ascii=False, default=str)
    
    # ══════════════════════════════════════════════════════════════
    # 3. DRAFT - Gmail-Entwürfe erstellen
    # ══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("📧 SCHRITT 3: DRAFTING")
    print("="*60)
    
    # Konvertiere zu Drafter-Format
    matches_for_drafter = []
    for r in results[:max_drafts]:
        matches_for_drafter.append({
            "project_id": r.project.id,
            "project_title": r.project.title,
            "project_url": r.project.url,
            "portal": r.project.portal,
            "profile_key": r.profile_key,
            "profile_name": r.profile_name,
            "is_team": r.is_team,
            "percentage": r.percentage,
            "recommendation": r.recommendation,
            "contact_email": r.project.contact_email,
            "contact_name": r.project.contact_name,
        })
    
    print(f"\n   Erstelle {len(matches_for_drafter)} Drafts...")
    if dry_run:
        print("   (DRY RUN - keine echten Drafts)")
    
    created = create_drafts_batch(matches_for_drafter, dry_run=dry_run, max_drafts=max_drafts)
    stats["drafts_created"] = created
    
    # ══════════════════════════════════════════════════════════════
    # ZUSAMMENFASSUNG
    # ══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("📊 PIPELINE ABGESCHLOSSEN")
    print("="*60)
    print(f"   🔍 Projekte gecrawlt:  {stats['projects_crawled']}")
    print(f"   📊 Matches gefunden:   {stats['matches_found']}")
    print(f"      🔥 HOT:             {stats['hot_matches']}")
    print(f"      ✅ GOOD:            {stats['good_matches']}")
    print(f"   📧 Drafts erstellt:    {stats['drafts_created']}")
    print("="*60)
    
    if not dry_run and created > 0:
        print("\n   📬 Öffne Gmail Drafts...")
        webbrowser.open("https://mail.google.com/mail/#drafts")
    
    stats["finished"] = datetime.now().isoformat()
    
    # Stats speichern
    stats_file = OUTPUT_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)
    
    return stats


# ══════════════════════════════════════════════════════════════════════════════
# INTERAKTIVER MODUS
# ══════════════════════════════════════════════════════════════════════════════

def interactive_mode():
    """Interaktives Menü."""
    while True:
        print("\n" + "="*60)
        print("   FREELANCER PIPELINE - HAUPTMENÜ")
        print("="*60)
        print("""
   1. 🔍 Projekte crawlen
   2. 📊 Projekte matchen
   3. 📧 Gmail Drafts erstellen
   4. 🚀 Komplette Pipeline (1→2→3)
   5. 📋 Letzte Ergebnisse anzeigen
   
   q. Beenden
""")
        
        choice = input("Auswahl: ").strip().lower()
        
        if choice == "q":
            print("\n👋 Auf Wiedersehen!")
            break
        elif choice == "1":
            step_crawl()
        elif choice == "2":
            step_match()
        elif choice == "3":
            dry = input("Dry-Run? (j/N): ").strip().lower() == "j"
            step_draft(dry_run=dry)
        elif choice == "4":
            dry = input("Dry-Run? (j/N): ").strip().lower() == "j"
            run_full_pipeline(dry_run=dry)
        elif choice == "5":
            show_latest_results()
        else:
            print("❌ Ungültige Auswahl")


def show_latest_results():
    """Zeigt die letzten Ergebnisse an."""
    matches_file = OUTPUT_DIR / "matches_latest.json"
    
    if not matches_file.exists():
        print("❌ Keine Ergebnisse vorhanden")
        return
    
    with open(matches_file) as f:
        data = json.load(f)
    
    print(f"\n📋 Letzte Matches ({len(data)} Einträge):\n")
    
    for i, m in enumerate(data[:15], 1):
        icon = {"HOT": "🔥", "GOOD": "✅", "MAYBE": "🤔"}.get(m.get("recommendation"), "❓")
        pct = m.get("percentage", 0)
        title = m.get("project", {}).get("title", "")[:50]
        profile = m.get("profile_name", "")
        
        print(f"   {i:2}. {icon} [{pct}%] {title}")
        print(f"       👤 {profile}")
    
    if len(data) > 15:
        print(f"\n   ... und {len(data) - 15} weitere")


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Freelancer Pipeline - Vollautomatisch")
    parser.add_argument("--auto", action="store_true", help="Vollautomatisch (keine Interaktion)")
    parser.add_argument("--crawl-only", action="store_true", help="Nur crawlen")
    parser.add_argument("--match-only", action="store_true", help="Nur matchen")
    parser.add_argument("--draft-only", action="store_true", help="Nur drafts")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Keine echten Drafts erstellen")
    parser.add_argument("--hot-only", action="store_true", help="Nur HOT Matches (70%+)")
    parser.add_argument("--min-score", type=int, default=50, help="Minimum Match-Prozent (default: 50)")
    parser.add_argument("--max-drafts", type=int, default=10, help="Max Drafts (default: 10)")
    parser.add_argument("--keywords", "-k", help="Zusätzliche Keywords (kommasepariert)")
    
    args = parser.parse_args()
    
    # Einzelne Schritte
    if args.crawl_only:
        keywords = None
        if args.keywords:
            keywords = [kw.strip().split() for kw in args.keywords.split(",")]
        step_crawl(keyword_sets=keywords)
        return
    
    if args.match_only:
        step_match(min_percentage=args.min_score)
        return
    
    if args.draft_only:
        step_draft(dry_run=args.dry_run, hot_only=args.hot_only, max_drafts=args.max_drafts)
        return
    
    # Auto-Modus: Vollautomatische Pipeline
    if args.auto:
        run_full_pipeline(
            dry_run=args.dry_run,
            hot_only=args.hot_only,
            min_percentage=args.min_score,
            max_drafts=args.max_drafts,
        )
        return
    
    # Interaktiver Modus
    interactive_mode()


if __name__ == "__main__":
    main()
