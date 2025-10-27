---
title: "orbvis: A Python CLI for Orbital-Projected Band Structure and DOS in DFT"
tags:
  - Python
  - Materials Science
  - Solid-State physics
  - Band Structure
  - DFT
authors:
  - name: Taradutt Pattnaik
    orcid: 0009-0000-6673-9092
    corresponding: true
    affiliation: 1

  - name: S. Pamir Alpay
    affiliation: "1, 2, 3"
affiliations:
  - index: 1
    name: Department of Materials Science and Engineering, University of Connecticut, Storrs CT 06269 – USA
  - index: 2
    name: Department of Physics, University of Connecticut, Storrs CT 06269 – USA
  - index: 3
    name: Institute of Materials Science, University of Connecticut, Storrs CT 06269 – USA
date: 27 October 2025
bibliography: paper.bib
---

# Summary

Density Functional Theory (DFT) is a widely used computational technique in materials science and condensed matter physics, allowing researchers to study electronic structure of atoms, molecules, and solids. DFT softwares generate large, detailed output files that contain extensive information about the energy levels and properties of electronic states of materials. However, interpreting these data-rich outputs files can be challenging, especially when additional features like orbital projection are enabled.

For example, in the *VASP* [@Kresse1996] software, setting `LORBIT = 11` in the input file (`INCAR`) instructs the program to output the projection of each electronic state onto the atomic orbitals of every atom in the system. While this orbital-resolved information provides  detailed insights into how individual atomic orbitals could be contributing to the electronic structure, it also makes the output files significantly larger and more complex to parse and visualize without specialized tools. 

*orbvis*, short for orbital visualization, is a Python based command-line tool that is designed to streamline this process. It extracts, processes and visualizes orbital projected band structures and projected density of states (pDOS) for individual atoms or groups of atoms, directly from DFT output files. Currently, *orbvis* supports only VASP and operates in two modes

- **band** (requires `PROCAR` and plots orbital-projected band structures)  
- **dos** (requires `DOSCAR` and plots projected density of states)  

Users can run *orbvis* entirely from the terminal without requiring any prior knowledge of python. *orbvis* uses a configuration file inspired by *VASP* input file (`INCAR`) making it intuitive for researchers already familiar with the *VASP* environment. *orbvis* generates high-quality, publication-ready plots with detailed customization options for orbital selection, color schemes, and layout.

# Statement of need

While several tools exist for post-processing DFT output files such as *p4vasp*[@Dubey2025], *sumo*[@MGanose2018], *pyprocar*[@Herath2020], orbital-projected band structure and projected density of states (pDOS) visualization are often features among many. Each tool offers valuable features but often involves trade-offs in terms of flexibility, ease of use, or the clarity of the visualizations produced.

For example, *p4vasp* provides a graphical interface suitable for interactive plotting but lacks support for scripting or command-line workflows. *Sumo*, on the other hand, is a command-line tool that integrates tightly with the *pymatgen*[@Ong2013] and *seekpath*[@Hinuma2017] ecosystems. However, its reliance on internally generated k-point paths makes it less adaptable to externally generated paths such as those from *VASPKIT*[@Wang2021] or other k-path generators. In certain cases, like hybrid functional (HSE[@Heyd2003]) calculations where the band structure and self-consistent field (SCF) k-points may be mixed in the same file, only the zero-weighted k-points are relevant for the band path. Tools that assume uniform formatting may fail or require manual intervention. Additionally, when band paths contain discontinuities, correct trimming and merging is needed to avoid artificial jumps, something many tools do not handle automatically.

*orbvis* is designed specifically to address these pain points. It is a lightweight, memory-efficient, and scriptable command-line tool focused solely on orbital-projected band structure and pDOS visualization from *VASP* output files. Unlike other tools, *orbvis* performs a series of automated preprocessing steps to ensure clean band structure visualization. It collects the k-point path, removes duplicates, filters out irrelevant points (e.g., weighted k-points in hybrid functional (HSE) calculations where band structure and SCF k-points can be mixed), and automatically detects and labels high symmetry points. Discontinuities along the k-path are identified and trimmed. The orbital-projected band data is then cut at these points and merged in an elegant way to produce a neat band structure plot.

*orbvis* improves the clarity of orbital-projection plots through a **scatter-based visualization** approach:

- The size of each scatter point is scaled according to the orbital contribution values from the `PROCAR` file.
- Adjustable transparency ensures that smaller contributions remain visible, even when overlaid by dominant orbitals.

This strategy enables simultaneous, uncluttered visualization of multiple orbitals and atoms a scenario where color interpolation schemes used by other tools often fall short.

Key Features of `orbvis`:

- **Command-line driven**: Designed for scripting, automation, and easy integration into computational workflows.
- **VASP-style configuration file**: A familiar `KEY = VALUE` format (modeled after *VASP* `INCAR`) allows users to set up complex projection and plotting tasks without any Python knowledge.
- **Robust k-point handling**: 
  - Filters only those k-points that are required for band structure 
  - Automatically detects and merges discontinuous segments in complex k-paths to eliminate visual jumps.
- **Spin support**: Handles spin-polarized and spin–orbit-coupling (SOC) enabled calculations via the `ISPIN` and `SOC` tags.
- **Memory-efficient implementation**: Uses *NumPy* [@Harris2020] vectorization and optimized parsing to process large files with minimal memory usage.
- **Dot-based orbital projection plots**: Provides clear, uncluttered visualization of orbital contributions across atoms and orbitals.
- **Flexible color customization**: 
  -  Auto-generates color schemes using *Distinctipy* [@Roberts2024] and *NumPy* palettes such as `tab10`, `tab20`, `set10`, and `plasma`. 
  -  Accepts user-defined color lists via hex codes or color names.
- **High-symmetry point labeling**: Supports Unicode high-symmetry point labels (e.g., Γ, Λ, Σ) directly from terminal input, with automatic fallback to labels like K0, K1, etc., if none are specified.
- **Visualization of DOS**: Offers similarly configurable and high-quality DOS visualizations.

![Plots generated with *orbvis*. **Left:** Band structure of monolayer MoS~2~ showing contributions from Mo *d* orbitals, calculated with the HSE hybrid functional in *VASP*, reproducing results similar to [@Chang2013]. **Right:** Projected density of states (pDOS).](bandos.png)

Rather than being a general-purpose toolkit, *orbvis* is designed to do one thing well: generate clean, interpretable, and customizable orbital-resolved band structure and DOS plots from raw DFT outputs. It is especially useful for systems where orbital characters reveal key electronic insights, such as 2D materials including transition metal dichalcogenides and their van der Waals heterostructures[@Sun2017], spin–orbit coupling materials like topological insulators[@M2022;@Reid2020;@Acosta2018], magnetic systems[@Jiang2018;@Devaraj2024], and unconventional superconductors[@Liu2018]. By combining clarity, automation, and scripting compatibility, *orbvis* fills a niche in the DFT post-processing ecosystem, ideal for both exploratory studies and high-throughput workflows.
  
# Acknowledgements

The authors acknowledge support from the high-performance computing center at the University of Connecticut for providing the computational resources.