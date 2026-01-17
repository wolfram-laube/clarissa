#!/usr/bin/env python3
"""
CLARISSA GitLab Runner Benchmark Report Generator
Generates versionierte benchmark reports with visualizations.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import seaborn as sns
from datetime import datetime
from pathlib import Path
import numpy as np

# Benchmark data from Pipeline 2268913615 (2026-01-17)
BENCHMARK_DATA = {
    "metadata": {
        "pipeline_id": 2268913615,
        "timestamp": "2026-01-17T15:22:03Z",
        "version": "1.0.0",
        "git_ref": "main",
        "total_runners": 12,
        "successful_runners": 11
    },
    "results": [
        {"machine": "Mac #1", "executor": "shell", "job": "benchmark-mac-group-shell", "duration_s": 20.8, "status": "success"},
        {"machine": "Mac #1", "executor": "docker", "job": "benchmark-mac-docker", "duration_s": 46.9, "status": "success"},
        {"machine": "Mac #1", "executor": "k8s", "job": "benchmark-mac-k8s", "duration_s": 45.3, "status": "success"},
        {"machine": "Mac #2", "executor": "shell", "job": "benchmark-mac2-shell", "duration_s": 7.2, "status": "success"},
        {"machine": "Mac #2", "executor": "docker", "job": "benchmark-mac2-docker", "duration_s": 16.4, "status": "success"},
        {"machine": "Mac #2", "executor": "k8s", "job": "benchmark-mac2-k8s", "duration_s": 18.9, "status": "success"},
        {"machine": "Linux Yoga", "executor": "shell", "job": "benchmark-linux-shell", "duration_s": 5.7, "status": "success"},
        {"machine": "Linux Yoga", "executor": "docker", "job": "benchmark-linux-docker", "duration_s": 8.4, "status": "success"},
        {"machine": "Linux Yoga", "executor": "k8s", "job": "benchmark-linux-k8s", "duration_s": 11.4, "status": "success"},
        {"machine": "GCP VM", "executor": "shell", "job": "benchmark-gcp-shell", "duration_s": 6.4, "status": "success"},
        {"machine": "GCP VM", "executor": "docker", "job": "benchmark-gcp-docker", "duration_s": 27.0, "status": "success"},
        {"machine": "GCP VM", "executor": "k8s", "job": "benchmark-gcp-k8s", "duration_s": 12.8, "status": "failed", "error": "K8s not configured on GCP VM"}
    ],
    "test_spec": {
        "cpu_test": "Prime count to 100,000",
        "disk_test": "50MB sequential write",
        "python_version": "3.11"
    }
}


def create_visualizations(data: dict, output_dir: Path):
    """Generate benchmark visualizations."""
    
    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette("husl")
    
    df = pd.DataFrame(data["results"])
    df_success = df[df["status"] == "success"]
    
    # === Chart 1: Grouped Bar Chart by Machine ===
    fig, ax = plt.subplots(figsize=(12, 6))
    
    machines = ["Mac #1", "Mac #2", "Linux Yoga", "GCP VM"]
    executors = ["shell", "docker", "k8s"]
    x = np.arange(len(machines))
    width = 0.25
    
    colors = {"shell": "#2ecc71", "docker": "#3498db", "k8s": "#9b59b6"}
    
    for i, executor in enumerate(executors):
        durations = []
        for machine in machines:
            row = df[(df["machine"] == machine) & (df["executor"] == executor)]
            if len(row) > 0 and row.iloc[0]["status"] == "success":
                durations.append(row.iloc[0]["duration_s"])
            else:
                durations.append(0)  # Failed or missing
        
        bars = ax.bar(x + i*width, durations, width, label=executor.capitalize(), color=colors[executor])
        
        # Add value labels
        for bar, dur in zip(bars, durations):
            if dur > 0:
                ax.annotate(f'{dur:.1f}s',
                           xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('Machine', fontsize=12)
    ax.set_ylabel('Duration (seconds)', fontsize=12)
    ax.set_title('GitLab Runner Benchmark - Duration by Machine and Executor', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(machines)
    ax.legend(title="Executor")
    ax.set_ylim(0, max(df_success["duration_s"]) * 1.2)
    
    # Add note about failed runner
    ax.annotate('* GCP K8s: Not configured', xy=(0.98, 0.02), xycoords='axes fraction',
                ha='right', va='bottom', fontsize=9, fontstyle='italic', color='gray')
    
    plt.tight_layout()
    plt.savefig(output_dir / "benchmark_by_machine.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    # === Chart 2: Heatmap ===
    fig, ax = plt.subplots(figsize=(10, 6))
    
    pivot_data = df.pivot(index="machine", columns="executor", values="duration_s")
    pivot_data = pivot_data.reindex(machines)
    pivot_data = pivot_data[executors]
    
    # Create mask for failed jobs
    mask = df.pivot(index="machine", columns="executor", values="status")
    mask = mask.reindex(machines)[executors]
    mask_array = mask != "success"
    
    sns.heatmap(pivot_data, annot=True, fmt=".1f", cmap="RdYlGn_r", 
                ax=ax, mask=mask_array, cbar_kws={'label': 'Duration (s)'},
                linewidths=0.5, annot_kws={"size": 12})
    
    ax.set_title('Runner Performance Heatmap (seconds, lower is better)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Executor Type', fontsize=12)
    ax.set_ylabel('Machine', fontsize=12)
    
    # Mark failed cell
    for i, machine in enumerate(machines):
        for j, executor in enumerate(executors):
            if mask.loc[machine, executor] != "success":
                ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=True, color='lightgray', alpha=0.8))
                ax.text(j + 0.5, i + 0.5, 'N/A', ha='center', va='center', fontsize=10, color='gray')
    
    plt.tight_layout()
    plt.savefig(output_dir / "benchmark_heatmap.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    # === Chart 3: Executor Comparison (Box Plot) ===
    fig, ax = plt.subplots(figsize=(8, 6))
    
    sns.boxplot(data=df_success, x="executor", y="duration_s", ax=ax, palette=colors, order=executors)
    sns.stripplot(data=df_success, x="executor", y="duration_s", ax=ax, color='black', alpha=0.5, order=executors)
    
    ax.set_xlabel('Executor Type', fontsize=12)
    ax.set_ylabel('Duration (seconds)', fontsize=12)
    ax.set_title('Performance Distribution by Executor Type', fontsize=14, fontweight='bold')
    ax.set_xticklabels(['Shell', 'Docker', 'Kubernetes'])
    
    plt.tight_layout()
    plt.savefig(output_dir / "benchmark_by_executor.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    # === Chart 4: Summary Stats ===
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    
    for idx, executor in enumerate(executors):
        exec_data = df_success[df_success["executor"] == executor]["duration_s"]
        
        ax = axes[idx]
        bars = ax.bar(df_success[df_success["executor"] == executor]["machine"], 
                     exec_data.values, color=colors[executor])
        
        ax.axhline(y=exec_data.mean(), color='red', linestyle='--', label=f'Mean: {exec_data.mean():.1f}s')
        ax.set_title(f'{executor.capitalize()} Executor', fontsize=12, fontweight='bold')
        ax.set_ylabel('Duration (s)')
        ax.tick_params(axis='x', rotation=45)
        ax.legend(loc='upper right', fontsize=9)
        
        for bar in bars:
            ax.annotate(f'{bar.get_height():.1f}',
                       xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=9)
    
    plt.suptitle('Detailed Executor Performance Comparison', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / "benchmark_detailed.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    return ["benchmark_by_machine.png", "benchmark_heatmap.png", "benchmark_by_executor.png", "benchmark_detailed.png"]


def generate_markdown_report(data: dict, charts: list, output_dir: Path) -> str:
    """Generate Markdown report."""
    
    meta = data["metadata"]
    results = data["results"]
    df = pd.DataFrame(results)
    df_success = df[df["status"] == "success"]
    
    # Calculate statistics
    stats = {
        "fastest": df_success.loc[df_success["duration_s"].idxmin()],
        "slowest": df_success.loc[df_success["duration_s"].idxmax()],
        "mean": df_success["duration_s"].mean(),
        "median": df_success["duration_s"].median(),
    }
    
    # Stats by executor
    exec_stats = df_success.groupby("executor")["duration_s"].agg(["mean", "min", "max"]).round(1)
    
    report = f"""# CLARISSA GitLab Runner Benchmark Report

