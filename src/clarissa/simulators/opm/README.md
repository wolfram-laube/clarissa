# OPM Flow Docker Image

CLARISSA's containerized OPM Flow simulator.

## Version

Current version: See `VERSION` file.

## Semantic Versioning

We follow [semver](https://semver.org/):

| Bump | When |
|------|------|
| **Patch** (1.0.x) | Bugfix, security update, OPM patch update |
| **Minor** (1.x.0) | New OPM features, new entrypoint options, backward-compatible changes |
| **Major** (x.0.0) | Breaking changes to entrypoint API, base image change, incompatible OPM upgrade |

## Release Process

1. Update `VERSION` file
2. Commit: `chore(opm): bump version to X.Y.Z`
3. Tag: `git tag opm-flow-vX.Y.Z`
4. Push: `git push origin opm-flow-vX.Y.Z`

CI automatically builds and pushes:
- `registry.gitlab.com/.../opm-flow:vX.Y.Z`
- `registry.gitlab.com/.../opm-flow:latest`

## Usage

```bash
docker pull registry.gitlab.com/wolfram_laube/blauweiss_llc/irena/opm-flow:latest

docker run --rm -v $(pwd):/data opm-flow:latest /data/MYMODEL.DATA
```

## Build Locally

```bash
docker build -t opm-flow:local .
```
