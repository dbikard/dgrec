# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/API/03_analysis.ipynb.

# %% auto 0
__all__ = ['bases', 'mut_rate']

# %% ../nbs/API/03_analysis.ipynb 2
from .utils import parse_genotypes, str_to_mut
import os
import numpy as np
from Bio import SeqIO
import matplotlib.pyplot as plt

# %% ../nbs/API/03_analysis.ipynb 4
bases=list("ATGC")
def mut_rate(gen_list:list, #a genotype list with the number of molecules detected
             ran:tuple, #the position range in which to compute the mutation rate. If None the rate is computed for the full sequence.
             ref_seq:str, #reference sequence
             ):
    """Computes the mutation rate per base within the specified range. The rate can be computed for specific bases using the base_restriction argument."""
    mut_pileup=np.zeros(len(ref_seq))
    nTOT = 0
    for g, n in gen_list:
        nTOT += n
        gens = str_to_mut(g)
        for m in gens:
            mut_pileup[m[1]]+=n

    mut_pileup=mut_pileup/nTOT

    mut_n_per_base={}
    for b in bases:
        b_pos= np.where((np.array(list(ref_seq))==b) & 
                (np.arange(len(ref_seq))>ran[0]) & 
                (np.arange(len(ref_seq))<ran[1]))
        mut_n_per_base[b]=mut_pileup[b_pos].mean()

    mut_n_per_base["all"]=mut_pileup[ran[0]:ran[1]].mean()

    return mut_n_per_base
        