**Version:** {meta['version']}  
**Pipeline:** [{meta['pipeline_id']}](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/pipelines/{meta['pipeline_id']})  
**Timestamp:** {meta['timestamp']}  
**Git Ref:** `{meta['git_ref']}`  

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Runners | {meta['total_runners']} |
| Successful | {meta['successful_runners']} |
| Failed | {meta['total_runners'] - meta['successful_runners']} |
| Fastest Runner | {stats['fastest']['job']} ({stats['fastest']['duration_s']:.1f}s) |
| Slowest Runner | {stats['slowest']['job']} ({stats['slowest']['duration_s']:.1f}s) |
| Mean Duration | {stats['mean']:.1f}s |
| Median Duration | {stats['median']:.1f}s |

---

## Test Specification

- **CPU Test:** {data['test_spec']['cpu_test']}
- **Disk Test:** {data['test_spec']['disk_test']}
- **Python Version:** {data['test_spec']['python_version']}

---

## Visualizations

### Performance by Machine and Executor
![Benchmark by Machine](benchmark_by_machine.png)

### Performance Heatmap
![Heatmap](benchmark_heatmap.png)

### Distribution by Executor Type
![By Executor](benchmark_by_executor.png)

### Detailed Comparison
![Detailed](benchmark_detailed.png)

