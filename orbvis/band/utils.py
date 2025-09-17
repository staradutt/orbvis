# MIT License
# Copyright (c) 2025 Taradutt Pattnaik
# See LICENSE file for full license information.
"""
OrbVis

Orbital-projected band structure plotting for VASP PROCAR data.

File name:orbvis/band/utils.py

Author: Taradutt Pattnaik
Created: 2025-06-11
"""
import numpy as np
import math

orbital_labels = {0:  r"$s$",1:  r"$p_y$",2:  r"$p_z$",3:  r"$p_x$",4:  r"$d_{xy}$",5:  r"$d_{yz}$",6:  r"$d_{z^2}$",
7:  r"$d_{xz}$",8:  r"$d_{x^2 - y^2}$",9:  r"$f_{y(3x^2 - y^2)}$",10: r"$f_{xyz}$",11: r"$f_{yz^2}$",12: r"$f_{z^3}$",
13: r"$f_{xz^2}$",14: r"$f_{z(x^2 - y^2)}$",15: r"$f_{x(x^2 - 3y^2)}$"}
base_colors = [["r","g","b","orange","yellow","lightblue"],
            ["#8ecae6","#219ebc","#023047","#ffb703","#fb8500"],
            ["#264653","#2a9d8f","#e9c46a","#f4a261","#e76f51"],
            ["#ff595e","#ffca3a","#8ac926","#1982c4","#6a4c93"],
            ["#2b2d42","#8d99ae","#edf2f4","#ef233c","#d90429"],
            ["#0b3954","#087e8b","#bfd7ea","#ff5a5f","#c81d25"],
            ["#220901","#621708","#941b0c","#bc3908","#f6aa1c"],
            ["#355070","#6d597a","#b56576","#e56b6f","#eaac8b"],
            ["#003049","#d62828","#f77f00","#fcbf49","#eae2b7"],
            ["#eae2b7","#fe7f2d","#fcca46","#a1c181","#619b8a"]]

def angle_between(v1, v2): #code to get angle between two vectors , will be used later in the code
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    cos_theta = np.clip(np.dot(v1, v2) / (norm1 * norm2), -1.0, 1.0)
    return np.degrees(np.arccos(cos_theta))



def clean_kpoints(k_point_array, angle_tolerance_deg=5.0, jump_threshold=0.2, weight_tol=1e-3):
    """
    Cleans a k-point array for band structure by removing weighted points (if needed),
    removing adjacent duplicates, and detecting high-symmetry points via:
      - direction changes
      - large k-point jumps
    
    Parameters:
        k_point_array (np.ndarray): [index, kx, ky, kz, weight]
        angle_tolerance_deg (float): Threshold for direction angle change.
        jump_threshold (float): Threshold for abrupt distance jumps.
        weight_tol (float): Tolerance for weight uniformity check.

    Returns:
        cleaned_kpoints (list of tuples): (index, kx, ky, kz)
        high_sym_indices (list of int): Indices of high-symmetry points in cleaned_kpoints
    """


    # Step 1: Determine whether to trim based on weight uniformity

    weights = k_point_array[:, 4]
    if np.all(np.abs(weights - weights[0]) < weight_tol):
        band_kpoints = k_point_array  # if all weights are equal , use all
    else:
        band_kpoints = k_point_array[np.abs(weights) < weight_tol]  # Keep only ~zero-weight by making a true false mask based on whether weight is less than tol

    # Step 2: Remove adjacent duplicates (within tolerance)
    cleaned_kpoints = []
    prev_k = None
    for row in band_kpoints:
        idx, kx, ky, kz, _ = row
        current_k = np.array([kx, ky, kz])
        if prev_k is None or not np.allclose(prev_k, current_k, atol=1e-8):
            cleaned_kpoints.append((int(idx), kx, ky, kz))
            prev_k = current_k
    cleaned_kpoints = np.array(cleaned_kpoints)

    # Step 3: Detect direction changes and jumps
    high_sym_indices = [int(cleaned_kpoints[0][0])]  # Always include first point



    for i in range(1, len(cleaned_kpoints) - 1):
        k_prev = cleaned_kpoints[i - 1][1:]
        k_curr = cleaned_kpoints[i][1:]
        k_next = cleaned_kpoints[i + 1][1:]

        vec1 = np.array(k_curr) - np.array(k_prev)
        vec2 = np.array(k_next) - np.array(k_curr)

        angle = angle_between(vec1, vec2)
        jump = np.linalg.norm(np.array(k_curr) - np.array(k_prev))

        if angle > angle_tolerance_deg or jump > jump_threshold:
            high_sym_indices.append(int(cleaned_kpoints[i][0]))

    high_sym_indices.append(int(cleaned_kpoints[-1][0]))  # Always include last point  

    # Convert back to numpy array of list of tuples
    cleaned_kpoints = np.array([tuple(row) for row in cleaned_kpoints])

    return cleaned_kpoints, high_sym_indices


