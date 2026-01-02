# 📄 Publications

Research publications related to the CLARISSA project.

---

## IJACSA 2026

**CLARISSA: A Physics-Centric AI Agent Architecture for Reservoir Simulation**

| Resource | Link |
|----------|------|
| **Abstract** | [Read Abstract](ijacsa-2026/abstract.md) |
| **Paper (PDF)** | [Download PDF](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/raw/main/conference/ijacsa-2026/CLARISSA_Paper_IJACSA.pdf) |
| **Paper (LaTeX)** | [View Source](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/blob/main/conference/ijacsa-2026/CLARISSA_Paper_IJACSA.tex) |

### Figures

| Figure | Description |
|--------|-------------|
| [Figure 1](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/raw/main/conference/ijacsa-2026/figures/CLARISSA_Figure1_Architecture.png) | System Architecture |
| [Figure 2](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/raw/main/conference/ijacsa-2026/figures/CLARISSA_Figure2_NLP_Pipeline.png) | NLP Pipeline |
| [Figure 3](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/raw/main/conference/ijacsa-2026/figures/CLARISSA_Figure3_DataMesh.png) | Data Mesh |
| [Figure 4](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/raw/main/conference/ijacsa-2026/figures/CLARISSA_Figure4_Communication.png) | Communication Flow |

### Supplementary Materials

- [Abstract (CFP submission)](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/raw/main/conference/ijacsa-2026/supplementary/CLARISSA_Abstract_CFP.pdf)
- [Architecture Summary](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/raw/main/conference/ijacsa-2026/supplementary/CLARISSA_Architecture_Summary_Detailed.pdf)

---

## Source Files

All publication source files are in the [`conference/`](https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/tree/main/conference) directory:

```
conference/
├── abstract.md                    # Main abstract
└── ijacsa-2026/
    ├── CLARISSA_Paper_IJACSA.tex  # LaTeX source
    ├── CLARISSA_Paper_IJACSA.pdf  # Compiled PDF
    ├── CLARISSA_Paper_IJACSA.docx # Word version
    ├── figures/                   # Mermaid sources + PNGs
    └── supplementary/             # Additional materials
```

## Contributing to Publications

To update the paper:

1. Edit `conference/ijacsa-2026/CLARISSA_Paper_IJACSA.tex`
2. Regenerate PDF
3. Commit both `.tex` and `.pdf`
4. Update figures in `figures/` if needed
