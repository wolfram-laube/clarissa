# ADR-013: Documentation Internationalization (i18n) Architecture

| ADR Info        | Details                                           |
|-----------------|---------------------------------------------------|
| **Status**      | Proposed                                          |
| **Date**        | 2026-01-02                                        |
| **Deciders**    | Wolfram Laube (Architect)                         |
| **Categories**  | Documentation, DevOps, i18n                       |

## Context

### Problem Statement

CLARISSA's documentation needs to support multiple languages to serve an international contributor and user base. The current approach of manually maintaining separate translated copies of documentation files does not scale:

| Current State | Impact |
|---------------|--------|
| 5 languages × 2 files = 10 manually maintained files | High maintenance overhead |
| Every content change requires updating ALL language versions | Error-prone, slow |
| No single source of truth | Translation drift inevitable |
| Translations embedded in final files | Hard to update, no review workflow |
| Pipeline rebuilds all languages on any change | Unnecessary CI/CD overhead |

### Drivers

1. **Scalability**: Adding a new language should be low-effort
2. **Maintainability**: Content changes should be made in ONE place
3. **Quality**: Translations should be reviewable and versioned
4. **Performance**: Pipeline should only rebuild what changed
5. **Flexibility**: Different content types have different i18n needs

## Decision

### Architecture Overview

Implement a **template-based i18n system** with separation of content, structure, and translations:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SOURCE (docs/i18n/)                             │
├─────────────────────────────────────────────────────────────────────────┤
│  templates/                    translations/                            │
│  ├── workflow-slides.jinja2    ├── en.yaml  (English - always complete) │
│  ├── cheatsheet.md.jinja2      ├── de.yaml  (German)                    │
│  └── ...                       ├── vi.yaml  (Vietnamese)                │
│                                ├── ar.yaml  (Arabic + RTL flag)         │
│                                └── is.yaml  (Icelandic)                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      BUILD PIPELINE (CI Job)                            │
├─────────────────────────────────────────────────────────────────────────┤
│  scripts/build_i18n_docs.py                                             │
│  - Load template                                                        │
│  - For each translation file:                                           │
│    - Merge with English fallback                                        │
│    - Apply RTL/font settings if needed                                  │
│    - Render to output format                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    OUTPUT (docs/guides/contributing/)                   │
├─────────────────────────────────────────────────────────────────────────┤
│  Generated at build time (gitignored):                                  │
│  ├── index.html                                                         │
│  ├── workflow-slides-en.html                                            │
│  ├── workflow-slides-de.html                                            │
│  ├── workflow-slides-vi.html                                            │
│  ├── workflow-slides-ar.html                                            │
│  ├── workflow-slides-is.html                                            │
│  ├── cheatsheet-en.md                                                   │
│  └── ...                                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### Content Scope Definition

| Content Type | i18n Strategy | Rationale |
|--------------|---------------|-----------|
| **Contributor onboarding** | Full i18n | Lowers barrier for international contributors |
| **User guides** | Full i18n | End users may not speak English |
| **Technical docs (ADRs)** | English-only | Technical audience, precise terminology |
| **API documentation** | English-only | Developer standard |
| **Code comments** | English-only | Industry standard |
| **CI/CD guides** | English-only | DevOps audience |
| **Error messages** | Configurable | Can be enabled per deployment |

### Translation File Structure

```yaml
# translations/de.yaml
meta:
  language_code: de
  language_name: Deutsch
  language_native: Deutsch
  flag_emoji: 🇩🇪
  direction: ltr
  font_family: "Space Grotesk"  # or override for specific scripts

workflow_slides:
  title: "GitLab Workflow"
  subtitle: "Leitfaden für Mitwirkende"
  nav:
    next: "Weiter"
    previous: "Zurück"
    overview: "Übersicht"
  sections:
    why_workflow:
      title: "Warum dieses Workflow?"
      without:
        title: "Ohne Workflow"
        items:
          - "Commit direkt auf main"
          - "Niemand weiß, wer was macht"
      with:
        title: "Mit Workflow"
        items:
          - "Alle Änderungen mit Issue verknüpft"
          - "Board zeigt wer woran arbeitet"
    # ... more sections

cheatsheet:
  title: "Kurzreferenz"
  tldr: "Issue → Branch → Commit → MR → Merge → Issue schließt automatisch"
  # ... more content
```

### RTL Language Support

