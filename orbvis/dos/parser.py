import numpy as np
def read_fermi_energy_streamed(path):
    """
    Efficiently read Fermi energy from DOSCAR using line-by-line parsing.

    Returns:
    - E_fermi (float): Fermi energy in eV
    """
    print("Orbvis is reading DOSCAR to extract Fermi energy...")
    with open(path, 'r') as f:
        for _ in range(5):
            next(f)  # skip first 5 lines
        line6 = next(f).split()
        E_fermi = float(line6[3])  # 4th val is fermi energy
        print("Fermi energy is "+ str(E_fermi))
        return E_fermi

def read_total_dos_streamed(path, ispin):
    """
    Efficiently read total DOS using line-by-line parsing.
    
    Returns:
    - E (nedos,): energy array
    - DOS (nedos,) if ispin=1
    - DOS (nedos, 2) if ispin=2 where DOS [:,0] = up, DOS [:,1] = down
    """
    print("Orbvis is reading doscar to extract tdos data...")
    with open(path, 'r') as f:
        for _ in range(5):
            next(f)

        meta = next(f).split()
        nedos = int(meta[2])

        E = []
        DOS = []
        

        if ispin == 1:
            for _ in range(nedos):
                parts = next(f).split()
                E.append(float(parts[0]))
                DOS.append(float(parts[1]))
            return np.array(E), np.array(DOS)

        elif ispin == 2:
            for _ in range(nedos):
                parts = next(f).split()
                E.append(float(parts[0]))
                DOS.append([float(parts[1]), float(parts[2])])  # up, down both are appended side by sidea s one entry
            return np.array(E), np.array(DOS)

        else:
            raise ValueError("ispin must be 1 or 2.")
def read_atom_orbital_dos_streamed(path, ispin, atom_index, orbital_index):
    """
    Efficiently read PDOS for a given atom/orbital using line-by-line parsing.

    Returns:
    - (nedos,) if ispin=1
    - (nedos, 2) if ispin=2 → [:,0] = up, [:,1] = down
    """
    print("Orbvis is reading doscar to extract atom "+str(atom_index)+"'s orbital "+str(orbital_index)+"'s pdos data...")
    with open(path, 'r') as f:
        for _ in range(5):
            next(f)

        meta = next(f).split()
        nedos = int(meta[2])

        # Skip total DOS block
        for _ in range(nedos):
            next(f)

        # Skip previous atoms' PDOS blocks
        block_size = 1 + nedos  # 1 metadata + nedos lines
        for _ in range(atom_index * block_size):
            next(f)

        next(f)  # skip current atom blocks metadata line

        if ispin == 1:
            dos = []
            for _ in range(nedos):
                parts = next(f).split()
                dos.append(float(parts[1 + orbital_index]))
            return np.array(dos)

        elif ispin == 2:
            dos = []
            for _ in range(nedos):
                parts = next(f).split()
                up = float(parts[1 + 2 * orbital_index])
                down = float(parts[2 + 2 * orbital_index])
                dos.append([up, down])
            return np.array(dos)

        else:
            raise ValueError("ispin must be 1 or 2.")

def read_total_dos_streamed_soc(path):
    """
    Read total DOS from DOSCAR with SOC (non-collinear).
    
    Returns:
    - E (nedos,): energy array
    - DOS (nedos,): total DOS array
    """
    print("Orbvis is reading doscar (SOC mode) to extract tdos data...")
    with open(path, 'r') as f:
        for _ in range(5):
            next(f)

        meta = next(f).split()
        nedos = int(meta[2])

        E = []
        DOS = []

        for _ in range(nedos):
            parts = next(f).split()
            E.append(float(parts[0]))
            DOS.append(float(parts[1]))  # Only the total DOS (no up/down split)

        return np.array(E), np.array(DOS)

def read_atom_orbital_dos_streamed_soc(path, atom_index, orbital_index):
    """
    Read site- and orbital-projected DOS for SOC case.
    
    Returns:
    - DOS (nedos,): total DOS for specified atom and orbital group (s=0, p=1, d=2, f=3)
    """
    print(f"Orbvis is reading doscar (SOC mode) to extract atom {atom_index}'s orbital {orbital_index}'s pdos data...")

    with open(path, 'r') as f:
        for _ in range(5):
            next(f)

        meta = next(f).split()
        nedos = int(meta[2])

        # Skip total DOS block
        for _ in range(nedos):
            next(f)

        # Each atom's PDOS block: 1 header + nedos lines
        block_size = 1 + nedos
        skip_lines = atom_index * block_size

        for _ in range(skip_lines):
            next(f)

        next(f)  # skip atom metadata line

        dos = []
        col = 1 + 4 * orbital_index  # total, mx, my, mz → each orbital has 4 columns

        for _ in range(nedos):
            parts = next(f).split()
            dos.append(float(parts[col]))

        return np.array(dos)