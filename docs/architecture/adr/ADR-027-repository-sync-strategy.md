# ADR-027: Bidirectional Repository Synchronization Strategy

## Status
**Accepted** (2026-01-24)

## Context

The CLARISSA project requires collaboration between team members using different platforms:

- **Wolfram (Austria)**: Primary development on GitLab, where CI/CD pipelines run
- **Mike, Ian, Doug (Houston)**: Prefer GitHub for familiarity and Google Colab integration

Google Colab, essential for GPU-accelerated notebook development, only supports GitHub repositories natively. However, GitLab remains our source of truth for CI/CD, merge requests, and container registry.

### Requirements

1. Team members must be able to push from either platform
2. All branches (not just `main`) must synchronize
3. Colab users must be able to save notebooks back to the repository
4. CI/CD pipelines must run on GitLab
5. Sync must be automatic and near-real-time

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| **GitLab only** | Simple, single source | No Colab integration |
| **GitHub only** | Colab works, familiar to US team | Lose GitLab CI/CD, container registry |
| **Manual sync** | Full control | Error-prone, delays, forgotten syncs |
| **One-way mirror (GitLab→GitHub)** | Simple setup | GitHub changes lost |
| **Bidirectional sync** | Best of both worlds | More complex setup |

## Decision

Implement **bidirectional synchronization** between GitLab and GitHub:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Bidirectional Sync                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   GitLab (primary)                    GitHub (mirror)           │
│   gitlab.com/wolfram_laube/           github.com/wolfram-laube/ │
│   blauweiss_llc/irena                 clarissa                  │
│                                                                 │
│        │                                   │                    │
│        │◄──────── Push Mirror ────────────│                    │
│        │          (all branches)           │                    │
│        │                                   │                    │
│        │─────────► GitHub Actions ────────►│                    │
│        │           (all branches)          │                    │
│        │                                   │                    │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Details

#### GitLab → GitHub (Push Mirror)

- **Mechanism**: GitLab native Push Mirroring feature
- **Trigger**: Every `git push` to GitLab
- **Scope**: All branches, all tags
- **Latency**: Immediate for real pushes, 1-5 minutes for API commits
- **Authentication**: GitHub Personal Access Token stored in mirror config

```
Mirror ID: 2982763
URL: https://github.com/wolfram-laube/clarissa.git
only_protected_branches: false
```

#### GitHub → GitLab (GitHub Actions)

- **Mechanism**: GitHub Actions workflow triggered on push
- **Trigger**: Any push to any branch
- **Scope**: Current branch + tags
- **Latency**: ~30 seconds
- **Authentication**: GitLab PAT stored as GitHub Secret (`GITLAB_TOKEN`)

```yaml
# .github/workflows/mirror-to-gitlab.yml
name: Mirror to GitLab

on:
  push:
    branches: [ '**' ]
  delete:

jobs:
  mirror-push:
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Push branch to GitLab
        env:
          GITLAB_TOKEN: ${{ secrets.GITLAB_TOKEN }}
        run: |
          git remote add gitlab https://oauth2:${GITLAB_TOKEN}@gitlab.com/wolfram_laube/blauweiss_llc/irena.git
          BRANCH=${GITHUB_REF#refs/heads/}
          git push gitlab "$BRANCH" --force
          git push gitlab --tags --force 2>/dev/null || true

  mirror-delete:
    if: github.event_name == 'delete' && github.event.ref_type == 'branch'
    runs-on: ubuntu-latest
    steps:
      - name: Delete branch on GitLab
        env:
          GITLAB_TOKEN: ${{ secrets.GITLAB_TOKEN }}
        run: |
          curl -s --request DELETE \
            --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
            "https://gitlab.com/api/v4/projects/77260390/repository/branches/${{ github.event.ref }}"
```

### Workflow for Team Members

1. **Clone from either repo** (both work identically)
2. **Create feature branch** (`git checkout -b feature/xyz`)
3. **Make changes and commit**
4. **Push to origin** (whichever you cloned from)
5. **Create MR on GitLab** (preferred, even for GitHub pushes)
6. **CI/CD runs on GitLab**
7. **Merge on GitLab**
8. **Both repos sync automatically**

### Colab Workflow

1. Open notebook via Colab badge in documentation
2. Make changes in Colab
3. File → Save a copy in GitHub
4. Select `wolfram-laube/clarissa`
5. Create new branch (e.g., `colab/notebook-update`)
6. Commit
7. Branch syncs to GitLab automatically
8. Create MR on GitLab for review

## Consequences

### Positive

- **Seamless collaboration**: Team can use preferred platform
- **Colab integration**: GPU notebooks work without friction
- **CI/CD intact**: All pipelines remain on GitLab
- **No manual sync**: Automation prevents human error
- **Branch support**: Feature branch workflow preserved

### Negative

- **Sync window**: ~30-60 second window where repos differ
- **Conflict potential**: Simultaneous edits to same file can conflict
- **Two sets of credentials**: GitHub PAT + GitLab PAT required
- **Debugging complexity**: Issues may need investigation on both platforms

### Mitigations

| Risk | Mitigation |
|------|------------|
| Merge conflicts | Team coordination, feature branches, no direct `main` commits |
| Credential leakage | Tokens stored as secrets, not in code |
| Sync failures | Monitoring via GitLab mirror status, GitHub Actions notifications |
| Confusion about which repo | Documentation clearly states "push to whichever you cloned from" |

## References

- [GitLab Push Mirroring Documentation](https://docs.gitlab.com/ee/user/project/repository/mirror/push.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [CLARISSA Tutorials - Git Workflow](https://irena-40cc50.gitlab.io/tutorials/#git-workflow-contributing-changes)
