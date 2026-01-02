# 📚 CLARISSA Guides

Welcome to the CLARISSA documentation guides. This section contains practical how-to documentation for contributors and users.

## 🚀 Getting Started

New to the project? Start here:

| Guide | Description | Format |
|-------|-------------|--------|
| [GitLab Workflow (Language Selector)](contributing/index.html) | Complete contributor onboarding with visual examples | HTML Slides |
| [Workflow Cheatsheet](contributing/cheatsheet-en.md) | Quick reference for daily use | Markdown |
| [Project Management](project-management.md) | Issue tracking, labels, and board usage | Markdown |

## 🌍 Language Versions

Documentation is available in multiple languages:

- **English**: [Workflow Slides (EN)](contributing/workflow-slides-en.html) • [Cheatsheet (EN)](contributing/cheatsheet-en.md)
- **Deutsch**: [Workflow Slides (DE)](contributing/workflow-slides-de.html) • [Cheatsheet (DE)](contributing/cheatsheet-de.md)
- **Tiếng Việt**: [Workflow Slides (VI)](contributing/workflow-slides-vi.html) • [Cheatsheet (VI)](contributing/cheatsheet-vi.md)
- **العربية**: [Workflow Slides (AR)](contributing/workflow-slides-ar.html) • [Cheatsheet (AR)](contributing/cheatsheet-ar.md)

## 📋 Guide Index

### Contributing

Everything you need to contribute code to CLARISSA:

- **[GitLab Workflow Slides](contributing/index.html)** - Interactive presentation covering:
    - Issue board usage
    - Branch naming conventions
    - Conventional Commits format
    - Merge request best practices
    - Automatic issue closing

- **Workflow Cheatsheets** - One-page quick reference in [EN](contributing/cheatsheet-en.md) | [DE](contributing/cheatsheet-de.md) | [VI](contributing/cheatsheet-vi.md)

### Project Management

- **[Project Management Guide](project-management.md)** - Detailed documentation of:
    - Label taxonomy (type, priority, component, workflow)
    - Milestone structure
    - Issue templates
    - Board configuration

## 🔗 Quick Links

| Resource | Description |
|----------|-------------|
| [Issue Board](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/boards) | Kanban board for task tracking |
| [All Issues](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/issues) | Full issue list |
| [Merge Requests](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/merge_requests) | Open MRs |
| [CI/CD Pipelines](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/pipelines) | Build status |

## ➕ Adding a New Language

To add a new language translation:

1. Create `workflow-slides-XX.html` (copy from any existing language)
2. Create `cheatsheet-XX.md` (copy from any existing language)
3. Update `contributing/index.html` language selector
4. Update this index page
5. Update language switcher in all `workflow-slides-*.html` files

Where `XX` is the [ISO 639-1 language code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes).

## ❓ Need Help?

- Create an issue with label `help-wanted`
- Check the [Architecture Documentation](../architecture/README.md) for technical details
- Review [ADRs](../architecture/adr/index.md) for design decisions
