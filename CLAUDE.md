# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DGRec is a bioinformatics tool for analyzing DGRec (Diversity Generating Retroelement + recombineering) data. DGRec is a novel in vivo hypermutation technique. The DGRec package processes sequencing reads to identify genotypes and includes ML models for predicting mutagenesis outcomes.

Publication: https://www.biorxiv.org/content/10.1101/2025.03.24.644984v1

## DGRec Biology

DGRec combines **DGR** (Diversity Generating Retroelement, from Bordetella phage BPP-1) with **recombineering** (CspRecT + mutL*) to achieve targeted in vivo hypermutation in E. coli.

**Key mechanism**: The DGR reverse transcriptase (bRT) + Avd reverse-transcribe the **Template Repeat (TR)** RNA, making errors predominantly at **adenine positions** (~30% error rate at A, <2% at other bases). CspRecT integrates the mutagenic cDNA into the **Variable Repeat (VR)** in the target gene. mutL* prevents mismatch repair from correcting mutations.

**Why adenine bias matters for the code**:
- `is_dgrec()` validates the adenine bias signature (≥70% A mutations)
- `optimize_sequence()` chooses codons to control which positions have adenines (and thus get diversified)
- `codons_reaching_stop` lists codons where A-mutagenesis can produce stop codons

**Sequence context effects**: The +1 base affects mutation rate (G decreases, C increases) and substitution bias. This creates position-dependent, context-dependent error patterns — explaining why the LSTM model captures sequential dependencies (the "snowball effect": a prior mutation at +1 increases error rate at the current position).

**TR quality depends on RNA folding**: The key predictive feature is **ΔE = E(TR+Spacer) - E(TR)** — the energy difference captures whether the spacer interaction disrupts the TR fold, affecting bRT accessibility. This is what the encoding module computes.

**TR design constraints**:
- TR length: 50-200 bp, with mutations predominantly in the middle (recombineering needs homology arms on both sides)
- TR self-mutagenesis: progressive adenine loss over time as A→non-A mutations accumulate
- Only ~9% of random TRs show >10% mutagenesis — hence the prediction models

## Development Framework

This project uses **nbdev3** - all Python source code is auto-generated from Jupyter notebooks. **Never edit `.py` files directly** - edit the corresponding notebooks in `nbs/API/` instead.

## Common Commands

```bash
# Install dependencies (ViennaRNA required for predictions)
conda install -c conda-forge -c bioconda viennarna
pip install -e .

# Export notebooks to Python modules (after editing notebooks)
nbdev-export

# Run tests
nbdev-test

# Build documentation locally
nbdev-docs

# Preview documentation
nbdev-preview

# Clean notebook metadata
nbdev-clean

# Prepare for commit (clean + export + test)
# This runs nbdev-clean, nbdev-export, and nbdev-test — no need to run them separately
nbdev-prepare
```

## CLI Usage

```bash
# Single-end reads
dgrec genotypes fastq_path reference_path -o output.csv

# Paired-end reads
dgrec genotypes_paired fwd.fastq rev.fastq ref.fasta --fwd_span 0 150 --rev_span 30 150 -o output.csv
```

## Architecture

### Notebook-to-Module Mapping

| Notebook | Module | Purpose |
|----------|--------|---------|
| `nbs/API/00_genotypes.ipynb` | `dgrec/genotypes.py` | Single-end genotype calling with UMI dedup to correct PCR/sequencing errors |
| `nbs/API/01_genotypes_paired.ipynb` | `dgrec/genotypes_paired.py` | Paired-end genotype calling |
| `nbs/API/02_plotting.ipynb` | `dgrec/plotting.py` | Visualization of mutation profiles and amino acid diversity |
| `nbs/API/03_analysis.ipynb` | `dgrec/analysis.py` | Mutation rate analysis (A-specific elevated rates in VR are the hallmark DGRec signature) |
| `nbs/API/04_encoding.ipynb` | `dgrec/encoding.py` | Sequence encoding — computes ΔE feature that predicts whether TR RNA is accessible for bRT binding |
| `nbs/API/05_predictions.ipynb` | `dgrec/predictions.py` | ML predictions of TR activity (only ~9% of random TRs produce >10% mutagenesis) |
| `nbs/API/07_utils.ipynb` | `dgrec/utils.py` | Core utilities: alignment, genotype validation, codon tables, DGRec signature testing |
| `nbs/API/08_cli.ipynb` | `dgrec/cli.py` | Click-based CLI |
| `nbs/API/09_lstm.ipynb` | `dgrec/lstm.py` | LSTM model that captures bRT's position-dependent, context-dependent error patterns including the snowball effect |
| `nbs/API/10_library_size.ipynb` | `dgrec/library_size.py` | Library size estimation — extrapolates from sampled genotypes using power-law model |

