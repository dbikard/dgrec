# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['align2mut', 'mut_rix', 'get_mutations', 'mut_to_str', 'get_UMI_genotype', 'correct_UMI_genotypes',
           'genotype_UMI_counter', 'get_genotypes', 'dgrec_genotypes']

# %% ../nbs/00_core.ipynb 4
from fastcore.basics import *
from Bio import SeqIO
from Bio import pairwise2
import gzip as gz
import os
from collections import defaultdict, Counter
import numpy as np
import itertools
import click

# %% ../nbs/00_core.ipynb 7
def align2mut(align):
    """Converts a sequence alignment result from Bio.pairwise2.Align.globalms into a genotype string.
    Positions are those of the alignment."""
    res=[]
    for i in range(align.end):
        if align.seqA[i]!=align.seqB[i]:
            mut=(align.seqA[i],i,align.seqB[i])
            res.append(mut)
    return res

# %% ../nbs/00_core.ipynb 9
def mut_rix(mutations):
    """Reindexes the positions of the mutations to go from 
    their position in the sequence alignment to their position in the original sequence."""
    ph=0
    res_rix=[]
    for mut in mutations:
        rix=mut[1]+ph
        res_rix.append((mut[0],rix,mut[2]))
        if mut[0]=='-':
            ph-=1
            
    return res_rix

# %% ../nbs/00_core.ipynb 12
def get_mutations(seqA,seqB):
    """Aligns two sequences and returns a genotype string.
    The string is a comma separated list of mutations.
    """
    align=pairwise2.align.globalms(seqA,seqB, 2, -1, -1, -.5, one_alignment_only=True)[0]
    mutations=align2mut(align) 
    mutations=mut_rix(mutations)
    return mutations

# %% ../nbs/00_core.ipynb 14
def mut_to_str(mutations: list):
    """Converts list of mutations to a comma separated string"""
    mut_str_list=[''.join(map(str,mut)) for mut in mutations]
    mut_str=','.join(mut_str_list)
    return mut_str

# %% ../nbs/00_core.ipynb 16
def get_UMI_genotype(fastq_path: str, #path to the input fastq file
                     ref_seq: str, #sequence of the reference amplicon
                     umi_size: int = 10, #number of nucleotides at the begining of the read that will be used as the UMI
                     quality_threshold: int = 30, #threshold value used to filter out reads of poor average quality
                     ignore_pos: list = [], #list of positions that are ignored in the genotype
                     ) -> dict:
    
    """Takes as input a fastq_file of single read amplicon sequencing, and a reference amplicon sequence.
       Returns a dictionnary containing as keys UMIs and as values a list of all genotype strings read for that UMI.
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
    print(log)
    return UMI_dict

# %% ../nbs/00_core.ipynb 18
def correct_UMI_genotypes(UMI_dict: dict, #the output of the get_UMI_genotype function
                          reads_thr=2 #only keep UMIs for which we have more than reads_thr reads
                          ) -> dict:
    """Keeps only the genotype with the most reads for each UMI.
    Returns a dictionary with UMIs as keys and a tuple as value: (genotype string, number of reads)
    """
    UMI_gen_dict={}
    for umi in UMI_dict:
        N=len(UMI_dict[umi])
        if N>=reads_thr: #only consider umis for which we have more than reads_thr reads
            gen_counter=Counter(UMI_dict[umi])
            gen=sorted(list(gen_counter.items()),key=lambda x: x[1], reverse=True)[0] #only keep the genotype with the most reads for this umi
            UMI_gen_dict[umi]=gen

    return UMI_gen_dict

# %% ../nbs/00_core.ipynb 20
def genotype_UMI_counter(UMI_gen_dict):
    """Takes as input the output of correct_UMI_genotypes() and 
    returns a list of genotypes sorted by the number of UMIs detected corresponding that each genotype."""
    umi_counter=Counter([gen for gen,n in UMI_gen_dict.values()])
    gen_sorted_list=sorted(list(umi_counter.items()),key=lambda x: x[1], reverse=True)
    return gen_sorted_list


# %% ../nbs/00_core.ipynb 22
def get_genotypes(fastq_path: str, #path to the input fastq file
                    ref_seq: str, #sequence of the reference amplicon
                    umi_size: int = 10, #number of nucleotides at the begining of the read that will be used as the UMI
                    quality_threshold: int = 30, #threshold value used to filter out reads of poor average quality
                    ignore_pos: list = [], #list of positions that are ignored in the genotype
                    reads_thr: int = 0, #minimum number of reads required to take a UMI into account. Using a number >2 enables to perform error corrects for UMIs with multiple reads.
                    ):
    """Putting things together in a single wrapper function that takes the fastq as input and returns the list of genotypes."""
    UMI_dict = get_UMI_genotype(fastq_path, ref_seq, umi_size, quality_threshold, ignore_pos)
    UMI_gen_dict=correct_UMI_genotypes(UMI_dict, reads_thr)
    gen_list = genotype_UMI_counter(UMI_gen_dict)
    print("Number of genotypes:", len(gen_list))
    return gen_list
    

# %% ../nbs/00_core.ipynb 24
#Commande line interface
@click.command()
@click.argument('fastq', type=click.Path(exists=True))
@click.argument('ref', type=click.Path(exists=True))
@click.option('--umi_size', '-u', default=10, help="Number of nucleotides at the begining of the read that will be used as the UMI")
@click.option('--quality_threshold', '-q', default=10, help="threshold value used to filter out reads of poor average quality")
@click.option('--ignore_pos', '-i', default=[], multiple=True, help="list of positions that are ignored in the genotype, e.g. [0,1,149,150]")
@click.option('--reads_thr', '-r', default=0, help="minimum number of reads required to take a UMI into account. Using a number >2 enables to perform error corrects for UMIs with multiple reads")
@click.option('--output', '-o', default="genotypes.csv", help="output file path")
def dgrec_genotypes(fastq, ref, umi_size, quality_threshold, ignore_pos, reads_thr, output):
    ref=next(SeqIO.parse(ref,"fasta"))
    ref_seq=str(ref.seq)
    gen_list = get_genotypes(fastq, ref_seq, 
                             umi_size=umi_size, 
                             quality_threshold=quality_threshold, 
                             ignore_pos=ignore_pos,
                             reads_thr=reads_thr)
    
    with open(output,"w") as handle:
            for g,n in gen_list:
                handle.write(f"{g}\t{n}\n")
