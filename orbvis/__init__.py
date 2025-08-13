# MIT License
# Copyright (c) 2025 Taradutt Pattnaik
# See LICENSE file for full license information.
"""
OrbVis

Orbital-projected band structure plotting for VASP PROCAR data.

Author: Taradutt Pattnaik
Created: 2025-06-11
"""
__version__ = "0.1.0"


# Expose key classes/functions 
from .band import read_band_energies_and_klist_from_PROCAR, get_tot_index_from_procar,orbvis_orbital_specific_band_data_from_PROCAR
#from .dos import DOSPlot
