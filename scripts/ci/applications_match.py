#!/usr/bin/env python3
"""
Applications Pipeline - Match Job
Matches projects against profiles
"""

import os
import sys
import json

sys.path.insert(0, os.getcwd())

from src.admin.applications.pipeline.matcher import ProjectMatcher
from src.admin.applications.pipeline.profiles import PROFILES

def main():
    min_score = int(os.environ.get("MIN_SCORE", "50"))
    max_results = int(os.environ.get("MAX_RESULTS", "20"))
    
    # Load projects
    with open("output/projects.json") as f:
        projects = json.load(f)
    
    print(f"📊 Matching {len(projects)} projects against {len(PROFILES)} profiles...")
    
    matcher = ProjectMatcher(PROFILES)
    results = []
    
    for project in projects:
        match = matcher.match(project)
        if match and match['score'] >= min_score:
            results.append(match)
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    results = results[:max_results]
    
    # Summary
    hot = sum(1 for r in results if r['recommendation'] == 'HOT')
    good = sum(1 for r in results if r['recommendation'] == 'GOOD')
    
    print(f"\n📊 MATCHING RESULTS")
    print(f"   🔥 HOT:  {hot}")
    print(f"   ✅ GOOD: {good}")
    print(f"   Total:  {len(results)}")
    
    for r in results[:10]:
        title = r['project']['title'][:50]
        print(f"\n[{r['score']}%] {title}...")
        print(f"   → {r['profile_name']}")
    
    with open("output/matches.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(results)} matches saved to output/matches.json")

if __name__ == "__main__":
    main()
