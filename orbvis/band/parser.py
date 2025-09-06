import ast
import matplotlib.cm as cm
from matplotlib import colors as mcolors
import numpy as np
import re


from distinctipy import get_colors, get_hex

class VASPStyleParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.params = {
            'MODE': 'band',
            'PROCAR_PATH': None,
            'DOSCAR_PATH': None,
            'ISPIN': 1,
            'SOC': False, 
            'ORBITAL_INFO': None,

            # BAND-only
            'BS_LINEWIDTH': 1.0,
            'SCALE': 1.0,

            # DOS-only
            'TDOS_LINEWIDTH': 1.0,
            'PDOS_LINEWIDTH': 1.0,
            'SIGMA': 2.0,
            'XMIN': None,             # Optional xlim lower limit (for DOS only)
            'XMAX': None,             # Optional xlim (for DOS only)
            'SHOW_TDOS': True,         # Whether to show TDOS in PDOS plots
            # Common
            'TITLE': 'Orbvis',
            'EFERMI': None,
            'COLOR_SCHEME': None,
            'SAVEAS': 'output.png',
            'DPI': 300,
            'YMIN': -5.0,
            'YMAX': 5.0,
            'FIGSIZEX': 10,
            'FIGSIZEY': 6,
            'TRANSPARENCY': 70,
            'LEGEND_LOC': None,
            'PLOT_OPTION': 0  # # 0 = orbital scatterplot; 1 (parametric) is not implemented yet
        }

        self._parse()
        self._apply_defaults()
        self._validate()

    def _parse(self):
        with open(self.filepath, 'r') as f:
            lines = f.readlines()

        buffer = ""
        parsing_key = None
        bracket_balance = 0

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            if '#' in line:
                line = line.split('#', 1)[0].strip()

            if parsing_key:
                buffer += ' ' + line
                bracket_balance += line.count('[') - line.count(']')
                if bracket_balance <= 0:
                    self._parse_buffered_value(parsing_key, buffer)
                    parsing_key = None
                    buffer = ""
                continue

            if '=' in line:
                key, value = map(str.strip, line.split('=', 1))
                key = key.upper()

                if key not in self.params:
                    raise ValueError(f"Unknown config key: {key}")

                if key in ['ORBITAL_INFO', 'COLOR_SCHEME']:
                    buffer = value
                    parsing_key = key
                    bracket_balance = value.count('[') - value.count(']')
                    if bracket_balance <= 0:
                        self._parse_buffered_value(key, buffer)
                        parsing_key = None
                        buffer = ""
                else:
                    self._parse_single_key(key, value)

    def _parse_buffered_value(self, key, buffer):
        try:
            parsed = ast.literal_eval(buffer)
        except Exception:
            parsed = buffer.strip()

        if key == 'ORBITAL_INFO':
            if not isinstance(parsed, list):
                raise ValueError("ORBITAL_INFO must be a list.")
            self._validate_orbital_info(parsed)
            self.params[key] = parsed

        elif key == 'COLOR_SCHEME':
            if isinstance(parsed, int):
                if parsed not in [0, 1]:
                    raise ValueError("COLOR_SCHEME integer must be 0 or 1.")
                self.params[key] = parsed
            elif isinstance(parsed, list):
                try:
                    self.params[key] = [self._normalize_color(c) for c in parsed]
                except ValueError as e:
                    raise ValueError(f"Invalid color in COLOR_SCHEME: {e}")
            elif isinstance(parsed, str):
                self.params[key] = parsed.strip()
            else:
                raise ValueError("COLOR_SCHEME must be int, list of color strings, or colormap name.")

    def _parse_single_key(self, key, value):
        if key in ['ISPIN', 'DPI']:
            self.params[key] = int(value)
        elif key in ['YMIN', 'YMAX','XMIN', 'XMAX','FIGSIZEX', 'FIGSIZEY', 'TRANSPARENCY', 'EFERMI', 'SCALE', 'BS_LINEWIDTH', 'TDOS_LINEWIDTH', 'PDOS_LINEWIDTH', 'SIGMA']:
            self.params[key] = float(value)
        elif key == 'LEGEND_LOC':
            self.params[key] = value.strip().lower()

        elif key == 'SHOW_TDOS':
            val = value.lower()
            if val in ['true', '1']:
                self.params[key] = True
            elif val in ['false', '0']:
                self.params[key] = False
            else:
                raise ValueError("SHOW_TDOS must be True or False.")
        elif key == 'MODE':
            val = value.strip().lower()
            if val not in ['band', 'dos']:
                raise ValueError("MODE must be 'band' or 'dos'.")
            self.params[key] = val
        elif key == 'SOC':
            val = value.lower()
            if val in ['true', '1', 'on']:
                self.params[key] = True
                self.params['ISPIN'] = 1  # Force ISPIN = 1 when SOC is enabled
            elif val in ['false', '0', 'off']:
                self.params[key] = False
            else:
                raise ValueError("SOC must be True, False, 1, 0, on, or off.")
        elif key == 'PLOT_OPTION':
            val = int(value)
            if val not in [0, 1]:
                raise ValueError("PLOT_OPTION must be 0 or 1.")
            if self.params['MODE'] == 'dos' and val == 1:
                raise ValueError("PLOT_OPTION = 1 (parametric) is not allowed in DOS mode.")
            self.params[key] = val
        elif key == 'SAVEAS':
            val = value.strip()
            if not (val.lower().endswith('.jpg') or val.lower().endswith('.png')):
                raise ValueError("SAVEAS must end with .jpg or .png")
            self.params[key] = val
        elif key == 'COLOR_SCHEME':
            try:
                parsed = ast.literal_eval(value)
            except Exception:
                parsed = value.strip()
            self._parse_buffered_value(key, parsed)
        else:
            self.params[key] = value

    def _normalize_color(self, c):
        try:
            c = str(c).strip().lstrip('#')
            if len(c) == 6:
                return '#' + c.upper()
            # Try to interpret as named color
            return mcolors.to_hex(c)
        except Exception:
            raise ValueError(f"Invalid color code or name: {c}")

    def _validate_orbital_info(self, value):
        for item in value:
            if not (isinstance(item, (list, tuple)) and len(item) == 3):
                raise ValueError("Each ORBITAL_INFO entry must be [atom_indices, element, orbital_indices].")
            atoms, element, orbitals = item
            if not (isinstance(atoms, list) and all(isinstance(i, int) for i in atoms)):
                raise ValueError("atom_indices must be a list of integers.")
            if not isinstance(element, str):
                raise ValueError("element must be a string.")
            if not (isinstance(orbitals, list) and all(isinstance(i, int) for i in orbitals)):
                raise ValueError("orbital_indices must be a list of integers.")

    def _apply_defaults(self):
        if self.params['COLOR_SCHEME'] is None:
            self.params['COLOR_SCHEME'] = 0  # Default to distinctipy, non-pastel

    def _validate(self):
        mode = self.params['MODE']

        if mode == 'band':
            if not self.params['PROCAR_PATH']:
                raise ValueError("PROCAR_PATH is required in band mode.")

            if self.params['XMIN'] is not None or self.params['XMAX'] is not None:
                raise ValueError("XMIN/XMAX are not allowed in band mode.")
        elif mode == 'dos':
            if not self.params['DOSCAR_PATH']:
                raise ValueError("DOSCAR_PATH is required in dos mode.")
            if self.params['PLOT_OPTION'] != 0:
                raise ValueError("Only PLOT_OPTION = 0 is allowed in DOS mode.")

        if self.params['ORBITAL_INFO'] is None:
            raise ValueError("ORBITAL_INFO is required.")

        cs = self.params['COLOR_SCHEME']
        plot_opt = self.params['PLOT_OPTION']

        if plot_opt == 1:
            raise NotImplementedError("PLOT_OPTION = 1 (parametric plotting) is not yet implemented. Set PLOT_OPTION = 0.")
            #if not isinstance(cs, str) or not hasattr(cm, cs):
            #    raise ValueError("COLOR_SCHEME must be a valid matplotlib colormap name string when PLOT_OPTION = 1.")
        elif plot_opt == 0:
            if isinstance(cs, int):
                if cs not in [0, 1]:
                    raise ValueError("COLOR_SCHEME integer must be 0 or 1.")
            elif isinstance(cs, str):
                if not hasattr(cm, cs):
                    raise ValueError(f"Unknown matplotlib colormap: {cs}")
            elif isinstance(cs, list):
                try:
                    [self._normalize_color(c) for c in cs]
                except Exception:
                    raise ValueError("Invalid entry in COLOR_SCHEME list.")
            else:
                raise ValueError("Invalid COLOR_SCHEME format.")


    def get(self, key):
        return self.params.get(key.upper())

    def as_dict(self):
        return self.params.copy()


