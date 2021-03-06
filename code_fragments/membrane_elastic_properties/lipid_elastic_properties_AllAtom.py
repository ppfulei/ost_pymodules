"""
Example written by Niklaus Johner (niklaus.johner@a3.epfl.ch)

This example represents a typical script used to calculate the membrane elastic properties from a simulation.
As input you need an aligned trajectory (see the align_trajectory_AllAtom.py for an example of how to align a trajectory).

"""
from ost import *
import os,sys
import numpy as npy
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
sys.path.append("../") #Set path to the python modules
import lipid_analysis,trajectory_utilities


indir="path/to/input directory"
outdir="path/to/output directory"
pdbname="pdbname"
trajname="trajname"
filename_basis='tilt&splay_'

#We have to define several parameters:
# 1. The list containing the residue names of the different lipids in the system.
#    For example if the system contains DOPC and DPPC.
lipid_names=['DOPC','DPPC']

# 2. Define the residue name of the water molecules.
#    This is used together with the lipid names to calculate the density maps
#    of water and lipids used to extract the membrane interface and orient the normals on the interface.
water_name='TIP3'

# 3. For each lipid type, we define the selection for headgroups and tails which
#    which are used to determine the director vectors.
#    We also need a selection that will be used to calculate distances between lipids. 
#    This should be atoms lying at the neutral plane.
head_group_dict={'DOPC':'aname=P,C2','DPPC':'aname=P,C2'}
tail_dict={'DOPC':'aname=C316,C317,C318,C216,C217,C218','DPPC':'aname=C214,C215,C216,C314,C315,C316'}
distance_sele_dict={'DOPC':'aname=C22,C21,C23,C31,C32,C33','DPPC':'aname=C22,C21,C23,C31,C32,C33'}

# 4. We define the different cutoffs used by the algorithms. 
#    We give here good default values, but more information can be found
#    in the documentation
#max distance between two lipids to be considered in the splay calculation
distance_cutoff=10.0 
#max tilt angle with respect to normal for splay calculations
angle_cutoff=0.175 
# radius of area used to calculate the normals to the membrane interface. If too small, normals will be noisy.
within_size_normals=10.0
#Density cutoff used when calculating the interface.
#This can be set to 0, but calculations will be slower.
density_cutoff=0.3
#Stride used when calculating the water and lipid densities.
#When set to 1, all frames are considered, which can be slow.
density_stride=1

#5. We have to define for which lipids we want to make the analysis.
#   Typically the trajectory being analysed comprises several replicates
#   of the simulation system, which is used to treat periodic boundary conditions properly.
#   But we typically only want to analyse one of the replicas. In this example it has chain name A.
to_analyze="cname=A and rname=DOPC,DPPC"
to_ignore="cname!=A and rname=DOPC,DPPC"

#6.  We need to define the area per lipid (at the neutral plane). This is used in the
#    Calculation of the lipid splay constants.
#    In this example it is set to 60 A^2. For a lipid bilayer the area can be obtained
#    Using the lipid_analysis.AnalyzeAreaPerLipid function.
lipid_area=60.0

#7. Other parameters
prot_sele=None
sele_dict={}


###########################################
#Now starts the analysis
#Typically the rest of the script does not have to be modified
###########################################

#First we load the structure and trajectory
p=io.IOProfile(processor=conop.HeuristicProcessor(),dialect='CHARMM',fault_tolerant=True)
eh=io.LoadPDB(os.path.join(indir,pdbname+".pdb"),profile=p)
t=io.LoadCHARMMTraj(eh,os.path.join(indir,trajname+'.dcd'),stride=1)


#   Periodic boundaries are best treated by replicating the simulation box around
#   the original unit cell and then calculating tilts and splays only for lipids from
#   the original unit cell, but using the surrounding unit cells to find all neighbors 
#   of a lipid for the splay calculation and to avoid boundary effects on the interfaces
#   and hence on the normal vectors used both for the tilt and splay calculations.
#   We therefore need to tell the function which lipids belong to the central unit cell.
#   This is done by setting a bool property for the corresponding residues.

tilt_bool_prop='do_tilt'
splay_bool_prop='do_splay'


v=eh.Select(to_analyze)
for r in v.residues:
  r.SetBoolProp(tilt_bool_prop,True)
  r.SetBoolProp(splay_bool_prop,True)
v=eh.Select(to_ignore)
for r in v.residues:
  r.SetBoolProp(tilt_bool_prop,False)
  r.SetBoolProp(splay_bool_prop,False)


#  We calculate the tilts and splays:
(lipid_tilt_dict,lipid_normal_dict,splay_dict,b_eh)=lipid_analysis.AnalyzeLipidTiltAndSplay(t,
  lipid_names,head_group_dict,tail_dict,distance_cutoff,within_size_normals,distance_sele_dict,water_name,
  outdir,density_cutoff,prot_sele,density_stride,tilt_bool_prop,splay_bool_prop,filename_basis,sele_dict)


########################################################
# Now we analyze the lipid tilts and splays, fitting the corresponding analytical functions
# to extract the elastic constants. See documentation and papers cited therein for more information.
# This can be done with a single function call to ExtractTiltAndSplayModuli.
# The function will make one fit for each lipid type, and then calculate the overall tilt modulus
# By taking a weighted average of the individual contributions.

# The number of bins used when making the histograms for the tilts
nbins=100

#Now we extract the constants
k_dict=lipid_analysis.ExtractTiltAndSplayModuli(lipid_tilt_dict,splay_dict,lipid_area,outdir,nbins)



