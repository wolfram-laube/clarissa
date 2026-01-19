#!/usr/bin/env python3
"""
PROJEKT-MATCHER
===============
Matched gefundene Projekte gegen Profile (Wolfram, Ian, Michael).

Features:
- Einzelperson-Matching
- Team-Matching (Kombinationen)
- Ranking nach Score
- Export für Gmail Drafter

Usage:
    python matcher.py projects.json
    python matcher.py projects.json --min-score 50
    python matcher.py projects.json --profile wolfram
"""

import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from profiles import PROFILES, TEAM_COMBOS, Profile, get_best_matches
from crawler import Project

# ══════════════════════════════════════════════════════════════════════════════
# MATCH-ERGEBNIS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class MatchResult:
    """Ergebnis eines Projekt-Profile-Matches."""
    project: Project
    profile_key: str
    profile_name: str
    score: int
    percentage: int
    matches: Dict
    is_team: bool = False
    team_members: List[str] = None
    recommendation: str = ""  # "HOT", "GOOD", "MAYBE", "SKIP"
    
    def to_dict(self) -> Dict:
        return {
            "project": self.project.to_dict(),
            "profile_key": self.profile_key,
            "profile_name": self.profile_name,
            "score": self.score,
            "percentage": self.percentage,
            "matches": self.matches,
            "is_team": self.is_team,
            "team_members": self.team_members,
            "recommendation": self.recommendation,
        }


# ══════════════════════════════════════════════════════════════════════════════
# MATCHER
# ══════════════════════════════════════════════════════════════════════════════

class ProjectMatcher:
    """Matched Projekte gegen Profile."""
    
    def __init__(self):
        self.profiles = PROFILES
        self.team_combos = TEAM_COMBOS
    
    def match_single(self, project: Project, profile_key: str) -> Optional[MatchResult]:
        """Matched ein Projekt gegen ein einzelnes Profil."""
        if profile_key not in self.profiles:
            return None
        
        profile = self.profiles[profile_key]
        text = project.full_text
        
        match = profile.match_score(text)
        
        if match["excluded_by"]:
            return None
        
        # Recommendation basierend auf Prozent
        if match["percentage"] >= 70:
            recommendation = "HOT"
        elif match["percentage"] >= 50:
            recommendation = "GOOD"
        elif match["percentage"] >= 30:
            recommendation = "MAYBE"
        else:
            recommendation = "SKIP"
        
        return MatchResult(
            project=project,
            profile_key=profile_key,
            profile_name=profile.name,
            score=match["score"],
            percentage=match["percentage"],
            matches=match["matches"],
            recommendation=recommendation,
        )
    
    def match_all_profiles(self, project: Project, min_percentage: int = 30) -> List[MatchResult]:
        """Matched ein Projekt gegen alle Profile."""
        results = []
        
        for key in self.profiles:
            result = self.match_single(project, key)
            if result and result.percentage >= min_percentage:
                results.append(result)
        
        # Sortieren nach Score
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def match_team(self, project: Project, team_key: str) -> Optional[MatchResult]:
        """Matched ein Projekt gegen ein Team."""
        if team_key not in self.team_combos:
            return None
        
        team = self.team_combos[team_key]
        text = project.full_text
        
        # Kombinierter Score aus allen Team-Mitgliedern
        total_score = 0
        all_matches = {"must_have": [], "strong_match": [], "nice_to_have": []}
        member_scores = []
        
        for profile in team["profiles"]:
            match = profile.match_score(text)
            if match["excluded_by"]:
                return None  # Wenn einer excluded ist, ganzes Team nicht
            
            total_score += match["score"]
            member_scores.append((profile.name, match["percentage"]))
            
            for cat in all_matches:
                all_matches[cat].extend(match["matches"].get(cat, []))
        
        # Durchschnittlicher Prozentsatz
        avg_percentage = sum(s[1] for s in member_scores) // len(member_scores)
        
        # Team-Bonus wenn Keywords matchen
        team_keywords = team.get("keywords", set())
        text_lower = text.lower()
        team_keyword_hits = sum(1 for kw in team_keywords if kw in text_lower)
        if team_keyword_hits >= 2:
            avg_percentage = min(100, avg_percentage + 10)
        
        if avg_percentage >= 70:
            recommendation = "HOT"
        elif avg_percentage >= 50:
            recommendation = "GOOD"
        else:
            recommendation = "MAYBE"
        
        return MatchResult(
            project=project,
            profile_key=team_key,
            profile_name=team["name"],
            score=total_score,
            percentage=avg_percentage,
            matches=all_matches,
            is_team=True,
            team_members=[p.name for p in team["profiles"]],
            recommendation=recommendation,
        )
    
    def match_projects(self, 
                       projects: List[Project],
                       include_teams: bool = True,
                       min_percentage: int = 30) -> List[MatchResult]:
        """
        Matched alle Projekte gegen alle Profile und Teams.
        
        Returns:
            Sortierte Liste von Match-Ergebnissen
        """
        all_results = []
        
        for project in projects:
            # Einzelprofile
            for key in self.profiles:
                result = self.match_single(project, key)
                if result and result.percentage >= min_percentage:
                    all_results.append(result)
            
            # Team-Kombinationen
            if include_teams:
                for team_key in self.team_combos:
                    result = self.match_team(project, team_key)
                    if result and result.percentage >= min_percentage:
                        all_results.append(result)
        
        # Sortieren: HOT zuerst, dann nach Score
        priority = {"HOT": 0, "GOOD": 1, "MAYBE": 2, "SKIP": 3}
        all_results.sort(key=lambda x: (priority.get(x.recommendation, 3), -x.score))
        
        return all_results
    
    def get_summary(self, results: List[MatchResult]) -> Dict:
        """Erstellt Zusammenfassung der Ergebnisse."""
        summary = {
            "total": len(results),
            "by_recommendation": {"HOT": 0, "GOOD": 0, "MAYBE": 0, "SKIP": 0},
            "by_profile": {},
            "by_portal": {},
        }
        
        for r in results:
            summary["by_recommendation"][r.recommendation] = \
                summary["by_recommendation"].get(r.recommendation, 0) + 1
            
            summary["by_profile"][r.profile_name] = \
                summary["by_profile"].get(r.profile_name, 0) + 1
            
            portal = r.project.portal
            summary["by_portal"][portal] = summary["by_portal"].get(portal, 0) + 1
        
        return summary