---

## Results Matrix

| Machine | Shell | Docker | Kubernetes |
|---------|-------|--------|------------|
"""
    
    machines = ["Mac #1", "Mac #2", "Linux Yoga", "GCP VM"]
    executors = ["shell", "docker", "k8s"]
    
    for machine in machines:
        row = f"| {machine} |"
        for executor in executors:
            match = df[(df["machine"] == machine) & (df["executor"] == executor)]
            if len(match) > 0:
                r = match.iloc[0]
                if r["status"] == "success":
                    row += f" {r['duration_s']:.1f}s |"
                else:
                    row += f" ❌ Failed |"
            else:
                row += " - |"
        report += row + "\n"
    
    report += f"""
---

## Statistics by Executor Type

| Executor | Mean | Min | Max |
|----------|------|-----|-----|
| Shell | {exec_stats.loc['shell', 'mean']:.1f}s | {exec_stats.loc['shell', 'min']:.1f}s | {exec_stats.loc['shell', 'max']:.1f}s |
| Docker | {exec_stats.loc['docker', 'mean']:.1f}s | {exec_stats.loc['docker', 'min']:.1f}s | {exec_stats.loc['docker', 'max']:.1f}s |
| K8s | {exec_stats.loc['k8s', 'mean']:.1f}s | {exec_stats.loc['k8s', 'min']:.1f}s | {exec_stats.loc['k8s', 'max']:.1f}s |

---

## Observations

1. **Shell executors are fastest** - Minimal overhead, direct execution
2. **Linux Yoga shows best overall performance** - Consistent across all executor types
3. **Mac #1 shows higher latency** - Possible resource constraints or network latency
4. **GCP K8s not configured** - Kubernetes cluster not available on GCP VM

---

## How to Run Benchmarks

### Via GitLab UI
1. Navigate to CI/CD → Pipelines
2. Click "Run pipeline" on `main` branch
3. Find benchmark jobs (prefixed with `benchmark-`)
4. Click "Play" button on each benchmark job

### Via GitLab API
```bash
# Create pipeline
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \\
  --request POST \\
  "https://gitlab.com/api/v4/projects/77260390/pipeline?ref=main"

# List and trigger benchmark jobs
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \\
  "https://gitlab.com/api/v4/projects/77260390/pipelines/<PIPELINE_ID>/jobs" | \\
  jq '.[] | select(.name | startswith("benchmark-"))'

# Trigger a specific job
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \\
  --request POST \\
  "https://gitlab.com/api/v4/projects/77260390/jobs/<JOB_ID>/play"
```

---

## Appendix: Raw Data

```json
{json.dumps(data, indent=2)}
```

---

*Generated: {datetime.now().isoformat()}*
"""
    
    return report


def main():
    output_dir = Path("/home/claude/benchmark_output")
    output_dir.mkdir(exist_ok=True)
    
    print("Generating visualizations...")
    charts = create_visualizations(BENCHMARK_DATA, output_dir)
    print(f"  Created: {', '.join(charts)}")
    
    print("Generating Markdown report...")
    report = generate_markdown_report(BENCHMARK_DATA, charts, output_dir)
    
    report_path = output_dir / "BENCHMARK_REPORT.md"
    report_path.write_text(report)
    print(f"  Created: {report_path}")
    
    # Also save raw JSON
    json_path = output_dir / "benchmark_data.json"
    json_path.write_text(json.dumps(BENCHMARK_DATA, indent=2))
    print(f"  Created: {json_path}")
    
    print(f"\nAll outputs in: {output_dir}")
    return output_dir


if __name__ == "__main__":
    main()
