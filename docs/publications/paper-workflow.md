# 📝 Paper Workflow Guide (Legacy)

!!! warning "Deprecated Documentation"
    **This document describes the legacy LaTeX-only workflow for IJACSA 2026.**
    
    For the current CI/CD pipeline documentation covering:
    
    - LLM-powered multi-author merge
    - Mermaid diagram rendering
    - Automated PDF generation
    - GitLab Pages deployment
    
    **→ See [CI/CD Publication Workflow](ci-workflow.md)**

---

How to edit, review, and publish CLARISSA research papers.

!!! note "Scope"
    This guide applies only to the **IJACSA 2026 LaTeX paper**. For SPE Europe 2026, see [CI/CD Workflow](ci-workflow.md).

---

## Quick Reference

| Task | Command/Action |
|------|----------------|
| Edit paper | Edit `.tex` in `conference/ijacsa-2026/` |
| Build PDF | `pdflatex CLARISSA_Paper_IJACSA.tex` |
| Update figure | Edit `.mermaid`, render to `.png` |
| Submit changes | Create MR with `docs:` prefix |

---

## 1. Repository Structure

```
conference/
├── spe-europe-2026/canonical/       # SPE Europe 2026 abstract
└── ijacsa-2026/
    ├── CLARISSA_Paper_IJACSA.tex    # LaTeX source (PRIMARY)
    ├── CLARISSA_Paper_IJACSA.pdf    # Compiled PDF
    ├── CLARISSA_Paper_IJACSA.docx   # Word export (for co-authors)
    ├── figures/
    │   ├── *.mermaid                # Diagram sources
    │   └── *.png                    # Rendered images
    └── supplementary/
        ├── CLARISSA_Abstract_CFP.pdf
        └── CLARISSA_Architecture_Summary_Detailed.pdf
```

**Source of Truth:** The `.tex` file is authoritative. PDF and DOCX are generated artifacts.

---

## 2. Editing the Paper

### Setup (first time)

```bash
# Clone repo
git clone git@gitlab.com:wolfram_laube/blauweiss_llc/clarissa.git
cd clarissa

# Install LaTeX (Ubuntu/Debian)
sudo apt install texlive-latex-recommended texlive-fonts-recommended texlive-latex-extra

# Or on macOS
brew install --cask mactex
```

### Make Changes

```bash
# 1. Create branch
git checkout -b docs/paper-update-section-3

# 2. Edit the paper
cd conference/ijacsa-2026
# Edit CLARISSA_Paper_IJACSA.tex with your editor

# 3. Build PDF
pdflatex CLARISSA_Paper_IJACSA.tex
pdflatex CLARISSA_Paper_IJACSA.tex  # Run twice for references

# 4. Commit both source and PDF
git add CLARISSA_Paper_IJACSA.tex CLARISSA_Paper_IJACSA.pdf
git commit -m "docs(paper): update section 3 methodology"

# 5. Push and create MR
git push -u origin docs/paper-update-section-3
```

### Commit Message Convention

```
docs(paper): <what changed>

Examples:
- docs(paper): add evaluation results table
- docs(paper): fix typo in abstract
- docs(paper): update architecture figure
- docs(paper): revise related work section
```

---

## 3. Updating Figures

Figures are created with Mermaid and rendered to PNG.

### Edit a Figure

```bash
cd conference/ijacsa-2026/figures

# 1. Edit the Mermaid source
nano CLARISSA_Figure1_Architecture.mermaid

# 2. Render to PNG (requires mmdc - mermaid CLI)
mmdc -i CLARISSA_Figure1_Architecture.mermaid -o CLARISSA_Figure1_Architecture.png -b white

# 3. Commit both
git add *.mermaid *.png
git commit -m "docs(paper): update architecture diagram"
```

### Install Mermaid CLI

```bash
npm install -g @mermaid-js/mermaid-cli
```

---

## 4. Review Process

### For Authors

1. Create MR with clear description of changes
2. Request review from co-authors
3. Address feedback in new commits
4. Squash merge when approved

### For Reviewers

When reviewing paper changes:

- [ ] LaTeX compiles without errors
- [ ] PDF is included and matches source
- [ ] Figures are updated if referenced content changed
- [ ] References are complete
- [ ] No tracked changes or comments left in

---

## 5. Generating Word Version

Some co-authors or journals need Word format:

```bash
# Using pandoc
pandoc CLARISSA_Paper_IJACSA.tex -o CLARISSA_Paper_IJACSA.docx

# Or use online converter like latex2rtf
```

**Note:** Word version may need manual formatting fixes.

---

## 6. Pre-Submission Checklist

Before submitting to journal/conference:

- [ ] All authors listed correctly
- [ ] Affiliations are current
- [ ] Abstract within word limit
- [ ] Figures are high resolution (300 DPI min)
- [ ] References formatted per journal style
- [ ] Supplementary materials prepared
- [ ] PDF file size within limits
- [ ] No "TODO" or "FIXME" comments remaining

---

## 7. Version Control Best Practices

### Do

- ✅ Commit `.tex` and `.pdf` together
- ✅ Use meaningful commit messages
- ✅ Create branches for major revisions
- ✅ Keep figure sources (`.mermaid`) in sync with PNGs

### Don't

- ❌ Commit only PDF without source
- ❌ Leave merge conflicts in LaTeX
- ❌ Force push to shared branches
- ❌ Edit PDF directly (always edit `.tex`)

---

## 8. File Naming Convention

```
CLARISSA_Paper_<VENUE>.tex      # Main paper
CLARISSA_Paper_<VENUE>.pdf      # Compiled
CLARISSA_Figure<N>_<Name>.png   # Figures
CLARISSA_Table<N>_<Name>.tex    # Tables (if separate)
```

Examples:
- `CLARISSA_Paper_IJACSA.tex`
- `CLARISSA_Figure1_Architecture.png`
- `CLARISSA_Figure2_NLP_Pipeline.png`

---

## Quick Links

| Resource | Link |
|----------|------|
| Paper (PDF) | [Download](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/raw/main/conference/ijacsa-2026/CLARISSA_Paper_IJACSA.pdf) |
| LaTeX Source | [View](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/blob/main/conference/ijacsa-2026/CLARISSA_Paper_IJACSA.tex) |
| Figures | [Browse](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/tree/main/conference/ijacsa-2026/figures) |
| Abstract | [Read](https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/blob/main/conference/spe-europe-2026/canonical/full-paper.md) |