# ══════════════════════════════════════════════════════════════════════════════
# AUSGABE-FORMATIERUNG
# ══════════════════════════════════════════════════════════════════════════════

def format_result(result: MatchResult, verbose: bool = False) -> str:
    """Formatiert ein Match-Ergebnis für die Ausgabe."""
    icons = {"HOT": "🔥", "GOOD": "✅", "MAYBE": "🤔", "SKIP": "⏭️"}
    icon = icons.get(result.recommendation, "❓")
    
    lines = [
        f"\n{icon} [{result.percentage}%] {result.project.title[:60]}",
        f"   👤 {result.profile_name}" + (" (TEAM)" if result.is_team else ""),
        f"   🔗 {result.project.url}",
    ]
    
    if result.project.remote:
        lines.append(f"   🏠 Remote: {result.project.remote}")
    
    if verbose and result.matches:
        if result.matches.get("must_have"):
            lines.append(f"   ✓ Must-have: {', '.join(result.matches['must_have'][:5])}")
        if result.matches.get("strong_match"):
            lines.append(f"   ✓ Strong: {', '.join(result.matches['strong_match'][:5])}")
    
    return "\n".join(lines)


def format_for_drafter(results: List[MatchResult]) -> List[Dict]:
    """Formatiert Ergebnisse für den Gmail Drafter."""
    output = []
    
    for r in results:
        output.append({
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
    
    return output


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Projekt-Matcher")
    parser.add_argument("input", nargs="?", help="Input JSON mit Projekten")
    parser.add_argument("--min-score", "-m", type=int, default=30, help="Minimum Prozent")
    parser.add_argument("--profile", "-p", help="Nur bestimmtes Profil (wolfram/ian/michael)")
    parser.add_argument("--no-teams", action="store_true", help="Keine Team-Matches")
    parser.add_argument("--output", "-o", help="Output JSON für Drafter")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose Output")
    
    args = parser.parse_args()
    
    # Projekte laden
    if args.input:
        with open(args.input) as f:
            data = json.load(f)
            projects = [Project(**p) for p in data]
    else:
        # Demo-Daten
        projects = [
            Project(
                id="demo_1",
                title="Senior DevOps Engineer - Kubernetes/AWS",
                portal="freelancermap",
                url="https://example.com/1",
                description="Wir suchen einen erfahrenen DevOps Engineer mit Kubernetes und AWS Erfahrung. Terraform, CI/CD, Python von Vorteil. 100% Remote möglich.",
                remote="100%",
            ),
            Project(
                id="demo_2",
                title="AI/ML Engineer - LLM Integration",
                portal="freelancermap",
                url="https://example.com/2",
                description="Aufbau einer RAG-Pipeline mit LangChain. Python, PyTorch, Vector Databases. Erfahrung mit OpenAI oder Claude API.",
                remote="100%",
            ),
            Project(
                id="demo_3",
                title="Technical Project Manager - Digital Transformation",
                portal="gulp",
                url="https://example.com/3",
                description="Leitung eines Transformationsprojekts. MBA oder vergleichbar. Stakeholder Management, Agile, AI-Strategie.",
                remote="80%",
            ),
        ]
        print("⚠️  Keine Input-Datei, nutze Demo-Daten\n")
    
    print(f"📊 Matche {len(projects)} Projekte...")
    
    matcher = ProjectMatcher()
    
    if args.profile:
        # Nur ein Profil
        results = []
        for p in projects:
            r = matcher.match_single(p, args.profile)
            if r and r.percentage >= args.min_score:
                results.append(r)
        results.sort(key=lambda x: x.score, reverse=True)
    else:
        # Alle Profile + Teams
        results = matcher.match_projects(
            projects,
            include_teams=not args.no_teams,
            min_percentage=args.min_score,
        )
    
    # Summary
    summary = matcher.get_summary(results)
    
    print(f"\n{'='*60}")
    print(f"📈 ERGEBNIS: {summary['total']} Matches")
    print(f"   🔥 HOT: {summary['by_recommendation'].get('HOT', 0)}")
    print(f"   ✅ GOOD: {summary['by_recommendation'].get('GOOD', 0)}")
    print(f"   🤔 MAYBE: {summary['by_recommendation'].get('MAYBE', 0)}")
    print(f"{'='*60}")
    
    # Details
    for r in results:
        print(format_result(r, verbose=args.verbose))
    
    # Output für Drafter
    if args.output:
        drafter_data = format_for_drafter(results)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(drafter_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Drafter-Daten: {args.output}")
    
    return results


if __name__ == "__main__":
    main()
