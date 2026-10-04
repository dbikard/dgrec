"""Analysing DGRec data

Modules:

- `dgrec.pairwise2`: Pairwise sequence alignment using a dynamic programming algorithm."""

__version__ = "0.1.4"

from .example_data import get_example_data_dir
from .genotypes import get_genotypes
from .genotypes_paired import get_genotypes_paired
from .plotting import plot_mutations, plot_mutations_percentage, plot_mutations_percentage_protein
from .predictions import score, score_list, DGR_percentage, DGR_percentage_list, optimize_sequence
from .encoding import encode_tr_list
from . import utils, library_size, analysis

#dgrec.lstm is deliberately not imported here: it needs TensorFlow, which is an optional extra.
