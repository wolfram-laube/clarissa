#!/usr/bin/env python3
"""Generate publications index HTML for GitLab Pages."""
from pathlib import Path

HTML = '''<!DOCTYPE html>
<html><head><title>CLARISSA Publications</title>
<meta charset="UTF-8">
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:900px;margin:50px auto;padding:20px}
h1{color:#1a365d;border-bottom:2px solid #3182ce;padding-bottom:10px}
.conf{background:#f7fafc;padding:20px;margin:20px 0;border-radius:8px;border-left:4px solid #3182ce}
.conf h2{margin-top:0;color:#2c5282}
a{color:#3182ce}
.links{margin-top:15px}
.links a{display:inline-block;margin-right:15px;margin-bottom:10px;padding:8px 16px;background:#ebf8ff;border-radius:4px;text-decoration:none}
.links a:hover{background:#bee3f8}
.badge{font-size:0.8em;color:#718096;margin-top:10px}
</style></head><body>
<h1>CLARISSA Publications</h1>
<p>Review copies for internal distribution. Updated automatically on each push to main.</p>

<div class="conf">
<h2>SPE Europe Energy Conference 2026</h2>
<p><strong>CLARISSA: A Conversational User Interface for Democratizing Reservoir Simulation</strong></p>
<p>Douglas Perschke, Michal Matejka, Wolfram Laube</p>
<div class="links">
<a href="spe-europe-2026/submission-form.pdf">Submission Abstract (PDF)</a>
<a href="spe-europe-2026/submission-form.html">Interactive HTML</a>
<a href="spe-europe-2026/full-paper.pdf">Full Paper (PDF)</a>
<a href="spe-europe-2026/abstract-with-diagrams.pdf">Legacy Abstract (PDF)</a>
</div>
<p class="badge">Category: 05.6 ML/AI in Subsurface Operations</p>
</div>

<div class="conf">
<h2>IJACSA 2026</h2>
<p><strong>CLARISSA: A Conversational Language Agent for Reservoir Integrated Simulation System Analysis</strong></p>
<p>Wolfram Laube, Douglas Perschke, Michal Matejka</p>
<div class="links">
<a href="ijacsa-2026/CLARISSA_Paper_IJACSA.pdf">Full Paper (PDF)</a>
</div>
</div>

<hr style="margin-top:40px;border:none;border-top:1px solid #e2e8f0">
<p style="color:#718096;font-size:0.9em">
Source: <a href="https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/tree/main/conference">GitLab</a>
</p>
</body></html>'''

if __name__ == '__main__':
    output = Path('public/publications/index.html')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(HTML)
    print(f'✅ Generated {output}')
