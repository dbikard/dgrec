# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/API/07_utils.ipynb.

# %% auto 0
__all__ = ['align2mut', 'mut_rix', 'get_mutations', 'get_mutations_noalign', 'mut_to_str', 'str_to_mut', 'genstr_to_seq',
           'reverse_complement', 'get_prot_mut', 'parse_genotypes', 'get_aa_mut_list', 'downsample_fastq_gz',
           'get_basename_without_extension', 'pickle_save', 'pickle_load', 'make_dgr_oligos', 'reverse_comp_geno_list',
           'remove_position', 'remove_position_list']

# %% ../nbs/API/07_utils.ipynb 2
import gzip
import itertools
import os
import csv
from . import pairwise2
from .pairwise2 import format_alignment
from Bio.Align import PairwiseAligner
from Bio.Seq import Seq
from Bio import SeqIO

# %% ../nbs/API/07_utils.ipynb 3
def align2mut(align):
    """Converts a sequence alignment result from Bio.pairwise2.Align.globalms into a list of mutations.
    Positions are those of the alignment."""
    res=[]
    for i in range(align.end):
        if align.seqA[i]!=align.seqB[i]:
            mut=(align.seqA[i],i,align.seqB[i])
            res.append(mut)
    return res

# %% ../nbs/API/07_utils.ipynb 5
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

# %% ../nbs/API/07_utils.ipynb 7
def get_mutations(seqA,seqB, match=2, mismatch=-1, gap_open=-1, gap_extend=-.5):
    """Aligns two sequences and returns a genotype string.
    The string is a comma separated list of mutations.
    """
    align=pairwise2.align.globalms(seqA,seqB, match, mismatch, gap_open, gap_extend, one_alignment_only=True)[0]
    mutations=align2mut(align) 
    mutations=mut_rix(mutations)
    return mutations

# %% ../nbs/API/07_utils.ipynb 9
def get_mutations_noalign(seqA,seqB):
    """Returns a genotype string.
    The string is a comma separated list of mutations.
    """
    assert(len(seqA)==len(seqB))
    mutations=[]
    for i in range(len(seqA)):
        if seqA[i]!=seqB[i]:
            mutations.append((seqA[i],str(i),seqB[i]))
    return mutations

# %% ../nbs/API/07_utils.ipynb 15
def mut_to_str(mutations: list):
    """Converts list of mutations to a comma separated string"""
    mut_str_list=[''.join(map(str,mut)) for mut in mutations]
    mut_str=','.join(mut_str_list)
    return mut_str

# %% ../nbs/API/07_utils.ipynb 17
def str_to_mut(gen: str):
    """Converts genotype string to a list of mutations"""
    
    mutations=[]
    if gen=="":
        return mutations
    else:
        g=gen.split(',')
        for mut in g:
            mut_from=mut[0]
            ix=int(mut[1:-1])
            mut_to=mut[-1]
            mutations.append([mut_from,ix,mut_to])

        return mutations

# %% ../nbs/API/07_utils.ipynb 19
def genstr_to_seq(genstr,refseq):
    j=0
    seq=''
    for mut in str_to_mut(genstr):
        tb, i, qb = mut
        seq+=refseq[j:i]
        if tb=="-":
            seq+=qb
            j=i
        elif qb=="-":
            j=i+1
            pass
        else:
            seq+=qb
            j=i+1

    seq+=refseq[j:]

    return seq

# %% ../nbs/API/07_utils.ipynb 23
def reverse_complement(dna):
    dna=dna.upper()
    # Dictionary to hold the complement of each base
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C','-': '-','N': 'N'}
    
    # Reverse the DNA string
    reversed_dna = dna[::-1]
    
    # Get the complement for each base in the reversed string
    reverse_complement_dna = ''.join(complement[base] for base in reversed_dna)
    
    return reverse_complement_dna



# %% ../nbs/API/07_utils.ipynb 24
def get_prot_mut(genstr,refseq,frame=0,ori=1):
    mut_seq=genstr_to_seq(genstr,refseq)
    if ori==-1:
        refseq=reverse_complement(refseq)
        mut_seq=reverse_complement(mut_seq)

    cut_mut=((len(mut_seq)-frame)%3)
    if cut_mut:
        mut_seq_inframe=mut_seq[frame:-cut_mut]
    else:
        mut_seq_inframe=mut_seq[frame:]

    cut_ref=((len(refseq)-frame)%3)
    if cut_ref:
        refseq_inframe=refseq[frame:-cut_ref]
    else:
        refseq_inframe=refseq[frame:]

    mut_prot=Seq(mut_seq_inframe).translate()
    ref_prot=Seq(refseq_inframe).translate()
    L=min(len(mut_prot),len(ref_prot))
    mut_prot=mut_prot[:L]
    ref_prot=ref_prot[:L]
    return mut_to_str(get_mutations_noalign(ref_prot,mut_prot))


# %% ../nbs/API/07_utils.ipynb 28
def parse_genotypes(genotypes_file):
    gen_list=[]
    with open(genotypes_file,"r") as handle: 
        reader = csv.reader(handle, delimiter='\t')
        for row in reader:
            gen_list.append((row[0],int(row[1])))
    return gen_list

