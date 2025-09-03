import numpy as np

from .parser import (
    read_fermi_energy_streamed,
    read_total_dos_streamed,
    read_atom_orbital_dos_streamed,
)

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from .utils import (
    normalize_color,
    orbital_labels,
)
from distinctipy import get_colors, get_hex
import matplotlib.colors as mcolors
import matplotlib.cm as cm

def plot_pdos(**params):
    # ====== Extract parameters =====
    path = params["DOSCAR_PATH"]
    data = params["ORBITAL_INFO"]
    ispin = params["ISPIN"]
    sigma = params.get("SIGMA", 2.0)
    tdos_lw = params.get("TDOS_LINEWIDTH", 1.0)
    pdos_lw = params.get("PDOS_LINEWIDTH", 1.0)
    transparency = params.get("TRANSPARENCY", 90) / 100.0
    title = params.get("TITLE", "Orbital Projected Density of States")
    figsize_x = params.get("FIGSIZEX", 10)
    figsize_y = params.get("FIGSIZEY", 6)
    ymin = params.get("YMIN", -5)
    ymax = params.get("YMAX", 5)
    dpi = params.get("DPI", 300)
    saveas = params.get("SAVEAS", "pdos_output.png")
    efermi = params.get("EFERMI", None)
    color_scheme = params["COLOR_SCHEME"]
    xmin = params.get("XMIN", None)
    xmax = params.get("XMAX", None)
    show_tdos = params.get("SHOW_TDOS", True)
    legend_loc = params.get("LEGEND_LOC") or "best"

    num_cases = len(data)

    # ===== Handle colors =====
    if isinstance(color_scheme, list):
        color_scheme = [normalize_color(c) for c in color_scheme]
        if len(color_scheme) < num_cases:
            print(f"[orbvis] Provided {len(color_scheme)} colors, need {num_cases}. Adding extra colors.")
            extra = get_colors(num_cases - len(color_scheme))
            color_scheme.extend([get_hex(c) for c in extra])
        else:
            color_scheme = color_scheme[:num_cases]
    elif isinstance(color_scheme, str):
        try:
            cmap = cm.get_cmap(color_scheme)
            color_scheme = [mcolors.to_hex(cmap(i / max(1, num_cases - 1))) for i in range(num_cases)]
        except Exception:
            raise ValueError(f"Invalid colormap name: {color_scheme}")
    elif isinstance(color_scheme, int):
        if color_scheme == 0:
            color_scheme = [get_hex(c) for c in get_colors(num_cases)]
        elif color_scheme == 1:
            color_scheme = [get_hex(c) for c in get_colors(num_cases, pastel_factor=0.7)]
        else:
            raise ValueError("COLOR_SCHEME int must be 0 (normal) or 1 (pastel).")
    else:
        raise ValueError("Invalid COLOR_SCHEME format.")

    # ===== Read DOS data =====
    energy_arr, tdos = read_total_dos_streamed(path, ispin)
    if efermi is None:
        efermi = read_fermi_energy_streamed(path)
    energy_arr = energy_arr - efermi

    all_pdos_data = []
    all_labels = []

    for entry in data:
        atom_list, element_name, orbital_list = entry
        label = element_name
        pdos_data = np.zeros_like(tdos)

        for i, atom in enumerate(atom_list):
            for j, orb in enumerate(orbital_list):
                pdos_data += read_atom_orbital_dos_streamed(path, ispin, atom, orb)
                if i == 0:
                    if j == 0:
                        label += orbital_labels[int(orb)]
                    else:
                        label += r"$+$" + orbital_labels[int(orb)]

        all_pdos_data.append(pdos_data)
        all_labels.append(label)

    # ===== Plotting ======
    fig, ax = plt.subplots(figsize=(figsize_x, figsize_y), dpi=dpi)

    if ispin == 1:
        
        if show_tdos:
            tdos_smooth = gaussian_filter1d(tdos, sigma=sigma)
            ax.plot(energy_arr, tdos_smooth, label="TDOS", color="black", linewidth=tdos_lw)


        for i, pdos in enumerate(all_pdos_data):
            pdos_smooth = gaussian_filter1d(pdos, sigma=sigma)
            ax.plot(energy_arr, pdos_smooth, label=all_labels[i],
                    color=color_scheme[i], linewidth=pdos_lw, alpha=transparency)

    elif ispin == 2:
        if show_tdos:
            up_tdos = gaussian_filter1d(tdos[:, 0], sigma=sigma)
            down_tdos = gaussian_filter1d(tdos[:, 1], sigma=sigma)
            ax.plot(energy_arr, up_tdos, label="TDOS ", color="black", linewidth=tdos_lw)
            ax.plot(energy_arr, -down_tdos, color="black", linewidth=tdos_lw)

        for i, pdos in enumerate(all_pdos_data):
            up = gaussian_filter1d(pdos[:, 0], sigma=sigma)
            down = gaussian_filter1d(pdos[:, 1], sigma=sigma)
            ax.plot(energy_arr, up, label=all_labels[i],
                    color=color_scheme[i], linewidth=pdos_lw, alpha=transparency)
            ax.plot(energy_arr, -down, color=color_scheme[i], linewidth=pdos_lw, alpha=transparency)

    # ====== Final tweaks =====
    if xmin is not None or xmax is not None:
        ax.set_xlim(left=xmin, right=xmax)
    else:
        ax.set_xlim(energy_arr.min(), energy_arr.max())
    ax.set_ylim(ymin, ymax)
    ax.axvline(x=0.0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel(r"$E - E_f$ (eV)")
    ax.set_ylabel("DOS (states/eV)")
    ax.set_title(title)
    ax.legend(loc=legend_loc, fontsize="small", ncol=max(1, len(all_labels) // 3))
    plt.tight_layout()
    plt.savefig(saveas)
    plt.close()
    print(f"[orbvis] PDOS plot saved to '{saveas}'")