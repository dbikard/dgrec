"""Analysing DGRec data

Modules:

- `dgrec.pairwise2`: Pairwise sequence alignment using a dynamic programming algorithm."""

__version__ = "0.2.0"

from .example_data import get_example_data_dir
from .genotypes import get_genotypes
from .genotypes_paired import get_genotypes_paired
from .plotting import plot_mutations, plot_mutations_percentage, plot_mutations_percentage_protein
from .predictions import (tr_score, tr_score_list, tr_mutagenesis_percentage,
                          tr_mutagenesis_percentage_list, optimize_sequence,
                          score, score_list, DGR_percentage, DGR_percentage_list)  #the last four are deprecated aliases
from .encoding import encode_tr_list
from . import utils, library_size, analysis

#dgrec.lstm is deliberately not imported here: it needs TensorFlow, which is an optional extra.