# %% ../nbs/API/07_utils.ipynb 31
def get_aa_mut_list(gen_list,refseq, frame=0, ori=1):
    amino_mut_dic={}
    for gen, n in gen_list:
        if "-" not in gen: #excludes insertion or deletions as they will lead to frameshifts
            if "N" not in gen:  #exclue Ns
                mut=get_prot_mut(gen, refseq, frame=frame, ori=ori)
                if mut in amino_mut_dic:
                    amino_mut_dic[mut]+=n
                else:
                    amino_mut_dic[mut]=n
    aa_mut_list=list(amino_mut_dic.items())
    aa_mut_list=sorted(aa_mut_list,key=lambda x: x[1],reverse=True)
    return aa_mut_list


# %% ../nbs/API/07_utils.ipynb 33
def downsample_fastq_gz(input_file, output_file, num_reads=10000):
    """Downsamples a compressed FASTQ file to the specified number of reads.

    Args:
        input_file (str): Path to the input FASTQ.gz file.
        output_file (str): Path to the output FASTQ.gz file.
        num_reads (int, optional): Number of reads to keep. Defaults to 10000.
    """

    with gzip.open(input_file, 'rb') as infile, gzip.open(output_file, 'wb') as outfile:
        lines = itertools.islice(infile, num_reads * 4)  # Read 4 lines (1 read) at a time
        for line in lines:
            outfile.write(line)

# %% ../nbs/API/07_utils.ipynb 35
def get_basename_without_extension(file_path):
    """
    Extracts the basename of a file without the extension.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The basename of the file without the extension.
    """

    basename = os.path.basename(file_path)
    if '.' in basename:
        # Split at the last dot to remove the extension
        return basename.rsplit('.', 1)[0]
    else:
        # No extension, return the whole filename
        return basename

# %% ../nbs/API/07_utils.ipynb 39
def pickle_save(data_in,file_name_out):
    pickle_out = open(file_name_out,"wb")
    pickle.dump(data_in, pickle_out)
    pickle_out.close()
    


# %% ../nbs/API/07_utils.ipynb 40
def pickle_load(file_name_in):
    pickle_in = open(file_name_in,"rb")
    data_out = pickle.load(pickle_in)
    return data_out

# %% ../nbs/API/07_utils.ipynb 41
def make_dgr_oligos(target:str #TR DNA
                    ,split_number:int #Number of desired splits
                    ):
    "Split the TR target into the input number and then generates the oligos to order"
    bad_overhangs=['AATT', 'ATAT', 'TATA', 'TTAA', 'ACGT', 'CATG', 'CTAG', 'GATC', 'GTAC', 'TCGA', 'TGCA', 'CCGG', 'CGCG', 'GCGC', 'GGCC']
    target=target.upper()
    split=len(target)//split_number
    overhang_list=[]
    split_k_list=[]
    forward_list=[]
    reverse_list=[]
    full_list=[]


    
    for k in range(1,split_number):
        split_k=k*split
        overhang = target[split_k-2:split_k+2]
        
        while overhang in bad_overhangs+['ATAA','TCAG']:
            if split_k%2 == 0:
                split_k += 1
                print('+1')
            elif split_k%2 == 1:
                split_k += -1
                print('-1')
            overhang = target[split_k-2:split_k+2]
        overhang_list.append(overhang)
        split_k_list.append(split_k)

    forward_list.append('ATAA'+target[:split_k_list[0]-2])
    reverse_list.append(reverse_complement(target[:split_k_list[0]+2]))

    for j in range (len(split_k_list)-1):
        forward_list.append(target[split_k_list[j]-2:split_k_list[j+1]-2])
        reverse_list.append(reverse_complement(target[split_k_list[j]+2:split_k_list[j+1]+2]))


    forward_list.append(target[split_k_list[-1]-2:])
    reverse_list.append('CAGA'+reverse_complement(target[split_k_list[-1]+2:]))

    for i in range(split_number):
        full_list.append(forward_list[i])
        full_list.append(reverse_list[i])
            
    return(full_list)

# %% ../nbs/API/07_utils.ipynb 43
def reverse_comp_geno_list(geno_list:list # List of genotypes
                           ,ref_seq:str #string of the template sequence
                           ):
    l=len(ref_seq)
    gene_rev_dic={}
    for geno in geno_list:
        if geno[0]!='':
            mut_list=geno[0].split(',')
            umi_count=geno[1]
            rev_mut_list=[]
            for mut in mut_list:
                old_base=mut[0]
                new_base=mut[-1]
                position=int(mut[1:-1])
                rev_mut=reverse_complement(old_base)+str(l-position-1)+reverse_complement(new_base)
                rev_mut_list.append((rev_mut))
            revgen=','.join(rev_mut_list[::-1])
            if revgen in gene_rev_dic:
                gene_rev_dic[revgen]+=umi_count
            else:
                gene_rev_dic[revgen]=umi_count

        else:
            gene_rev_dic['']=geno[1]

    geno_list_rev = list(gene_rev_dic.items())
    return geno_list_rev


# %% ../nbs/API/07_utils.ipynb 44
def remove_position(geno,pos_list):
    mut_split=geno.split(',')
    new_geno=[]
    for mut in mut_split:
        if int(mut[1:-1]) not in pos_list:
            new_geno.append(mut)
    return ','.join(new_geno)



# %% ../nbs/API/07_utils.ipynb 45
def remove_position_list(geno_list,pos_list):
    new_geno_list=[]
    for k in geno_list:
        geno_k=k[0]
        count_k=k[1]
        # print(geno_k)
        if geno_k!='':
            new_geno_k=remove_position(geno_k,pos_list)
            new_geno_list.append((new_geno_k,count_k))
        else:
            new_geno_k=geno_k
            new_geno_list.append((new_geno_k,count_k))
    return new_geno_list