def read_band_energies_and_klist_from_PROCAR(file_path, ispin=1):
    """
    Efficiently extracts band eigenvalues and k-point list (coordinates + weights) from PROCAR.

    Parameters:
    - file_path (str): Path to PROCAR file
    - ispin (int): Spin polarization (1 or 2)

    Returns:
    - band_energies: np.ndarray
        Shape (num_band, num_kpt) if ispin=1
        Shape (2, num_band, num_kpt) if ispin=2
    - klist: np.ndarray of shape (num_kpt, 5)
        Each row: [kpt_index, kx, ky, kz, weight]
    """

    print("Orbvis is reading band energies and kpoint list from PROCAR ...")   
    with open(file_path, "r") as file:
        next(file)  # Skip first header line
        header = next(file).split()
        num_kpt = int(header[header.index("k-points:") + 1])
        num_band = int(header[header.index("bands:") + 1])
        #num_ions = int(header[header.index("ions:") + 1])  # Not used in this, I have got this block from orbital specific bs 

        # Initialize arrays
        if ispin == 1:
            band_energies = np.zeros((num_band, num_kpt))
        elif ispin == 2:
            band_energies = np.zeros((2, num_band, num_kpt))
        else:
            raise ValueError("ISPIN must be 1 or 2")

        klist = np.zeros((num_kpt, 5))  # [index, kx, ky, kz, weight]

        # State tracking
        current_kpt = -1
        current_band = -1
        current_spin = 0

        for line in file:
            line = line.strip()
            if not line:
                continue

            if line.startswith("k-point"):
                current_kpt += 1
                current_band = -1
                

                if current_spin == 0:  
        
                    float_values = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                    if len(float_values) >= 4:
                        kx, ky, kz = map(float, float_values[1:4])
                        weight = float(float_values[-1])
                        klist[current_kpt] = [current_kpt, kx, ky, kz, weight]
                        
                    else: 
                        raise ValueError("Invalid format")

                continue

            if line.startswith("band"):
                current_band += 1
                try:
                    parts = line.split()
                    energy = float(parts[parts.index("energy") + 1])
                except (ValueError, IndexError):
                    energy = 0.0

                if ispin == 1:
                    band_energies[current_band, current_kpt] = energy
                else:
                    band_energies[current_spin, current_band, current_kpt] = energy

            # Move to second spin block
            if ispin == 2 and current_kpt == num_kpt - 1 and current_band == num_band - 1:
                current_spin += 1
                if current_spin >= 2:
                    break  # Finished both spin channels
                current_kpt = -1
                current_band = -1
    print("Orbvis is done reading band energies and kpoint list from PROCAR")
    return band_energies, klist

