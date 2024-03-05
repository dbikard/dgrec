# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/API/00_genotypes.ipynb.

# %% auto 0
__all__ = ['get_UMI_genotype', 'correct_UMI_genotypes', 'genotype_UMI_counter', 'get_genotypes']

# %% ../nbs/API/00_genotypes.ipynb 4
from fastcore.basics import *
from Bio import SeqIO
import gzip as gz
import os
from collections import defaultdict, Counter
import numpy as np
import itertools
import click
import csv
from .utils import get_mutations, mut_to_str

# %% ../nbs/API/00_genotypes.ipynb 7
def get_UMI_genotype(fastq_path: str, #path to the input fastq file
                     ref_seq: str, #sequence of the reference amplicon
                     umi_size: int = 10, #number of nucleotides at the begining of the read that will be used as the UMI
                     quality_threshold: int = 30, #threshold value used to filter out reads of poor average quality
                     ignore_pos: list = [], #list of positions that are ignored in the genotype
                     ) -> dict:
    
    """Takes as input a fastq_file of single read amplicon sequencing, and a reference amplicon sequence.
       Returns a dictionnary containing as keys UMIs and as values a Counter of all genotype strings read for that UMI.
    """
    with gz.open(fastq_path,'rt') as handle:
        reads=SeqIO.parse(handle,"fastq")
        n_reads=0
        n_reads_pass_Qfilter=0
        n_reads_aligned=0
        UMI_dict=defaultdict(list,{})
        for r in reads:
            n_reads+=1
            meanScore=np.mean(r.letter_annotations['phred_quality'])

            if meanScore>quality_threshold:
                n_reads_pass_Qfilter+=1
                umi=str(r.seq[:umi_size])
                mutations=get_mutations(ref_seq,r.seq[umi_size:])
                if ignore_pos:
                    mutations = [m for m in mutations if m[1] not in ignore_pos]
                n_mut=len(mutations)
                if n_mut<15: #more than 10 mutation is almost certainly crap
                    n_reads_aligned+=1
                    UMI_dict[umi].append(mut_to_str(mutations))
    
    log='n reads:\t{}\nn_reads pass filter:\t{}\nn_reads aligned:\t{}\n'.format(n_reads,n_reads_pass_Qfilter,n_reads_aligned)
    log+=f"Number of UMIs: {len(UMI_dict)}\n"
    
    UMI_gencounter={}
    umi_readcounts=[]
    for umi in UMI_dict:
        umi_readcounts.append(len(UMI_dict[umi]))
        UMI_gencounter[umi]=Counter(UMI_dict[umi])

    log+=f"Median number of reads per UMI: {np.median(umi_readcounts)}"
    print(log)
    return UMI_gencounter

# %% ../nbs/API/00_genotypes.ipynb 9
def correct_UMI_genotypes(UMI_gencounter: dict, #the output of the get_UMI_genotype function
                          reads_per_umi_thr=2 #only assign a genotype to a UMI if we have reads_per_umi_thr reads for that genotype or more
                          ) -> dict:
    """Keeps only the genotype with the most reads for each UMI.
    Returns a dictionary with UMIs as keys and a tuple as value: (genotype string, number of reads)
    """
    UMI_gen_dict={}
    for umi in UMI_gencounter:
        gen, n =UMI_gencounter[umi].most_common(1)[0]
        if n>=reads_per_umi_thr: #only assign a genotype to a UMI if we have reads_per_umi_thr reads for that genotype or more
            UMI_gen_dict[umi]=gen

    return UMI_gen_dict

# %% ../nbs/API/00_genotypes.ipynb 11
def genotype_UMI_counter(UMI_gen_dict):
    """Takes as input the output of correct_UMI_genotypes() and 
    returns a list of genotypes sorted by the number of UMIs detected corresponding that each genotype."""
    umi_counter=Counter(UMI_gen_dict.values())
    gen_sorted_list=sorted(list(umi_counter.items()),key=lambda x: x[1], reverse=True)
    return gen_sorted_list


# %% ../nbs/API/00_genotypes.ipynb 13
def get_genotypes(fastq_path: str, #path to the input fastq file
                    ref_seq: str, #sequence of the reference amplicon
                    umi_size: int = 10, #number of nucleotides at the begining of the read that will be used as the UMI
                    quality_threshold: int = 30, #threshold value used to filter out reads of poor average quality
                    ignore_pos: list = [], #list of positions that are ignored in the genotype
                    reads_per_umi_thr: int = 0, #minimum number of reads required to take a UMI into account. Using a number >2 enables to perform error correction for UMIs with multiple reads.
                    save_umi_data: str = None, #path to the csv file where to save the details of the genotypes reads for each UMI. If None the data isn't saved.
                    ):
    """Putting things together in a single wrapper function that takes the fastq as input and returns the list of genotypes."""
    UMI_dict = get_UMI_genotype(fastq_path, ref_seq, umi_size, quality_threshold, ignore_pos)
    if save_umi_data:
        with open(save_umi_data,"w", newline='') as handle: 
            csv_writer = csv.writer(handle,delimiter="\t",doublequote=False)
            for umi in itertools.islice(UMI_dict,20):
                csv_writer.writerow([umi,list(UMI_dict[umi].items())])

    UMI_gen_dict=correct_UMI_genotypes(UMI_dict, reads_per_umi_thr)
    gen_list = genotype_UMI_counter(UMI_gen_dict)
    print("Number of genotypes:", len(gen_list))
    return gen_list
    