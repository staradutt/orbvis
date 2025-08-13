import numpy as np
import math 

from .parser import read_band_energies_and_klist_from_PROCAR, get_tot_index_from_procar,orbvis_orbital_specific_band_data_from_PROCAR
from .utils import angle_between,clean_kpoints,dist_bw_two_kpoints,compute_kpoint_distances
class orbitalbandplot:
    def __init__(path,ispin):
        self.path = path
        self.ispin = ispin
        self.scale = 20
        self.transparency = 70
        self.colmap_id = 0
        self.labels = []
        self.hs_points = []
        self.bs_data = None
        self.kpoints = None
    
    def load_data(self):
        self.bs_data, self.kpoints = read_band_energies_and_klist_from_PROCAR(self.path, self.ispin) 
    def get_high_symmetry_labels(self, input_labels=None):
        if input_labels:
            self.labels = [s.encode('utf-8').decode('unicode_escape') for s in input_labels]
        else:
            self.labels = [f"K{i}" for i in range(len(self.hs_points))]
    def plot(self, projections):
        # Call utility function with all params
        plot_bandstructure_with_projection(self.bs_data, self.kpoints, projections, self.labels, ...)