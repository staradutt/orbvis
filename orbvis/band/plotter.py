# orbvis/band/plotter.py

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from distinctipy import get_colors, get_hex

from .parser import (
    read_band_energies_and_klist_from_PROCAR,
    get_tot_index_from_procar,
    orbvis_orbital_specific_band_data_from_PROCAR,
)
from .utils import (
    orbital_labels,
    clean_kpoints,
    compute_kpoint_distances,
)


def orbscatter(**params):
    path = params["PROCAR_PATH"]
    data = params["ORBITAL_INFO"]
    ispin = params["ISPIN"]
    scale = params["SCALE"]
    transparency = params["TRANSPARENCY"]
    title = params["TITLE"]
    ymin = params["YMIN"]
    ymax = params["YMAX"]
    linewidth = params["BS_LINEWIDTH"]
    dpi = int(params["DPI"])
    saveas = params["SAVEAS"]
    color_scheme = params["COLOR_SCHEME"]
    efermi = params.get("EFERMI", None)
    legend_loc = params.get("LEGEND_LOC") or "lower right"
    num_cases = len(data)
    #print(params) to test if default are loading
    # ===== Color handling =====
    if isinstance(color_scheme, list):
        processed_colors = []
        for c in color_scheme:
            if isinstance(c, str) or isinstance(c, int):  # support unquoted hex
                c_str = str(c).strip()
                if not c_str.startswith("#") and len(c_str) in [6, 3]:  # likely a hex without #
                    c_str = f"#{c_str}"
                try:
                    hex_color = mcolors.to_hex(c_str)  # validate and normalize
                    processed_colors.append(hex_color)
                except ValueError:
                    raise ValueError(f"Invalid color in COLOR_SCHEME: {c}")
            else:
                raise ValueError(f"Unsupported color format in COLOR_SCHEME: {c}")
        
        if len(processed_colors) < num_cases:
            print(f"[orbvis] Provided {len(processed_colors)} colors, but {num_cases} are needed. Adding with distinctipy.")
            extra = get_colors(num_cases - len(processed_colors))
            processed_colors.extend([get_hex(c) for c in extra])
        elif len(processed_colors) > num_cases:
            print(f"[orbvis] More colors than needed. Truncating to {num_cases}.")
            processed_colors = processed_colors[:num_cases]
        
        color_scheme = processed_colors
    elif isinstance(color_scheme, str):
        try:
            cmap = cm.get_cmap(color_scheme)
            color_scheme = [mcolors.to_hex(cmap(i / (num_cases - 1))) for i in range(num_cases)]
        except Exception:
            raise ValueError(f"Invalid colormap: {color_scheme}")
    elif isinstance(color_scheme, int):
        if color_scheme == 0:
            color_scheme = [get_hex(c) for c in get_colors(num_cases)]
        elif color_scheme == 1:
            color_scheme = [get_hex(c) for c in get_colors(num_cases, pastel_factor=0.7)]
        else:
            raise ValueError("COLOR_SCHEME int value must be 0 (normal) or 1 (pastel).")
    else:
        raise ValueError("Invalid COLOR_SCHEME format.")

    # ===== Data Loading =====
    bs, kl = read_band_energies_and_klist_from_PROCAR(path, ispin)
    tot_ind = get_tot_index_from_procar(path)
    kl_new, hs = clean_kpoints(kl)

    print("The following high symmetry points were found:\n")
    for i in hs:
        print(kl[i][1:4])
    unicode_help = r"""
    Enter the high-symmetry point labels separated by spaces (e.g., \u0393 X M \u0393)
    These will be stored as raw Unicode strings (not decoded here). Common codes:
    - \u0393 → Γ Gamma
    - \u0394 → Δ Delta
    - \u03a3 → Σ Sigma
    - \u039B → Λ Lambda
    You can also combine like: \u039B1 → Λ1

    Press Enter without typing anything to use default labels: K0, K1, K2, ...
    Or type '0' to quit — default labels will still be used.
    """

    print(unicode_help)

    # Prompt for labels
    label_input = input(f"Enter {len(hs)} high-symmetry labels (or press Enter for K0, K1...): ").strip()
    if label_input == "" or label_input == "0":
        labels = [f"K{i}" for i in range(len(hs))]
    else:
        labels = [s.encode('utf-8').decode('unicode_escape') for s in label_input.split()]
        if len(labels) != len(hs):
            raise ValueError(f"You must provide exactly {len(hs)} labels.")

    # Prepare distance mapping
    full_data, reduced_data = compute_kpoint_distances(kl_new, x_scale=3)
    tick_vals = [dict(reduced_data)[i] for i in hs]
    idx_selected = reduced_data[:, 0].astype(int)

    if ispin == 1:
        bs_selected = bs[:, idx_selected]
    elif ispin == 2:
        bs_selected = bs[:, :, idx_selected]
    if efermi is not None:
        bs_selected = bs_selected - efermi
    
    x_arr = reduced_data[:, 1]

    all_procar_data = []
    all_labels = []

    for entry in data:
        atom_list, element_name, orbital_list = entry

        for orb in orbital_list:
            if orb > tot_ind:
                raise ValueError(f"Orbital index {orb} exceeds total index {tot_ind}.")
        if len(orbital_list) > 1 and tot_ind in orbital_list:
            raise ValueError("Don't mix 'tot' orbital with others.")

        label = element_name
        procar_data = np.zeros_like(bs)

        for i, atom in enumerate(atom_list):
            for j, orbital in enumerate(orbital_list):
                procar_data += orbvis_orbital_specific_band_data_from_PROCAR(path, atom, orbital, ispin)
                if i == 0:
                    if j == 0:
                        label += r"$tot$" if orbital == tot_ind else orbital_labels[orbital]
                    else:
                        label += r"$+$" + orbital_labels[orbital]

        all_procar_data.append(procar_data)
        all_labels.append(label)
    
    # ===== Plotting =====
    if ispin == 1:
        fig, ax = plt.subplots(figsize=(params["FIGSIZEX"], params["FIGSIZEY"]), dpi=dpi)
        custom_handles = []
        for band in range(bs_selected.shape[0]):
            ax.plot(x_arr, bs_selected[band], color="black", linewidth=linewidth)

        for i, data in enumerate(all_procar_data):
            data_k = data[:, idx_selected]
            for band in range(bs_selected.shape[0]):
                ax.scatter(
                    x_arr,
                    bs_selected[band],
                    s=scale * data_k[band],
                    alpha=transparency / 100.0,
                    color=color_scheme[i]
                )
            custom_handles.append(Line2D([0], [0], color=color_scheme[i], marker='o', linestyle="", markersize=5, label=all_labels[i]))
        
        ax.legend(handles=custom_handles, loc=legend_loc, framealpha=0.3)
        ax.set_xticks(tick_vals)
        ax.set_xticklabels(labels)
        ax.set_xlim(x_arr.min(), x_arr.max())
        ax.set_ylim(ymin, ymax)
        ax.set_title(title)
        ax.set_xlabel("K-path")
        ylabel = r"Energy (eV)" if efermi is None else r"$E - E_f$ (eV)"
        ax.set_ylabel(ylabel)
        plt.tight_layout()
        if saveas:
            plt.savefig(saveas, dpi=dpi)
            print(f"[orbvis] Saved to {saveas}")
        else:
            plt.show()

    elif ispin == 2:
        fig, axes = plt.subplots(1, 2, figsize=(params["FIGSIZEX"], params["FIGSIZEY"]), dpi=dpi)
        custom_handles = []

        # Up spin (left)
        for band in range(bs_selected[0].shape[0]):
            axes[0].plot(x_arr, bs_selected[0][band], color="black", linewidth=linewidth)

        # Down spin (right)
        for band in range(bs_selected[1].shape[0]):
            axes[1].plot(x_arr, bs_selected[1][band], color="black", linewidth=linewidth)

        for i, data in enumerate(all_procar_data):
            up_data = data[0][:, idx_selected]
            down_data = data[1][:, idx_selected]
            for band in range(bs_selected[0].shape[0]):
                axes[0].scatter(x_arr, bs_selected[0][band], s=scale * up_data[band], alpha=transparency / 100.0, color=color_scheme[i])
            for band in range(bs_selected[1].shape[0]):
                axes[1].scatter(x_arr, bs_selected[1][band], s=scale * down_data[band], alpha=transparency / 100.0, color=color_scheme[i])

            custom_handles.append(Line2D([0], [0], color=color_scheme[i], marker='o', linestyle="", markersize=5, label=all_labels[i]))

        # Add "↑" and "↓" labels below each subplot
        axes[0].text(0.5, -0.15, "↑", transform=axes[0].transAxes, ha='center', va='top', fontsize=14)
        axes[1].text(0.5, -0.15, "↓", transform=axes[1].transAxes, ha='center', va='top', fontsize=14)

        for i, ax in enumerate(axes):
            ax.set_xticks(tick_vals)
            ax.set_xticklabels(labels)
            ax.set_xlim(x_arr.min(), x_arr.max())
            ax.set_ylim(ymin, ymax)
            ax.set_xlabel("K-path")
            if i == 0:  # Only set y-label for the left (↑) plot
                ylabel = r"Energy (eV)" if efermi is None else r"$E - E_f$ (eV)"
                ax.set_ylabel(ylabel)

        fig.suptitle(title)
        fig.legend(handles=custom_handles, loc=legend_loc, framealpha=0.3)
        plt.tight_layout()
        if saveas:
            plt.savefig(saveas, dpi=dpi)
            print(f"[orbvis] Saved to {saveas}")
        else:
            plt.show()