def dist_bw_two_kpoints(kpt1, kpt2):
    dist_vector = np.array(kpt1) - np.array(kpt2)
    return math.sqrt(np.dot(dist_vector, dist_vector))


def compute_kpoint_distances(cleaned_kpoints, x_scale, jump_cutoff=0.25):
    """
    Computes distances and scaled positions for cleaned k-points.
    Limits abrupt jumps to a defined cutoff to prevent large segments dominating scale.

    Parameters:
        cleaned_kpoints (list of tuples): (index, kx, ky, kz)
        x_scale (float): Desired total scaled path length.
        jump_cutoff (float): Max allowed segment length before it's clipped.

    Returns:
        full_data (np.ndarray): [index, segment_distance, cumulative_distance, scaled_distance]
        reduced_data (np.ndarray): [index, scaled_distance]
    """
    num_kpts = len(cleaned_kpoints)

    segment_dists = [0.0]
    cumulative_dists = [0.0]
    raw_dists = [0.0]  # for keeping track

    for i in range(1, num_kpts):
        _, kx1, ky1, kz1 = cleaned_kpoints[i - 1]
        _, kx2, ky2, kz2 = cleaned_kpoints[i]
        d_raw = dist_bw_two_kpoints((kx1, ky1, kz1), (kx2, ky2, kz2))
        if d_raw>jump_cutoff:
            d = 0.0
        else:
            d = d_raw
        #d = min(d_raw, jump_cutoff)
        raw_dists.append(d_raw)
        segment_dists.append(d)
        cumulative_dists.append(cumulative_dists[-1] + d)

    total_length = cumulative_dists[-1]

    if total_length == 0:
        scaled_dists = cumulative_dists.copy()
    else:
        scaled_dists = [d * (x_scale / total_length) for d in cumulative_dists]

    indices = [int(row[0]) for row in cleaned_kpoints]
    full_data = np.array(list(zip(indices, segment_dists, cumulative_dists, scaled_dists)))
    reduced_data = np.array(list(zip(indices, scaled_dists)))
    return full_data, reduced_data


def insert_discontinuities(arr, discontinuity_indices):
    """
    Inserts NaN columns into the array at discontinuity positions.

    Parameters:
        arr (np.ndarray): Shape (bands, kpoints) or (2, bands, kpoints) if spin-polarized
        discontinuity_indices (list or np.ndarray): Positions to insert NaNs

    Returns:
        arr_with_nans (np.ndarray): Same shape but with NaNs inserted in kpoint axis
    """
    if arr.ndim == 2:
        parts = np.split(arr, discontinuity_indices, axis=1)
        with_nans = []
        for part in parts:
            with_nans.append(part)
            with_nans.append(np.full((arr.shape[0], 1), np.nan))
        return np.concatenate(with_nans[:-1], axis=1)  # drop last dummy
    elif arr.ndim == 3:
        out = []
        for spin in range(arr.shape[0]):
            parts = np.split(arr[spin], discontinuity_indices, axis=1)
            with_nans = []
            for part in parts:
                with_nans.append(part)
                with_nans.append(np.full((arr.shape[1], 1), np.nan))
            out.append(np.concatenate(with_nans[:-1], axis=1))
        return np.array(out)
    else:
        raise ValueError("Unsupported array shape in insert_discontinuities")

def merge_close_ticks(tick_vals, tick_labels, tol=1e-5):
    """
    Merges nearby tick positions and combines labels with '|'.

    Parameters:
        tick_vals (list of float): Tick positions
        tick_labels (list of str): Corresponding labels
        tol (float): Tolerance for merging

    Returns:
        merged_vals (list of float)
        merged_labels (list of str)
    """
    if not tick_vals or not tick_labels or len(tick_vals) != len(tick_labels):
        raise ValueError("tick_vals and tick_labels must be same-length non-empty lists.")

    merged_vals = []
    merged_labels = []

    current_val = tick_vals[0]
    current_label = tick_labels[0]

    for i in range(1, len(tick_vals)):
        if abs(tick_vals[i] - current_val) <= tol:
            current_label += "|" + tick_labels[i]
        else:
            merged_vals.append(current_val)
            merged_labels.append(current_label)
            current_val = tick_vals[i]
            current_label = tick_labels[i]

    # Append final
    merged_vals.append(current_val)
    merged_labels.append(current_label)

    return merged_vals, merged_labels

def get_valid_xlim(x_arr):
    """
    Safely compute axis limits from x_arr, ignoring NaN or Inf.

    Parameters:
        x_arr (np.ndarray): 1D array of x values (may include NaNs)

    Returns:
        tuple: (xmin, xmax)

    Raises:
        ValueError: If no valid x values are found
    """
    x_clean = x_arr[~np.isnan(x_arr) & ~np.isinf(x_arr)]
    if x_clean.size == 0:
        raise ValueError("No valid x-axis values found (all NaN or Inf).")
    return x_clean.min(), x_clean.max()