def get_tot_index_from_procar(path):
    with open(path) as f:
        for line in f:
            if line.strip().startswith('ion') and 'tot' in line:
                return line.strip().split()[1:].index('tot')
            

def orbvis_orbital_specific_band_data_from_PROCAR(file_path,ion_index,orbital_index, ispin=1):
   
    """
    Extracts orbital-projected band structure data from a VASP PROCAR file in a memory efficient manner by reading it line-by-line.
    Does not load the entire procar file into memory as it can be quite large for some calculations
    Parameters:
    - file_path (str): Path to the PROCAR file
    - ion_index (int): index of the ion (atom) starting from 0
    - orbital_index (int): index of the orbital column (s=0, py=1, ..., x2-y2=8, tot=9)
    - ispin (int): 1 or 2 (from INCAR setting)

    Returns:
    - numpy.ndarray: Shape (num_band, num_kpt) for ispin=1, or (2, num_band, num_kpt) for ispin=2
    """
    print("orbvis is reading orbital specific band data from PROCAR for atom "+str(ion_index)+"'s orbital "+str(orbital_index))
    with open(file_path, "r") as file:
        next(file)  # skip first header line lm decomposed 
        header = next(file)  # read second line
        temp_h = header.split()
        num_kpt = int(temp_h[temp_h.index("k-points:") + 1])
        num_band = int(temp_h[temp_h.index("bands:") + 1])
        #num_ions = int(temp_h[temp_h.index("ions:") + 1])
        
        #initialize output array
        if ispin == 1:
            band_data = np.zeros(( num_band, num_kpt))
        elif ispin == 2:
            band_data = np.zeros((2,num_band,num_kpt))
        else:
            raise ValueError("Invalid ispin value (must be either 1 or 2)")

        current_kpt = -1
        current_band = -1
        current_spin = 0
        ion_line_counter = 0
        in_spin_block = True

        for line in file:
            line = line.strip()

            if not line:
                continue  # Skip empty lines

            if line.startswith("k-point"):
                current_kpt += 1
                current_band = -1
                ion_line_counter = 0
                continue

            if line.startswith("band"):
                current_band += 1
                ion_line_counter = 0
                continue

            if line.startswith("ion"):
                continue  # Skip orbital header line

            if line.startswith("tot"):
                continue  # Skip total line

            # currently in the ion lines now
            if current_kpt >= 0 and current_band >= 0:
                ion_line_counter += 1
                if ion_line_counter == ion_index + 1:  # 1 based counting in PROCAR
                    try:
                        value = float(line.split()[orbital_index + 1])  # +1 skips ion number
                    except (ValueError, IndexError):
                        value = 0.0
                    if ispin == 1:
                        band_data[current_band,current_kpt] = value
                    elif ispin ==2:
                        band_data[current_spin, current_band, current_kpt] = value

            # If ispin = 2, check if we are starting the second spin block
            if ispin == 2 and current_kpt == num_kpt - 1 and current_band == num_band - 1:
                current_spin += 1
                if current_spin >= 2:
                    break  # Done reading both spin blocks so exit loop
                current_kpt = -1
                current_band = -1
                ion_line_counter = 0


    return band_data



