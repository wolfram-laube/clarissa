#!/usr/bin/env python3
"""
Gmail Benchmark Report with LLM-generated text.
Uses OpenAI or Anthropic to generate contextual email body.
"""
import os
import json
import base64
import glob
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


def generate_email_with_openai(benchmark_data, pipeline_url, pipeline_date):
    """Generate email text using OpenAI GPT-4."""
    try:
        import openai
    except ImportError:
        print("openai package not installed")
        return None
    
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    prompt = f"""Schreibe eine kurze, professionelle E-Mail auf Deutsch für einen GitLab CI/CD Benchmark-Report.

Benchmark-Daten:
{json.dumps(benchmark_data, indent=2)}

Pipeline: {pipeline_url}
Datum: {pipeline_date}

Anforderungen:
- Beginne mit "Hallo Wolfram,"
- Fasse die wichtigsten Erkenntnisse zusammen (schnellster/langsamster Runner, Vergleich der Executors)
- Erwähne dass 4 Grafiken als Anhänge dabei sind
- Halte es kurz und informativ (max 150 Wörter)
- Ende mit "Grüße, CLARISSA CI/CD Pipeline"
- Verwende deutsche Umlaute (ü, ö, ä, ß)
- Keine Markdown-Formatierung, nur Plain Text
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7
    )
    
    return response.choices[0].message.content


def generate_email_with_anthropic(benchmark_data, pipeline_url, pipeline_date):
    """Generate email text using Anthropic Claude."""
    try:
        import anthropic
    except ImportError:
        print("anthropic package not installed")
        return None
    
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    prompt = f"""Schreibe eine kurze, professionelle E-Mail auf Deutsch für einen GitLab CI/CD Benchmark-Report.

Benchmark-Daten:
{json.dumps(benchmark_data, indent=2)}

Pipeline: {pipeline_url}
Datum: {pipeline_date}

Anforderungen:
- Beginne mit "Hallo Wolfram,"
- Fasse die wichtigsten Erkenntnisse zusammen (schnellster/langsamster Runner, Vergleich der Executors)
- Erwähne dass 4 Grafiken als Anhänge dabei sind
- Halte es kurz und informativ (max 150 Wörter)
- Ende mit "Grüße, CLARISSA CI/CD Pipeline"
- Verwende deutsche Umlaute (ü, ö, ä, ß)
- Keine Markdown-Formatierung, nur Plain Text
"""
    
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


def get_fallback_body(pipeline_url, pipeline_date):
    """Fallback if LLM fails."""
    return f"""Hallo Wolfram,

die Benchmark-Ergebnisse für alle 12 GitLab Runner sind verfügbar.

Pipeline: {pipeline_url}
Datum: {pipeline_date}

Übersicht der Runner:
• Mac #1: Shell, Docker, Kubernetes
• Mac #2: Shell, Docker, Kubernetes  
• Linux Yoga: Shell, Docker, Kubernetes
• GCP VM: Shell, Docker, Kubernetes

Die Grafiken sind als Anhänge beigefügt.

Grüße,
CLARISSA CI/CD Pipeline
"""


def main():
    # Gmail credentials
    CLIENT_ID = os.environ["GMAIL_CLIENT_ID"]
    CLIENT_SECRET = os.environ["GMAIL_CLIENT_SECRET"]
    REFRESH_TOKEN = os.environ["GMAIL_REFRESH_TOKEN"]
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()

    # Get Gmail access token
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
    )
    if response.status_code != 200:
        print(f"Token error: {response.text}")
        exit(1)
    access_token = response.json()["access_token"]
    print("Got Gmail access token")

    # Prepare email metadata
    pipeline_date = os.environ.get("CI_PIPELINE_CREATED_AT", "")[:10]
    pipeline_url = os.environ.get("CI_PIPELINE_URL", "N/A")

    # Load benchmark data if available
    benchmark_data = {}
    json_files = glob.glob("docs/ci/benchmarks/*.json") + glob.glob("*.json")
    for jf in json_files:
        if "benchmark" in jf.lower():
            try:
                with open(jf) as f:
                    benchmark_data = json.load(f)
                print(f"Loaded benchmark data from {jf}")
                break
            except Exception as e:
                print(f"Could not load {jf}: {e}")

    # Generate email body with LLM
    body = None
    if benchmark_data:
        try:
            if LLM_PROVIDER == "anthropic" and os.environ.get("ANTHROPIC_API_KEY"):
                print("Generating email with Anthropic Claude...")
                body = generate_email_with_anthropic(benchmark_data, pipeline_url, pipeline_date)
                if body:
                    print(f"✓ Generated with Anthropic ({len(body)} chars)")
            elif os.environ.get("OPENAI_API_KEY"):
                print("Generating email with OpenAI GPT-4...")
                body = generate_email_with_openai(benchmark_data, pipeline_url, pipeline_date)
                if body:
                    print(f"✓ Generated with OpenAI ({len(body)} chars)")
            else:
                print("No LLM API key available, using fallback")
        except Exception as e:
            print(f"LLM generation failed: {e}")

    if not body:
        print("Using fallback email body")
        body = get_fallback_body(pipeline_url, pipeline_date)

    print("\n--- Generated Email Body ---")
    print(body)
    print("--- End of Body ---\n")

    # Build email
    msg = MIMEMultipart()
    msg["To"] = "wolfram.laube@blauweiss-edv.at"
    msg["Subject"] = f"[CLARISSA] GitLab Runner Benchmark Report {pipeline_date}"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Attach PNG files
    png_files = (
        glob.glob("docs/ci/benchmarks/*.png") + 
        glob.glob("benchmark_reports/*.png") + 
        glob.glob("*.png")
    )
    attached = 0
    for png_path in png_files:
        try:
            with open(png_path, "rb") as f:
                img_data = f.read()
            filename = os.path.basename(png_path)
            img = MIMEImage(img_data, name=filename)
            img.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(img)
            attached += 1
            print(f"Attached: {filename}")
        except Exception as e:
            print(f"Could not attach {png_path}: {e}")

    print(f"Attached {attached} images")

    # Create Gmail draft
    raw_b64 = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    resp = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={"message": {"raw": raw_b64}}
    )

    if resp.status_code in (200, 201):
        print(f"\n✓ Benchmark report draft erstellt (LLM: {LLM_PROVIDER})")
    else:
        print(f"Failed: {resp.text}")
        exit(1)


if __name__ == "__main__":
    main()
