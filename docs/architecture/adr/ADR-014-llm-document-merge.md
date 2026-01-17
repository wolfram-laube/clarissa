# ADR-014: LLM-Powered Multi-Format Document Merge Pipeline

## Status
**Accepted** (Implemented January 2026)

!!! success "Implementation Complete"
    This ADR has been implemented. See [CI/CD Publication Workflow](../publications/ci-workflow.md) for operational documentation.

## Context

The SPE Europe 2026 abstract is being co-authored by multiple contributors using different document formats:
- **Doug Perschke**: Works in Microsoft Word (DOCX)
- **Mike + Wolfram**: Work in Markdown (MD)

Traditional version control (Git) handles text-based merges well but struggles with:
1. Binary formats (DOCX)
2. Semantic equivalence across formats (same content, different markup)
3. Structural changes that are logically compatible but textually conflicting

We need a system that can:
- Accept contributions in native formats (don't force Doug to learn Markdown)
- Detect and merge semantic changes intelligently
- Produce consistent outputs in all required formats
- Run automatically in CI/CD

## Decision

Implement an **LLM-Powered Semantic Merge Pipeline** in GitLab CI/CD that:

1. **Normalizes** all input formats to a common intermediate representation
2. **Compares** versions semantically using an LLM
3. **Merges** changes with conflict detection and resolution
4. **Generates** all output formats from the merged source

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GitLab Repository                            │
├─────────────────────────────────────────────────────────────────────┤
│  conference/spe-europe-2026/                                        │
│  ├── sources/                    ← Original contributions           │
│  │   ├── doug/                                                      │
│  │   │   └── abstract-perschke.docx                                │
│  │   ├── mike/                                                      │
│  │   │   └── abstract-mike.md                                      │
│  │   └── wolfram/                                                   │
│  │       └── abstract-wolfram.md                                   │
│  │                                                                  │
│  ├── canonical/                  ← Single Source of Truth          │
│  │   ├── abstract.md             (LLM-merged, authoritative)       │
│  │   ├── metadata.yaml           (authors, versions, decisions)    │
│  │   └── merge-history.json      (what was merged, when, how)      │
│  │                                                                  │
│  └── outputs/                    ← Generated from canonical        │
│      ├── abstract.pdf                                              │
│      ├── abstract.html                                             │
│      ├── abstract.tex                                              │
│      ├── abstract.typ                                              │
│      └── abstract.docx           (for Doug to review)              │
└─────────────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

```yaml
stages:
  - detect
  - normalize
  - compare
  - merge
  - generate
  - notify
```

#### Stage 1: Detect Changes
```yaml
detect_changes:
  stage: detect
  script:
    - |
      # Detect which source files changed
      CHANGED=$(git diff --name-only $CI_COMMIT_BEFORE_SHA $CI_COMMIT_SHA)
      echo "Changed files: $CHANGED"
      
      # Categorize by author
      echo "$CHANGED" | grep "sources/doug" && echo "DOUG_CHANGED=true" >> changes.env
      echo "$CHANGED" | grep "sources/mike" && echo "MIKE_CHANGED=true" >> changes.env
      echo "$CHANGED" | grep "sources/wolfram" && echo "WOLFRAM_CHANGED=true" >> changes.env
  artifacts:
    reports:
      dotenv: changes.env
```

#### Stage 2: Normalize to Common Format
```yaml
normalize:
  stage: normalize
  script:
    - |
      # Convert DOCX to Markdown
      if [ -f sources/doug/*.docx ]; then
        pandoc sources/doug/*.docx -o normalized/doug.md --wrap=none
      fi
      
      # Copy MD files (already normalized)
      cp sources/mike/*.md normalized/mike.md 2>/dev/null || true
      cp sources/wolfram/*.md normalized/wolfram.md 2>/dev/null || true
      
      # Extract text-only version for LLM comparison
      for f in normalized/*.md; do
        pandoc "$f" -t plain -o "${f%.md}.txt"
      done
```

#### Stage 3: LLM Semantic Comparison
```yaml
llm_compare:
  stage: compare
  script:
    - |
      # Call Claude/GPT API to analyze differences
      python3 scripts/llm_compare.py \
        --base canonical/abstract.md \
        --inputs normalized/*.md \
        --output comparison-report.json
```

#### Stage 4: LLM Semantic Merge
```yaml
llm_merge:
  stage: merge
  script:
    - |
      # Call Claude/GPT API to perform intelligent merge
      python3 scripts/llm_merge.py \
        --base canonical/abstract.md \
        --inputs normalized/*.md \
        --comparison comparison-report.json \
        --output canonical/abstract.md \
        --history canonical/merge-history.json
  when: manual  # Require human approval for merges
```

#### Stage 5: Generate All Formats
```yaml
generate_outputs:
  stage: generate
  script:
    - |
      # Generate all output formats from canonical source
      pandoc canonical/abstract.md -o outputs/abstract.pdf
      pandoc canonical/abstract.md -o outputs/abstract.html
      pandoc canonical/abstract.md -o outputs/abstract.tex
      pandoc canonical/abstract.md -o outputs/abstract.docx
      # ... typst, etc.
```

### LLM Merge Script (Core Logic)

```python
#!/usr/bin/env python3
"""
llm_merge.py - Semantic document merge using LLM
"""

import anthropic
import json
from pathlib import Path

MERGE_PROMPT = """
You are a technical document merge assistant. You have:

1. BASE VERSION (current canonical document):
<base>
{base_content}
</base>

2. CONTRIBUTOR CHANGES:
{contributor_sections}

Your task:
1. Identify what each contributor added, modified, or removed
2. Merge changes semantically (not just textually)
3. Resolve conflicts by:
   - Preferring more specific/detailed content
   - Combining complementary additions
   - Flagging true conflicts for human review
4. Preserve the best writing from each contributor
5. Maintain consistent terminology and style

Output format:
```json
{{
  "merged_document": "... the full merged markdown ...",
  "changes_incorporated": [
    {{"contributor": "doug", "change": "Added voice-first design section", "action": "incorporated"}},
    ...
  ],
  "conflicts_requiring_review": [
    {{"section": "Architecture", "conflict": "Doug says 6 layers, Wolfram says 4", "suggestion": "Use 6-layer (more detailed)"}}
  ],
  "summary": "Brief description of merge"
}}
```
"""

def merge_documents(base_path, input_paths, output_path):
    client = anthropic.Anthropic()
    
    base_content = Path(base_path).read_text()
    
    contributor_sections = ""
    for input_path in input_paths:
        contributor = Path(input_path).stem
        content = Path(input_path).read_text()
        contributor_sections += f"\n<{contributor}>\n{content}\n</{contributor}>\n"
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": MERGE_PROMPT.format(
                base_content=base_content,
                contributor_sections=contributor_sections
            )
        }]
    )
    
    result = json.loads(response.content[0].text)
    
    # Write merged document
    Path(output_path).write_text(result["merged_document"])
    
    # Log merge history
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    result = merge_documents(args.base, args.inputs, args.output)
    print(json.dumps(result, indent=2))
```

## Workflow for Contributors

### Doug (DOCX User)
1. Downloads latest `outputs/abstract.docx` from GitLab
2. Makes edits in Word with Track Changes
3. Uploads to `sources/doug/abstract-perschke.docx`
4. Pipeline detects change, normalizes, compares, proposes merge

### Mike/Wolfram (Markdown Users)
1. Edit `sources/mike/abstract-mike.md` or `sources/wolfram/abstract-wolfram.md`
2. Commit and push
3. Pipeline handles merge into canonical

### Review Process
1. Pipeline creates Merge Request with diff preview
2. All authors can review proposed merge
3. Conflicts flagged for discussion
4. Manual approval triggers final merge

## Alternatives Considered

### 1. Force Single Format
- **Rejected**: Doug shouldn't have to learn Markdown
- Friction reduces contribution quality

### 2. Google Docs / Overleaf
- **Rejected**: External dependency, not Git-native
- Loses version control benefits

### 3. Pure Pandoc Conversion (No LLM)
- **Rejected**: Can't handle semantic conflicts
- Loses nuanced editorial decisions

### 4. Manual Merge by Designated Editor
- **Partially Accepted**: Human approval still required
- LLM reduces manual effort by 90%

## Consequences

### Positive
- Each author works in preferred format
- Semantic understanding of changes (not just text diff)
- Automated conflict detection
- Full audit trail of merge decisions
- Consistent output generation

### Negative
- API costs for LLM calls (~$0.10-0.50 per merge)
- Requires Claude/OpenAI API key in CI/CD
- Potential for LLM errors (mitigated by human review)
- Added pipeline complexity

### Risks
- LLM hallucination during merge → Mitigated by human approval gate
- API rate limits → Use caching, batch changes
- Format conversion loss → Test thoroughly, preserve originals

## Implementation Plan

1. **Phase 1**: Set up directory structure + manual merge workflow
2. **Phase 2**: Add Pandoc normalization pipeline
3. **Phase 3**: Integrate LLM comparison (read-only)
4. **Phase 4**: Enable LLM merge with human approval
5. **Phase 5**: Add Slack/Email notifications

## References

- [Pandoc User's Guide](https://pandoc.org/MANUAL.html)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
