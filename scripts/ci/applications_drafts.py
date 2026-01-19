#!/usr/bin/env python3
"""
Applications Pipeline - Drafts Job
Creates Gmail drafts for matched projects
"""

import os
import json
import base64
import requests

def main():
    # OAuth credentials from CI variables
    CLIENT_ID = os.environ.get("GMAIL_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("GMAIL_CLIENT_SECRET")
    REFRESH_TOKEN = os.environ.get("GMAIL_REFRESH_TOKEN")
    
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        print("⚠️  Gmail credentials not configured")
        print("   Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN")
        return
    
    max_drafts = int(os.environ.get("MAX_DRAFTS", "5"))
    
    # Load matches
    with open("output/matches.json") as f:
        matches = json.load(f)
    
    matches = matches[:max_drafts]
    
    if not matches:
        print("ℹ️  No matches to process")
        return
    
    # Get access token
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    })
    
    if resp.status_code != 200:
        print(f"❌ Token error: {resp.text}")
        return
    
    access_token = resp.json()["access_token"]
    print("✅ Got access token")
    
    # Create drafts
    created = 0
    for i, match in enumerate(matches, 1):
        project = match['project']
        profile = match['profile_name']
        score = match['score']
        keywords = match.get('matches', {}).get('must_have', [])[:5]
        
        # Generate email
        subject = f"Bewerbung: {project['title'][:60]}"
        
        body_lines = [
            "Sehr geehrte Damen und Herren,",
            "",
            f"mit großem Interesse habe ich Ihre Ausschreibung \"{project['title']}\" gesehen.",
            "",
            f"Match: {score}% für Profil \"{profile}\"",
            f"Keywords: {', '.join(keywords)}",
            "",
            f"Projekt: {project['url']}",
            "",
            "Verfügbarkeit: Ab sofort, 100% Remote",
            "Stundensatz: 105 EUR",
            "",
            "Mit freundlichen Grüßen,",
            "Wolfram Laube",
            "+43 664 4011521 | wolfram.laube@blauweiss-edv.at"
        ]
        body = "\n".join(body_lines)
        
        raw_email = f"To: \r\nSubject: {subject}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{body}"
        raw_b64 = base64.urlsafe_b64encode(raw_email.encode()).decode()
        
        resp = requests.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={"message": {"raw": raw_b64}}
        )
        
        rec = match['recommendation']
        title_short = project['title'][:40]
        
        if resp.status_code in (200, 201):
            created += 1
            print(f"[{i}/{len(matches)}] ✅ {rec} {score}%: {title_short}...")
        else:
            print(f"[{i}/{len(matches)}] ❌ Failed: {resp.text[:100]}")
    
    print(f"\n🎉 {created}/{len(matches)} Gmail drafts created!")
    print("👉 Check Gmail → Drafts")

if __name__ == "__main__":
    main()