### Biological Workflow

```
TR Design Phase:           05_predictions (score TRs) → 09_lstm (simulate diversity)
Experiment:                [wet lab — not in code]
Data Analysis Phase:       00/01_genotypes (call variants) → 02_plotting + 03_analysis (visualize & quantify)
Library Characterization:  10_library_size (estimate total diversity)
Shared:                    04_encoding (ML features), 07_utils (core utilities), 08_cli (command line)
```

### Data Processing Pipeline

```
FASTQ input → Alignment → UMI Grouping → Genotype Calling → Filtering → CSV output
```

### Key Functions

- `get_genotypes()` - Main single-end genotype calling
- `get_genotypes_paired()` - Paired-end genotype calling
- `score()` / `score_list()` - Predicts TR quality based on RNA folding energy (ΔE feature)
- `DGR_percentage()` - Predicts % of molecules that will be mutagenized
- `optimize_sequence()` - Finds synonymous codon substitutions that improve TR folding while preserving protein and controlling which amino acids can be reached by mutagenesis
- `plot_mutations()` - Visualization of per-position mutation profiles
- `is_dgrec()` - Validates the adenine bias signature (≥70% A mutations, ≥2 mutations)
- `generate_sequences_oneTR()` - Simulates VR diversity from a TR design using trained LSTM

### Genotype Format

Mutations are comma-separated: `A50T,G75C,T150A` where format is `[RefBase][Position][AltBase]`

## Dependencies

- **scikit-learn==1.7.1** and **tensorflow[and-cuda]==2.17** are pinned for model compatibility
- **ViennaRNA** is required for the encoding module (RNA secondary structure)
- Pre-trained models are bundled in `dgrec/example_data/`

## Testing in nbdev

In nbdev, tests are regular notebook cells containing `assert` statements placed after the function they test.

### Test cell pattern

Each exported function should follow this pattern in the notebook:

```
[#| export cell with function definition]
[visible demo cell showing usage]          ← IMMEDIATELY after, shown in docs
[#| hide cell with assert-based tests]     ← hidden from docs, run by nbdev-test
```

**IMPORTANT: Demo cell placement**
- The visible demo cell MUST be the cell immediately following the function definition
- Do NOT place another `#| export` cell between a function and its demo
- If a function needs setup (e.g., loading data), the setup should come BEFORE the function definition, not between the definition and demo
- Every exported function must have at least one visible demo cell for the auto-generated documentation

- Test cells use `#| hide` so they run during `nbdev-test` but don't appear in docs.
- Keep tests fast: use minimal inputs (1-2 sequences, small n values) for ML model tests.

### Import rules

nbdev requires imports to be in their own dedicated cells - **never mix `import` statements with other code**. This applies to ALL cells (visible, hidden, and export).

**Where to put imports:**
- **Module imports** (`numpy`, `os`, etc.): Add to the `#| export` imports cell at the top
- **Test-only imports** (`tempfile`, `Counter`): Check if already imported in the export cell. If not, create a dedicated `#| hide` cell containing just the import before the test cells that need it
- **Example data imports** (`from dgrec.example_data import ...`): Use the existing `#| hide` import cell near the top

**Common pattern for test dependencies:**
```python
#| hide
import tempfile
```
```python
#| hide
# Test using tempfile
with tempfile.TemporaryDirectory() as tmpdir:
    ...
```

### Cell ordering matters

Notebook cells execute top-to-bottom. A test cell can only reference functions and variables defined in **earlier** cells. If a function depends on another function defined later in the notebook, the test must be placed after both definitions.

### Editing .ipynb files

The `Edit` tool does not work on `.ipynb` files. Use one of:
- `NotebookEdit` tool for single-cell replacements or insertions
- Python scripts via `Bash` that manipulate the raw JSON for bulk changes

### Shared code belongs in utils

If the same constants or functions appear in multiple notebooks, consolidate them into `07_utils.ipynb` and import from `dgrec.utils` in other notebooks. This avoids drift between duplicate definitions.

## CI/CD

- Tests run via `fastai/workflows/nbdev3-ci@master` on push/PR
- Documentation auto-deploys to GitHub Pages via Quarto