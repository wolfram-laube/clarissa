#!/usr/bin/env python3
"""
Applications Pipeline - Match Job
Matches projects against all profile combinations
"""

import os
import sys
import json
from collections import defaultdict

sys.path.insert(0, os.getcwd())

from src.admin.applications.pipeline.profiles import PROFILES, TEAM_COMBOS

def match_project(project, profile):
    """Match ein Projekt gegen ein Profil."""
    # Kombiniere alle durchsuchbaren Texte
    search_text = " ".join([
        project.get("title", ""),
        project.get("description", ""),
        project.get("company", ""),
        " ".join(project.get("skills", [])),
    ]).lower()
    
    # Berechne Score
    result = profile.match_score(search_text)
    return result

def main():
    min_score = int(os.environ.get("MIN_SCORE", "40"))
    
    # Load projects
    with open("output/projects.json") as f:
        projects = json.load(f)
    
    print(f"📊 Matching {len(projects)} projects")
    print(f"   Against {len(PROFILES)} solo profiles + {len(TEAM_COMBOS)} team combos")
    print("=" * 70)
    
    # Results per profile
    results_by_profile = defaultdict(list)
    
    # Match gegen alle Profile
    all_profiles = {**PROFILES, **TEAM_COMBOS}
    
    for project in projects:
        project_title = project.get("title", "?")[:50]
        
        for profile_name, profile in all_profiles.items():
            result = match_project(project, profile)
            
            if result["percentage"] >= min_score and not result.get("excluded_by"):
                results_by_profile[profile_name].append({
                    "project": project,
                    "score": result["percentage"],
                    "matches": result["matches"],
                })
    
    # Output
    print()
    
    # Solo-Profile
    print("🧑 SOLO MATCHES")
    print("-" * 70)
    for name in ["wolfram", "ian", "michael"]:
        if name in results_by_profile:
            matches = sorted(results_by_profile[name], key=lambda x: -x["score"])
            print(f"\n{name.upper()} ({len(matches)} matches):")
            for m in matches[:5]:
                p = m["project"]
                print(f"  [{m['score']:3d}%] {p['title'][:45]}... ({p['remote_percent']}% remote)")
    
    # Team-Combos
    print()
    print("👥 TEAM MATCHES")
    print("-" * 70)
    for name in ["wolfram_ian", "wolfram_michael", "ian_michael", "wolfram_ian_michael"]:
        if name in results_by_profile:
            matches = sorted(results_by_profile[name], key=lambda x: -x["score"])
            display_name = name.replace("_", " + ").title()
            print(f"\n{display_name} ({len(matches)} matches):")
            for m in matches[:5]:
                p = m["project"]
                print(f"  [{m['score']:3d}%] {p['title'][:45]}... ({p['remote_percent']}% remote)")
    
    # Summary JSON
    output = {
        "total_projects": len(projects),
        "profiles": {}
    }
    
    for profile_name, matches in results_by_profile.items():
        sorted_matches = sorted(matches, key=lambda x: -x["score"])
        output["profiles"][profile_name] = {
            "count": len(matches),
            "top_matches": sorted_matches[:10]
        }
    
    os.makedirs("output", exist_ok=True)
    with open("output/matches.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    # Summary
    print()
    print("=" * 70)
    print("📊 ZUSAMMENFASSUNG")
    print("-" * 70)
    
    total_hot = 0
    for name, matches in results_by_profile.items():
        hot = sum(1 for m in matches if m["score"] >= 70)
        good = sum(1 for m in matches if 50 <= m["score"] < 70)
        total_hot += hot
        print(f"  {name:25s}: {len(matches):3d} total | 🔥 {hot:2d} HOT | ✅ {good:2d} GOOD")
    
    print()
    print(f"🔥 {total_hot} HOT matches (>=70%) über alle Profile!")
    print(f"✅ Saved to output/matches.json")

if __name__ == "__main__":
    main()
