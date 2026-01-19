#!/usr/bin/env python3
"""
Applications Pipeline - Match Job
Matches projects against:
  Solo: Wolfram, Ian, Michael  
  Teams: W+I, W+M, I+M, W+I+M
"""

import os
import sys
import json
from collections import defaultdict

sys.path.insert(0, os.getcwd())

from src.admin.applications.pipeline.profiles import PROFILES, TEAM_COMBOS, WOLFRAM, IAN, MICHAEL

def match_solo(project, profile):
    """Match gegen ein Solo-Profil."""
    search_text = " ".join([
        project.get("title", ""),
        project.get("description", ""),
        " ".join(project.get("skills", [])),
    ]).lower()
    return profile.match_score(search_text)

def match_team(project, team_config):
    """Match gegen ein Team-Combo."""
    search_text = " ".join([
        project.get("title", ""),
        project.get("description", ""),
        " ".join(project.get("skills", [])),
    ]).lower()
    
    keywords = team_config.get("keywords", set())
    matches = []
    for kw in keywords:
        if kw.lower() in search_text:
            matches.append(kw)
    
    # Score: 10 Punkte pro Keyword-Match, max 100
    score = min(100, len(matches) * 15)
    
    return {
        "percentage": score,
        "matches": {"keywords": matches},
        "excluded_by": None
    }

def main():
    min_score = int(os.environ.get("MIN_SCORE", "40"))
    
    with open("output/projects.json") as f:
        projects = json.load(f)
    
    print(f"📊 Matching {len(projects)} projects (min score: {min_score}%)")
    print("=" * 70)
    
    results = defaultdict(list)
    
    # ═══════════════════════════════════════════════════════════════════
    # SOLO MATCHES
    # ═══════════════════════════════════════════════════════════════════
    
    solo_profiles = {"wolfram": WOLFRAM, "ian": IAN, "michael": MICHAEL}
    
    for project in projects:
        for name, profile in solo_profiles.items():
            result = match_solo(project, profile)
            if result["percentage"] >= min_score and not result.get("excluded_by"):
                results[name].append({
                    "project": project,
                    "score": result["percentage"],
                    "keywords": result["matches"].get("must_have", [])[:5],
                })
    
    # ═══════════════════════════════════════════════════════════════════
    # TEAM MATCHES
    # ═══════════════════════════════════════════════════════════════════
    
    for team_name, team_config in TEAM_COMBOS.items():
        for project in projects:
            result = match_team(project, team_config)
            if result["percentage"] >= min_score:
                results[team_name].append({
                    "project": project,
                    "score": result["percentage"],
                    "keywords": result["matches"].get("keywords", [])[:5],
                })
    
    # ═══════════════════════════════════════════════════════════════════
    # OUTPUT
    # ═══════════════════════════════════════════════════════════════════
    
    print()
    print("🧑 SOLO MATCHES")
    print("-" * 70)
    
    for name in ["wolfram", "ian", "michael"]:
        matches = sorted(results[name], key=lambda x: -x["score"])
        print(f"\n{name.upper()} ({len(matches)} matches):")
        for m in matches[:5]:
            p = m["project"]
            print(f"  [{m['score']:3d}%] {p['title'][:42]}... ({p['remote_percent']}%R)")
            if m["keywords"]:
                print(f"         → {', '.join(m['keywords'][:4])}")
    
    print()
    print("👥 TEAM MATCHES") 
    print("-" * 70)
    
    for team_name in ["wolfram_ian", "wolfram_michael", "ian_michael", "all_three"]:
        if team_name in results:
            matches = sorted(results[team_name], key=lambda x: -x["score"])
            display = TEAM_COMBOS[team_name]["name"]
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
    all_names = ["wolfram", "ian", "michael", "wolfram_ian", "wolfram_michael", "ian_michael", "all_three"]
    
    for name in all_names:
        if name in results:
            matches = results[name]
            hot = sum(1 for m in matches if m["score"] >= 70)
            good = sum(1 for m in matches if 50 <= m["score"] < 70)
            total_hot += hot
            display = name.replace("_", "+")
            print(f"  {display:25s}: {len(matches):3d} | 🔥 {hot:2d} HOT | ✅ {good:2d} GOOD")
    
    print()
    print(f"🔥 {total_hot} HOT matches (>=70%) insgesamt!")
    
    # Save JSON
    output = {"total_projects": len(projects), "profiles": {}}
    for name, matches in results.items():
        output["profiles"][name] = {
            "count": len(matches),
            "hot": sum(1 for m in matches if m["score"] >= 70),
            "top": sorted(matches, key=lambda x: -x["score"])[:10]
        }
    
    with open("output/matches.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n✅ Saved to output/matches.json")

if __name__ == "__main__":
    main()