def read_band_energies_and_klist_from_PROCAR_SOC(file_path):
    """
    Extract band energies and k-point list from PROCAR in LSORBIT (SOC) mode.

    Parameters:
    - file_path (str): Path to the PROCAR file

    Returns:
    - band_energies: np.ndarray of shape (num_band, num_kpt)
    - klist: np.ndarray of shape (num_kpt, 5), each row = [kpt_index, kx, ky, kz, weight]
    """

    print("Orbvis is reading band energies and k-point list from PROCAR (SOC)...")

    with open(file_path, 'r') as file:
        next(file)  # Skip first line
        header = next(file).split()
        num_kpt = int(header[header.index("k-points:") + 1])
        num_band = int(header[header.index("bands:") + 1])
        # num_ions = int(header[header.index("ions:") + 1])  # Optional

        band_energies = np.zeros((num_band, num_kpt))
        klist = np.zeros((num_kpt, 5))  # [index, kx, ky, kz, weight]

        current_kpt = -1
        current_band = -1

        for line in file:
            line = line.strip()
            if not line:
                continue

            if line.startswith("k-point"):
                current_kpt += 1
                current_band = -1

                float_values = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                if len(float_values) >= 4:
                    kx, ky, kz = map(float, float_values[1:4])
                    weight = float(float_values[-1])
                    klist[current_kpt] = [current_kpt, kx, ky, kz, weight]
                else:
                    raise ValueError("Invalid k-point format")

            elif line.startswith("band"):
                current_band += 1
                try:
                    parts = line.split()
                    energy = float(parts[parts.index("energy") + 1])
                except (ValueError, IndexError):
                    energy = 0.0
                band_energies[current_band, current_kpt] = energy

    print("Orbvis is done reading PROCAR(SOC).")
    return band_energies, klist



def orbvis_orbital_specific_band_data_from_PROCAR_SOC(file_path, ion_index, orbital_index):
    """
    Extracts orbital-projected band structure data from a VASP PROCAR file with LSORBIT = .TRUE. (SOC).
    Only reads the first of four projection blocks (orbital character, not spin components).

    Parameters:
    - file_path (str): Path to the PROCAR file
    - ion_index (int): index of the ion (starting from 0)
    - orbital_index (int): index of the orbital column (s=0, py=1, ..., x2-y2=8, tot=9)

    Returns:
    - band_data: np.ndarray of shape (num_band, num_kpt)
    """
    print(f"Orbvis is reading orbital {orbital_index} of atom {ion_index} from PROCAR (SOC)...")

    with open(file_path, "r") as file:
        next(file)  # Skip first comment line
        header = next(file).split()
        num_kpt = int(header[header.index("k-points:") + 1])
        num_band = int(header[header.index("bands:") + 1])
        # num_ions = int(header[header.index("ions:") + 1])  # Not used here

        band_data = np.zeros((num_band, num_kpt))

        current_kpt = -1
        current_band = -1
        ion_line_counter = 0
        in_first_block = True

        for line in file:
            line = line.strip()

            if not line:
                continue

            if line.startswith("k-point"):
                current_kpt += 1
                current_band = -1
                continue

            if line.startswith("band"):
                current_band += 1
                ion_line_counter = 0
                in_first_block = True
                continue

            if line.startswith("ion"):
                continue  # Skip orbital label row

            if line.startswith("tot"):
                if in_first_block:
                    in_first_block = False  # Now entering spin-x block
                continue  # Skip 'tot' line

            if current_kpt >= 0 and current_band >= 0 and in_first_block:
                ion_line_counter += 1
                if ion_line_counter == ion_index + 1:
                    try:
                        value = float(line.split()[orbital_index + 1])  # +1 skips 'ion' index
                    except (ValueError, IndexError):
                        value = 0.0
                    band_data[current_band, current_kpt] = value

    print("Orbvis is done reading orbital-projected data(SOC).")
    return band_data
 