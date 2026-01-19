#!/usr/bin/env python3
"""
GMAIL DRAFTER
=============
Erstellt Gmail-Entwürfe für gematchte Projekte.

Features:
- Automatische Bewerbungstexte basierend auf Profil
- Attachments (CV, Zeugnisse)
- Batch-Erstellung für mehrere Projekte
- Browser-Fallback wenn keine Email bekannt

Usage:
    python drafter.py matches.json
    python drafter.py matches.json --dry-run
    python drafter.py matches.json --profile wolfram
"""

import os
import sys
import json
import base64
import pickle
import webbrowser
import argparse
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from urllib.parse import quote
from typing import List, Dict, Optional

# ══════════════════════════════════════════════════════════════════════════════
# KONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

ROOT_DIR = Path(__file__).parent
CONFIG_DIR = ROOT_DIR / "config"
ATTACHMENTS_DIR = ROOT_DIR / "attachments"

CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.pickle"

# Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

# ══════════════════════════════════════════════════════════════════════════════
# PROFILE-SPEZIFISCHE KONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

PROFILE_CONFIG = {
    "wolfram": {
        "name": "Wolfram Laube",
        "email": "wolfram.laube@blauweiss-edv.at",
        "phone": "+43 664 4011521",
        "rate": "105",
        "attachments": [
            "Profil_Laube_w_Summary_DE.pdf",
            "Studienerfolg_08900915_1.pdf",
        ],
        "signature": """Mit freundlichen Grüßen,

Wolfram Laube
Senior Solution Architect | AI Bachelor JKU 2026
+43 664 4011521
wolfram.laube@blauweiss-edv.at""",
        "intro_template": """Sehr geehrte Damen und Herren,

mit großem Interesse habe ich Ihre Ausschreibung "{title}" gesehen und bewerbe mich hiermit auf diese Position.

{body}

Verfügbarkeit: Ab sofort, 100% Remote
Stundensatz: {rate} EUR

{signature}""",
    },
    
    "ian": {
        "name": "Ian Matejka",
        "email": "ian.matejka@blauweiss-llc.com",
        "phone": "+1 XXX XXX XXXX",
        "rate": "105",
        "attachments": [
            "CV_Ian_Matejka_DE.pdf",
            "IanMatejkaCV1013MCM.pdf",
        ],
        "signature": """Best regards,

Ian Matejka
AI/ML Engineer
Blauweiss LLC""",
        "intro_template": """Dear Hiring Team,

I am writing to express my interest in the "{title}" position.

{body}

Availability: Immediate, 100% Remote
Rate: {rate} EUR/hour

{signature}""",
    },
    
    "michael": {
        "name": "Michael Matejka",
        "email": "michael.matejka@blauweiss-llc.com",
        "phone": "+1 XXX XXX XXXX",
        "rate": "120",
        "attachments": [
            "CV_Michael_Matejka_DE.pdf",
            "Michael_Matejka_CV_102025.pdf",
        ],
        "signature": """Best regards,

Michael Matejka
Technical Project Manager | MBA
Blauweiss LLC""",
        "intro_template": """Dear Hiring Team,

I am writing to express my interest in the "{title}" position.

{body}

Availability: Immediate, Remote preferred
Rate: {rate} EUR/hour

{signature}""",
    },
    
    # Team-Kombinationen
    "wolfram_ian": {
        "name": "Wolfram Laube & Ian Matejka",
        "email": "wolfram.laube@blauweiss-edv.at",
        "phone": "+43 664 4011521",
        "rate": "verhandelbar",
        "attachments": [
            "Profil_Laube_w_Summary_DE.pdf",
            "CV_Ian_Matejka_DE.pdf",
        ],
        "signature": """Mit freundlichen Grüßen,

Wolfram Laube (AI + DevOps/Cloud) & Ian Matejka (AI/ML Engineering)
Blauweiss LLC
+43 664 4011521""",
        "intro_template": """Sehr geehrte Damen und Herren,

wir bewerben uns als AI-fokussiertes Team auf Ihre Ausschreibung "{title}".

**Unser Angebot - Doppelte AI-Expertise:**
- **Wolfram Laube** (AI + Infrastructure): AI Bachelor JKU (Q1/2026), IBM AI-zertifiziert, 25+ Jahre Enterprise IT, CKA/CKAD - kann AI-Lösungen entwickeln UND produktionsreif deployen
- **Ian Matejka** (AI/ML Engineering): LLM-Spezialist, RAG-Pipelines, PyTorch/LangChain, Milvus, Computer Vision

**Gemeinsam:** End-to-End AI-Projekte von der Konzeption über Training bis zum skalierbaren Deployment auf Kubernetes.

{body}

Verfügbarkeit: Ab sofort, 100% Remote
Team-Rate: {rate}

{signature}""",
    },
    
    "wolfram_michael": {
        "name": "Wolfram Laube & Michael Matejka",
        "email": "wolfram.laube@blauweiss-edv.at",
        "phone": "+43 664 4011521",
        "rate": "verhandelbar",
        "attachments": [
            "Profil_Laube_w_Summary_DE.pdf",
            "CV_Michael_Matejka_DE.pdf",
        ],
        "signature": """Mit freundlichen Grüßen,

Wolfram Laube (Technical Architecture) & Michael Matejka (Business Strategy)
Blauweiss LLC
+43 664 4011521""",
        "intro_template": """Sehr geehrte Damen und Herren,

wir bewerben uns als eingespieltes Team auf Ihre Ausschreibung "{title}".

**Unser Angebot:**
- **Wolfram Laube** (Technical Architecture): 25+ Jahre Enterprise IT, Solution Architect, CKA/CKAD
- **Michael Matejka** (Business Strategy): MBA, Technical PM, Digital Transformation

{body}

Verfügbarkeit: Ab sofort, 100% Remote
Team-Rate: {rate}

{signature}""",
    },
    
    "ian_michael": {
        "name": "Ian Matejka & Michael Matejka",
        "email": "ian.matejka@blauweiss-llc.com",
        "phone": "+1 XXX XXX XXXX",
        "rate": "verhandelbar",
        "attachments": [
            "CV_Ian_Matejka_DE.pdf",
            "CV_Michael_Matejka_DE.pdf",
        ],
        "signature": """Best regards,

Ian Matejka (AI/ML Engineering) & Michael Matejka (Project Management)
Blauweiss LLC""",
        "intro_template": """Dear Hiring Team,

We are applying as a team for your "{title}" position.

**Our Offering:**
- **Ian Matejka** (AI/ML Engineering): LLM specialist, RAG pipelines, PyTorch/LangChain
- **Michael Matejka** (Project Management): MBA, Technical PM, Stakeholder Management

{body}

Availability: Immediate, 100% Remote
Team Rate: {rate}

{signature}""",
    },
    
    "all_three": {
        "name": "Wolfram Laube, Ian Matejka & Michael Matejka",
        "email": "wolfram.laube@blauweiss-edv.at",
        "phone": "+43 664 4011521",
        "rate": "verhandelbar",
        "attachments": [
            "Profil_Laube_w_Summary_DE.pdf",
            "CV_Ian_Matejka_DE.pdf",
            "CV_Michael_Matejka_DE.pdf",
        ],
        "signature": """Mit freundlichen Grüßen,

Wolfram Laube, Ian Matejka & Michael Matejka
Blauweiss LLC - Full Stack Consulting Team
+43 664 4011521""",
        "intro_template": """Sehr geehrte Damen und Herren,

wir bewerben uns als komplettes Delivery-Team auf Ihre Ausschreibung "{title}".

**Unser Team:**
- **Wolfram Laube** (Infrastructure & DevOps): 25+ Jahre, CKA/CKAD, AWS/Azure/GCP
- **Ian Matejka** (AI/ML Engineering): LLM-Spezialist, RAG, PyTorch/LangChain
- **Michael Matejka** (Project & Business): MBA, Technical PM, Transformation

Gemeinsam decken wir den kompletten Stack ab: Von Cloud-Infrastruktur über AI-Implementation bis zur Business-Integration.

{body}

Verfügbarkeit: Ab sofort, 100% Remote
Team-Rate: {rate}

{signature}""",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# BEWERBUNGSTEXT-GENERIERUNG
# ══════════════════════════════════════════════════════════════════════════════

def generate_body_for_match(match: Dict) -> str:
    """
    Generiert den Hauptteil der Bewerbung basierend auf dem Match.
    """
    profile_key = match.get("profile_key", "wolfram")
    percentage = match.get("percentage", 0)
    project_title = match.get("project_title", "")
    
    # Basis-Texte je nach Profil
    if profile_key == "wolfram" or profile_key.startswith("wolfram"):
        if "kubernetes" in project_title.lower() or "devops" in project_title.lower():
            body = """**Relevante Qualifikationen:**
- CKA + CKAD zertifiziert (2024)
- Kubernetes seit 2016: OpenShift, AKS, EKS, GKE, Vanilla
- Cloud-Architekturen: AWS, Azure, GCP
- CI/CD: GitLab, Jenkins, ArgoCD, Helm

**Aktuelle Referenz:**
50Hertz/Elia Group (2024-2025): IaaS Software Architect für KRITIS-konforme Hybrid-Cloud-Plattform."""

        elif "python" in project_title.lower() or "fastapi" in project_title.lower() or "django" in project_title.lower():
            body = """**Python-Expertise (10+ Jahre):**
- Backend: FastAPI, Flask, Django
- Data Science: Pandas, NumPy, scikit-learn
- Async: asyncio, aiohttp, Celery
- Testing: pytest, unittest
- DevOps: Poetry, pip, Docker, CI/CD

**Python in Produktion:**
- 50Hertz: Python-basierte Automation für Hybrid-Cloud-Infrastruktur
- Frauscher: ML-Pipelines mit Python, Time Series Analysis
- Disy: RAG-Pipeline mit LangChain, Vector DBs
- DKV/AOK: Backend-Services, API-Entwicklung

**Kombination Python + Enterprise:**
Nicht nur Scripting, sondern produktionsreife Architekturen mit 25 Jahren Enterprise-Erfahrung.
CKA/CKAD zertifiziert - ich kann Python-Services auch skalierbar auf Kubernetes deployen."""

        elif "java" in project_title.lower() or "spring" in project_title.lower():
            body = """**Relevante Qualifikationen:**
- Java: 25+ Jahre, Spring Boot bei DB VENDO, Siemens, DKV, AOK
- Microservices-Architekturen
- OpenShift/Kubernetes: CKA + CKAD zertifiziert

**Referenzen:**
- Deutsche Bahn VENDO: Cloud Architect, Digitale Vertriebsplattform
- Bank Austria: 7 Jahre Core Banking, Trading-Systeme"""

        elif any(kw in project_title.lower() for kw in ["ai", "ml", "ki", "llm", "machine learning", "künstliche intelligenz", "nlp", "rag"]):
            body = """**AI/ML Qualifikationen:**
- **AI Bachelor JKU Linz** (Abschluss Q1/2026) - Deep Learning, NLP, Computer Vision
- IBM-zertifiziert: Applied AI with Deep Learning, Advanced Machine Learning, Advanced Data Science
- Python: 10+ Jahre, TensorFlow, PyTorch, Keras, scikit-learn

**Praktische AI-Projekte:**
- RAG-Pipeline mit LangChain und Vector DBs
- LLM-Integration (GPT, Claude API)
- Frauscher: ML/MLOps für Predictive Maintenance, Time Series Analysis
- Disy: On-premise LLM mit GPT4All für Knowledge Base

**Einzigartige Kombination:**
AI-Expertise + 25 Jahre Enterprise-Architektur + CKA/CKAD = 
Ich kann AI-Lösungen nicht nur entwickeln, sondern auch produktionsreif deployen (Kubeflow, MLflow, Kubernetes)."""

        elif "mlops" in project_title.lower() or "platform" in project_title.lower():
            body = """**MLOps & Platform Engineering:**
- AI Bachelor JKU Linz (Q1/2026) + IBM AI/ML Zertifizierungen
- CKA + CKAD zertifiziert (2024)
- Kubeflow, MLflow, TensorFlow Serving auf Kubernetes
- CI/CD für ML-Pipelines: GitLab, ArgoCD

**Kombination AI + DevOps:**
- Model Training & Deployment auf K8s
- Feature Stores, Model Registry
- Monitoring für ML-Systeme (Prometheus/Grafana)

**Referenz:**
50Hertz (2024-2025): IaaS Software Architect, Hybrid Cloud Platform"""

        else:
            body = """**Profil-Highlights:**
- 25+ Jahre IT-Erfahrung, davon 10+ als Solution Architect
- **Python:** 10+ Jahre (FastAPI, Django, Pandas, ML-Stack)
- **AI Bachelor JKU Linz (Abschluss Q1/2026)** - Deep Learning, NLP, Computer Vision
- CKA + CKAD zertifiziert (2024)
- Multi-Cloud: AWS, Azure, GCP
- IBM AI/ML Zertifizierungen

**Branchen:** Banking, Energie (KRITIS), Healthcare, Mobility"""

    elif profile_key == "ian":
        body = """**AI/ML Expertise:**
- LLM Integration: GPT, Claude, Open Source Models
- RAG Pipelines: LangChain, LlamaIndex, Vector DBs
- MLOps: Kubeflow, MLflow, AWS SageMaker
- Frameworks: PyTorch, TensorFlow, Hugging Face

**Recent Projects:**
- Enterprise RAG system with Milvus
- Computer Vision pipeline for manufacturing
- MCP tools for agentic AI"""

    elif profile_key == "michael":
        body = """**Management Expertise:**
- Technical Project/Program Management
- Digital Transformation Leadership
- MBA, Strategic Planning
- Stakeholder & Executive Communication

**Domain Experience:**
- Energy/Oil & Gas: Reservoir Engineering, Data Analytics
- AI Strategy & Implementation
- M&A Technical Due Diligence"""

    else:
        body = "Siehe beigefügten Lebenslauf für Details."
    
    return body


def generate_subject(match: Dict) -> str:
    """Generiert den E-Mail-Betreff."""
    title = match.get("project_title", "Position")
    profile_name = match.get("profile_name", "")
    
    # Kürzen wenn zu lang
    if len(title) > 50:
        title = title[:47] + "..."
    
    return f"Bewerbung: {title}"


def generate_email(match: Dict) -> Dict:
    """
    Generiert komplette E-Mail-Daten für einen Match.
    
    Returns:
        Dict mit to, subject, body, attachments
    """
    profile_key = match.get("profile_key", "wolfram")
    config = PROFILE_CONFIG.get(profile_key, PROFILE_CONFIG["wolfram"])
    
    body = generate_body_for_match(match)
    
    email_body = config["intro_template"].format(
        title=match.get("project_title", ""),
        body=body,
        rate=config["rate"],
        signature=config["signature"],
    )
    
    return {
        "to": match.get("contact_email", ""),
        "subject": generate_subject(match),
        "body": email_body,
        "attachments": config["attachments"],
        "from_name": config["name"],
        "from_email": config["email"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# GMAIL API
# ══════════════════════════════════════════════════════════════════════════════

def get_gmail_service():
    """Authentifiziert und gibt Gmail Service zurück."""
    try:
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("\n❌ Google-Pakete nicht installiert!")
        print("   pip install google-auth-oauthlib google-api-python-client")
        return None
    
    creds = None
    
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"\n❌ {CREDENTIALS_FILE} nicht gefunden!")
                print("   Kopiere credentials.json nach config/")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)


def create_mime_message(to: str, subject: str, body: str, attachment_paths: List[Path]) -> Dict:
    """Erstellt MIME-Nachricht mit Attachments."""
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject
    
    msg_body = MIMEText(body)
    message.attach(msg_body)
    
    for filepath in attachment_paths:
        if not filepath.exists():
            print(f"   ⚠️  Attachment nicht gefunden: {filepath}")
            continue
        
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{filepath.name}"')
        message.attach(part)
        print(f"   📎 {filepath.name}")
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}


def create_draft(service, message: Dict) -> str:
    """Erstellt Gmail Draft und gibt ID zurück."""
    draft = service.users().drafts().create(userId='me', body={'message': message}).execute()
    return draft['id']


# ══════════════════════════════════════════════════════════════════════════════
# DRAFT-ERSTELLUNG
# ══════════════════════════════════════════════════════════════════════════════

def create_draft_for_match(match: Dict, dry_run: bool = False) -> bool:
    """
    Erstellt Gmail Draft für einen Match.
    
    Args:
        match: Match-Daten vom Matcher
        dry_run: Nur anzeigen, nicht erstellen
    
    Returns:
        True bei Erfolg
    """
    email = generate_email(match)
    
    print(f"\n{'='*60}")
    print(f"📧 {match.get('project_title', '')[:50]}")
    print(f"   👤 {email['from_name']}")
    print(f"   📬 An: {email['to'] or '(TODO: manuell eintragen)'}")
    print(f"   📝 Betreff: {email['subject'][:50]}")
    
    if dry_run:
        print(f"\n--- DRY RUN - Nicht erstellt ---")
        print(f"\n{email['body'][:500]}...")
        return True
    
    # Gmail Draft erstellen - AUCH OHNE EMPFÄNGER!
    service = get_gmail_service()
    if not service:
        print("   ❌ Gmail-Authentifizierung fehlgeschlagen")
        # Fallback: Browser öffnen
        url = match.get("project_url", "")
        if url:
            print(f"\n   🌐 Öffne Projekt-URL: {url}")
            webbrowser.open(url)
        return False
    
    # Attachments auflösen
    attachment_paths = []
    for att in email['attachments']:
        path = ATTACHMENTS_DIR / att
        if path.exists():
            attachment_paths.append(path)
        else:
            # Auch im Projekt-Verzeichnis suchen
            alt_path = Path("/mnt/project") / att
            if alt_path.exists():
                attachment_paths.append(alt_path)
            else:
                print(f"   ⚠️  Attachment nicht gefunden: {att}")
    
    try:
        # Draft erstellen - to kann leer sein!
        to_addr = email['to'] if email['to'] else ""
        
        message = create_mime_message(
            to_addr,
            email['subject'],
            email['body'],
            attachment_paths
        )
        
        draft_id = create_draft(service, message)
        print(f"\n   ✅ Draft erstellt! ID: {draft_id}")
        print(f"   🔗 Projekt: {match.get('project_url', '')[:60]}")
        
        if not email['to']:
            print(f"   ⚠️  ACHTUNG: Empfänger manuell eintragen!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        # Fallback: Browser
        url = match.get("project_url", "")
        if url:
            webbrowser.open(url)
        return False


def create_drafts_batch(matches: List[Dict], dry_run: bool = False, 
                        max_drafts: int = 5) -> int:
    """
    Erstellt Drafts für mehrere Matches.
    
    Returns:
        Anzahl erstellter Drafts
    """
    created = 0
    
    for i, match in enumerate(matches[:max_drafts]):
        print(f"\n[{i+1}/{min(len(matches), max_drafts)}]")
        
        if create_draft_for_match(match, dry_run=dry_run):
            created += 1
        
        # Pause zwischen Drafts
        if not dry_run and i < len(matches) - 1:
            import time
            time.sleep(1)
    
    return created


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Gmail Drafter")
    parser.add_argument("input", nargs="?", help="Input JSON vom Matcher")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Nur anzeigen")
    parser.add_argument("--profile", "-p", help="Nur bestimmtes Profil")
    parser.add_argument("--max", "-m", type=int, default=5, help="Max Drafts")
    parser.add_argument("--hot-only", action="store_true", help="Nur HOT Matches")
    
    args = parser.parse_args()
    
    # Matches laden
    if args.input:
        with open(args.input) as f:
            matches = json.load(f)
    else:
        # Demo
        matches = [
            {
                "project_id": "demo_1",
                "project_title": "Senior DevOps Engineer - Kubernetes/AWS",
                "project_url": "https://freelancermap.de/example",
                "portal": "freelancermap",
                "profile_key": "wolfram",
                "profile_name": "Wolfram Laube",
                "percentage": 85,
                "recommendation": "HOT",
                "contact_email": "",
            }
        ]
        print("⚠️  Keine Input-Datei, nutze Demo-Daten\n")
    
    # Filtern
    if args.profile:
        matches = [m for m in matches if m.get("profile_key") == args.profile]
    
    if args.hot_only:
        matches = [m for m in matches if m.get("recommendation") == "HOT"]
    
    print(f"📧 Erstelle Drafts für {len(matches)} Matches...")
    if args.dry_run:
        print("   (DRY RUN - keine echten Drafts)\n")
    
    created = create_drafts_batch(matches, dry_run=args.dry_run, max_drafts=args.max)
    
    print(f"\n{'='*60}")
    print(f"✅ {created} Drafts {'würden erstellt' if args.dry_run else 'erstellt'}")
    
    return created


if __name__ == "__main__":
    main()
