# 🔗 API Reference

## GitLab CI Trigger API

Das Portal nutzt die GitLab CI Trigger API um Pipelines zu starten.

### Endpoint
```
POST https://gitlab.com/api/v4/projects/{project_id}/trigger/pipeline
```

### Parameter

| Parameter | Beschreibung |
|-----------|--------------|
| `token` | CI Trigger Token |
| `ref` | Branch (default: `main`) |
| `variables[KEY]` | Pipeline-Variablen |

### Pipelines

#### Applications Crawler
```bash
curl -X POST \
  -F token=$TRIGGER_TOKEN \
  -F ref=main \
  -F "variables[PIPELINE_TYPE]=crawl" \
  https://gitlab.com/api/v4/projects/77260390/trigger/pipeline
```

#### Applications Matcher
```bash
curl -X POST \
  -F token=$TRIGGER_TOKEN \
  -F ref=main \
  -F "variables[PIPELINE_TYPE]=match" \
  https://gitlab.com/api/v4/projects/77260390/trigger/pipeline
```

#### Gmail Drafter
```bash
curl -X POST \
  -F token=$TRIGGER_TOKEN \
  -F ref=main \
  -F "variables[PIPELINE_TYPE]=drafts" \
  https://gitlab.com/api/v4/projects/77260390/trigger/pipeline
```

### Response
```json
{
  "id": 123456789,
  "web_url": "https://gitlab.com/.../pipelines/123456789",
  "status": "pending"
}
```
