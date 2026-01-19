#!/usr/bin/env python3
"""
Applications Pipeline - Match Job
Matches projects against all profile combinations:
1. Wolfram, Ian, Michael (solo)
2. Wolfram+Ian, Wolfram+Michael, Ian+Michael (pairs)  
3. Wolfram+Ian+Michael (trio)
"""

import os
import sys
import json
from collections import defaultdict

sys.path.insert(0, os.getcwd())

from src.admin.applications.pipeline.profiles import PROFILES, TEAM_COMBOS, WOLFRAM, IAN, MICHAEL

def match_project(project, profile):
    """Match ein Projekt gegen ein Profil."""
    search_text = " ".join([
        project.get("title", ""),
        project.get("description", ""),
        project.get("company", ""),
        " ".join(project.get("skills", [])),
    ]).lower()
    
    return profile.match_score(search_text)

def main():
    min_score = int(os.environ.get("MIN_SCORE", "40"))
    
    # Load projects from crawl artifacts
    with open("output/projects.json") as f:
        projects = json.load(f)
    
    print(f"📊 Matching {len(projects)} projects (min score: {min_score}%)")
    print("=" * 70)
    
    # All profiles to match against
    all_profiles = {}
    
    # Solo profiles
    all_profiles["wolfram"] = WOLFRAM
    all_profiles["ian"] = IAN
    all_profiles["michael"] = MICHAEL
    
    # Add team combos if they exist
    if TEAM_COMBOS:
        all_profiles.update(TEAM_COMBOS)
    
    print(f"Profiles: {list(all_profiles.keys())}")
    print()
    
    # Results per profile
    results = defaultdict(list)
    
    for project in projects:
        for profile_name, profile in all_profiles.items():
            result = match_project(project, profile)
            
            if result["percentage"] >= min_score and not result.get("excluded_by"):
                results[profile_name].append({
                    "project": project,
                    "score": result["percentage"],
                    "matches": result["matches"],
                })
    
    # ═══════════════════════════════════════════════════════════════════
    # OUTPUT
    # ═══════════════════════════════════════════════════════════════════
    
    print("🧑 SOLO MATCHES")
    print("-" * 70)
    
    for name in ["wolfram", "ian", "michael"]:
        if name in results:
            matches = sorted(results[name], key=lambda x: -x["score"])
            print(f"\n{name.upper()} ({len(matches)} matches):")
            for m in matches[:5]:
                p = m["project"]
                kw = m["matches"].get("must_have", [])[:3]
                print(f"  [{m['score']:3d}%] {p['title'][:42]}... ({p['remote_percent']}%R)")
                if kw:
                    print(f"         Keywords: {', '.join(kw)}")
    
    print()
    print("👥 TEAM MATCHES")
    print("-" * 70)
    
    team_names = ["wolfram_ian", "wolfram_michael", "ian_michael", "wolfram_ian_michael"]
    for name in team_names:
        if name in results:
            matches = sorted(results[name], key=lambda x: -x["score"])
            display = name.replace("_", " + ").upper()
            print(f"\n{display} ({len(matches)} matches):")
            for m in matches[:5]:
                p = m["project"]
                print(f"  [{m['score']:3d}%] {p['title'][:42]}... ({p['remote_percent']}%R)")
    
    # ═══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    
    print()
    print("=" * 70)
    print("📊 ZUSAMMENFASSUNG")
    print("-" * 70)
    
    total_hot = 0
    for name in ["wolfram", "ian", "michael"] + team_names:
        if name in results:
            matches = results[name]
            hot = sum(1 for m in matches if m["score"] >= 70)
            good = sum(1 for m in matches if 50 <= m["score"] < 70)
            total_hot += hot
            display = name.replace("_", "+")
            print(f"  {display:25s}: {len(matches):3d} total | 🔥 {hot:2d} HOT | ✅ {good:2d} GOOD")
    
    print()
    print(f"🔥 {total_hot} HOT matches (>=70%) insgesamt!")
    
    # Save JSON
    output = {"total_projects": len(projects), "profiles": {}}
    for name, matches in results.items():
        output["profiles"][name] = {
            "count": len(matches),
            "hot": sum(1 for m in matches if m["score"] >= 70),
            "top_matches": sorted(matches, key=lambda x: -x["score"])[:10]
        }
    
    with open("output/matches.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n✅ Saved to output/matches.json")

if __name__ == "__main__":
    main()
