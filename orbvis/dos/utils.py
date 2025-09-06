# MIT License
# Copyright (c) 2025 Taradutt Pattnaik
# See LICENSE file for full license information.
"""
OrbVis

Orbital-projected band structure plotting for VASP PROCAR data.

File name:orbvis/dos/utils.py

Author: Taradutt Pattnaik
Created: 2025-06-11
"""
import matplotlib.colors as mcolors

def normalize_color(color):
    """
    Normalize hex color (with or without '#') or named color to hex.
    """
    try:
        if isinstance(color, str):
            color = color.strip()
            if not color.startswith("#") and len(color) in [6, 3]:
                color = "#" + color
            return mcolors.to_hex(color)
        else:
            raise ValueError
    except Exception:
        raise ValueError(f"Invalid color format: {color}")
orbital_labels = {
    0:  r"$s$",
    1:  r"$p_y$",
    2:  r"$p_z$",
    3:  r"$p_x$",
    4:  r"$d_{xy}$",
    5:  r"$d_{yz}$",
    6:  r"$d_{z^2}$",
    7:  r"$d_{xz}$",
    8:  r"$d_{x^2 - y^2}$",
    9:  r"$f_{y(3x^2 - y^2)}$",
    10: r"$f_{xyz}$",
    11: r"$f_{yz^2}$",
    12: r"$f_{z^3}$",
    13: r"$f_{xz^2}$",
    14: r"$f_{z(x^2 - y^2)}$",
    15: r"$f_{x(x^2 - 3y^2)}$"
    }