For RTL languages (Arabic, Hebrew, Persian, Urdu):

```yaml
# translations/ar.yaml
meta:
  language_code: ar
  language_name: Arabic
  language_native: العربية
  flag_emoji: 🇸🇦
  direction: rtl           # Triggers RTL template variant
  font_family: "Cairo"     # Arabic-optimized font
  
# Template uses conditional:
# {% if meta.direction == 'rtl' %}
#   <html dir="rtl">
#   <!-- RTL-specific CSS -->
# {% endif %}
```

### Fallback Strategy

```
┌─────────────────────────────────────────────────────┐
│           Translation Resolution Order              │
├─────────────────────────────────────────────────────┤
│  1. Requested language (e.g., de.yaml)              │
│  2. English fallback (en.yaml) - ALWAYS complete    │
│  3. Key name as last resort (for debugging)         │
└─────────────────────────────────────────────────────┘
```

This ensures:
- Partial translations are valid (untranslated strings show English)
- English is the single source of truth
- Missing translations are visible in output (easy to spot)

### Pipeline Integration

```yaml
# .gitlab-ci.yml addition
build_i18n_docs:
  stage: build
  image: python:3.11
  script:
    - pip install jinja2 pyyaml
    - python scripts/build_i18n_docs.py
  artifacts:
    paths:
      - docs/guides/contributing/
  rules:
    - changes:
        - docs/i18n/**/*
        - scripts/build_i18n_docs.py
      when: always
    - when: never  # Skip if no i18n changes
```

Key optimization: **Only rebuild when i18n source files change.**

### Adding a New Language

1. Copy `translations/en.yaml` to `translations/XX.yaml`
2. Update `meta` section with language details
3. Translate strings (can be incremental - English fallback works)
4. Commit and push
5. Pipeline generates new language automatically

**Effort: ~1-2 hours for initial translation, no code changes required.**

## Alternatives Considered

### Option A: MkDocs i18n Plugin (mkdocs-static-i18n)

**Pros:**
- Native MkDocs integration
- Established plugin

**Cons:**
- Designed for full-site translation, not partial
- Less control over output format
- Doesn't handle HTML slides well

### Option B: Sphinx with sphinx-intl

**Pros:**
- Industry standard for technical docs
- gettext-based (professional translation tools)

**Cons:**
- Would require migrating from MkDocs
- Overkill for current project size
- Steeper learning curve

### Option C: Hugo with i18n Bundles

**Pros:**
- Fast builds
- Good i18n support

**Cons:**
- Would require complete documentation rewrite
- Different templating language

### Option D: Keep Manual Copies (Current)

**Pros:**
- No infrastructure changes
- Full control per file

**Cons:**
- Does not scale
- Maintenance nightmare
- Translation drift guaranteed

## Consequences

### Positive

1. **Single source of truth** for content structure
2. **Easy to add languages** without code changes
3. **Incremental translation** supported via fallback
4. **Pipeline efficiency** - only rebuilds on i18n changes
5. **Clear separation** of content, structure, and translation
6. **Reviewable translations** - YAML diffs are readable

### Negative

1. **Initial migration effort** to convert existing translations
2. **Template complexity** for dynamic content
3. **Build step required** - can't edit output directly
4. **Learning curve** for contributors editing translations

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Complex templates hard to maintain | Keep templates simple, use includes |
| Translation files get out of sync | CI job to validate completeness |
| RTL layouts break | Dedicated RTL test in pipeline |
| Contributor confusion | Clear CONTRIBUTING guide for i18n |

## Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Create `docs/i18n/` directory structure
- [ ] Build `scripts/build_i18n_docs.py` 
- [ ] Create base templates from existing HTML/MD
- [ ] Extract English strings to `en.yaml`

### Phase 2: Migration (Week 2)
- [ ] Convert existing DE, VI, AR, IS translations to YAML
- [ ] Validate output matches current files
- [ ] Update CI pipeline
- [ ] Remove manual translation files from git

### Phase 3: Documentation (Week 3)
- [ ] Update CONTRIBUTING.md with i18n guide
- [ ] Add translation completeness check to CI
- [ ] Document template authoring

## References

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [GNU gettext Manual](https://www.gnu.org/software/gettext/manual/)
- [W3C Internationalization](https://www.w3.org/International/)
- [RTL Styling Guide](https://rtlstyling.com/)
- Related Issues: #28, #30, #32, #33, #34
