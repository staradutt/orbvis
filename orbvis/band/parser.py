class VASPStyleParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.params = {
            'PROCAR_PATH': None,
            'ISPIN': 1,
            'ORBITAL_INFO': None,  # Required
            'SCALE': 1,
            'TRANSPARENCY': 70,
            'EFERMI': None,
            'TITLE': 'Orbital projected Band Structure',
            'FIGSIZEX': 10,
            'FIGSIZEY': 6,
            'PLOT_OPTION': 0,  # 0 for scatter, 1 for parametric
            'COLOR_SCHEME': None,  # Required validation later
            'YMIN': -5.0,
            'YMAX': 5.0,
            'LINEWIDTH': 1.0,
            'DPI': 300,
            'SAVEAS': 'orbband.jpg',
        }

        self._parse()
        self._validate()
        self._apply_default_color_scheme()

    def _parse(self):
        with open(self.filepath, 'r') as f:
            lines = f.readlines()

        buffer = ""
        parsing_key = None

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            if '#' in line:
                line = line.split('#', 1)[0].strip()

            if '=' in line and parsing_key is None:
                key, value = map(str.strip, line.split('=', 1))
                key = key.upper()

                if key not in self.params:
                    raise ValueError(f"Unknown config key: {key}")

                if key in ['ORBITAL_INFO', 'COLOR_SCHEME']:
                    buffer = value
                    parsing_key = key
                    if value.endswith(']'):  # Single-line list
                        self._parse_buffered_value(parsing_key, buffer)
                        parsing_key = None
                        buffer = ""
                else:
                    self._parse_single_key(key, value)

            elif parsing_key in ['ORBITAL_INFO', 'COLOR_SCHEME']:
                buffer += line
                if line.endswith(']'):
                    self._parse_buffered_value(parsing_key, buffer)
                    parsing_key = None
                    buffer = ""

    def _parse_buffered_value(self, key, buffer):
        try:
            parsed = ast.literal_eval(buffer)
        except Exception:
            raise ValueError(f"Failed to parse {key}. Check syntax.")

        if key == 'ORBITAL_INFO':
            self._validate_orbital_info(parsed)
            self.params[key] = parsed

        elif key == 'COLOR_SCHEME':
            if self.params['PLOT_OPTION'] == 0:
                if isinstance(parsed, int):
                    self.params[key] = parsed
                elif isinstance(parsed, list) and all(isinstance(c, str) for c in parsed):
                    self.params[key] = parsed
                elif isinstance(parsed, str):
                    self.params[key] = parsed.strip()
                else:
                    raise ValueError("COLOR_SCHEME must be an int, list of color strings, or a valid colormap name when PLOT_OPTION = 0.")
            elif self.params['PLOT_OPTION'] == 1:
                if not isinstance(parsed, str):
                    raise ValueError("COLOR_SCHEME must be a valid colormap name string when PLOT_OPTION = 1.")
                self.params[key] = parsed.strip()
                
    def _parse_single_key(self, key, value):
        if key in ['ISPIN', 'PLOT_OPTION', 'SCALE']:
            self.params[key] = int(value)

        elif key in ['YMIN', 'YMAX', 'FIGSIZEX', 'FIGSIZEY', 'DPI', 'LINEWIDTH', 'TRANSPARENCY']:
            try:
                self.params[key] = float(value)
            except ValueError:
                raise ValueError(f"{key} must be a numerical value.")

        elif key == 'EFERMI':
            try:
                self.params[key] = float(value)
            except ValueError:
                raise ValueError("EFERMI must be a float.")

        elif key == 'SAVEAS':
            val = value.strip()
            if not (val.lower().endswith('.jpg') or val.lower().endswith('.png')):
                raise ValueError("SAVEAS must end with .jpg or .png")
            self.params[key] = val

        elif key == 'COLOR_SCHEME':
            if self.params['PLOT_OPTION'] == 0:
                try:
                    parsed = ast.literal_eval(value)
                    if isinstance(parsed, int):
                        self.params[key] = parsed
                    elif isinstance(parsed, list) and all(isinstance(c, str) for c in parsed):
                        self.params[key] = parsed
                    elif isinstance(parsed, str):
                        self.params[key] = parsed.strip()
                    else:
                        raise ValueError
                except Exception:
                    # Fallback to treating it as a simple colormap string (e.g. tab20)
                    self.params[key] = value.strip()
            else:
                # PLOT_OPTION == 1: only a colormap name string is allowed
                if not isinstance(value, str):
                    raise ValueError("COLOR_SCHEME must be a colormap name string when PLOT_OPTION = 1.")
                self.params[key] = value.strip()

        else:
            self.params[key] = value

    def _validate_orbital_info(self, value):
        if not isinstance(value, list):
            raise ValueError("ORBITAL_INFO must be a list.")

        for item in value:
            if not (isinstance(item, (list, tuple)) and len(item) == 3):
                raise ValueError("Each ORBITAL_INFO entry must be [atom_indices, element, orbital_indices].")

            atom_ids, element, orbitals = item

            if not (isinstance(atom_ids, list) and all(isinstance(i, int) for i in atom_ids)):
                raise ValueError("atom_indices must be a list of integers.")

            if not isinstance(element, str):
                raise ValueError("element must be a string.")

            if not (isinstance(orbitals, list) and all(isinstance(i, int) for i in orbitals)):
                raise ValueError("orbital_indices must be a list of integers.")



    def _validate(self):
        if self.params['ORBITAL_INFO'] is None:
            raise ValueError("ORBITAL_INFO is required and cannot be None.")

        if self.params['PLOT_OPTION'] not in [0, 1]:
            raise ValueError("PLOT_OPTION must be 0 or 1.")

        cs = self.params['COLOR_SCHEME']
        if cs is None:
            raise ValueError("COLOR_SCHEME must be defined.")

        if self.params['PLOT_OPTION'] == 1:
            # Must be a string colormap
            if not isinstance(cs, str) or not hasattr(cm, cs):
                raise ValueError(f"COLOR_SCHEME must be a valid matplotlib colormap name string (e.g. 'plasma') when PLOT_OPTION = 1.")
        elif isinstance(cs, str):
            # If PLOT_OPTION == 0 and string is given, validate it's a valid colormap
            if not hasattr(cm, cs):
                raise ValueError(f"'{cs}' is not a valid matplotlib colormap name.")
    
    def _apply_default_color_scheme(self):
        if self.params['COLOR_SCHEME'] is None:
            self.params['COLOR_SCHEME'] = "tab20" if self.params['PLOT_OPTION'] == 0 else "plasma"

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

class VASPStyleParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.params = {
            'PROCAR_PATH': None,
            'ISPIN': 1,
            'ORBITAL_INFO': None,  #Required
            'SCALE': 1,
            'TRANSPARENCY':70,
            'EFERMI': None,
            'TITLE': 'Orbital projected Band Structure',
            'FIGSIZEX': 10,
            'FIGSIZEY': 6,
            'PLOT_OPTION': 0, #0 for scatter 1 for parametric
            'COLOR_SCHEME': None,  # Required validation later
            'YMIN': -5.0,
            'YMAX': 5.0,
            'LINEWIDTH': 1.0,
            'DPI': 300,
            'SAVEAS': 'orbband.jpg',
            
        }
        self._parse()
        self._validate()
        self._apply_default_color_scheme()
    def _parse(self):
        with open(self.filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Remove inline comments , only keep stuff before first inline comment 
                
                if '#' in line:
                    line = line.split('#', 1)[0].strip()
                #after splitting the comment also if there are invalid inputs without proper key value assignment
                #it will catch them
                if not line or '=' not in line:
                    continue

                key, value = map(str.strip, line.split('=', 1))#str strip to remove white spaces before after equal to sign
                
                key = key.upper()#if user enters lowercase

                if key not in self.params:
                    raise ValueError(f"Unknown config key: {key}. Please enter proper config key.")

                # PARSIng loGiC
                if key =='ORBITAL_INFO':
                    try:
                        self.params[key] = ast.literal_eval(value)
                        if not isinstance(self.params[key], list):
                            raise ValueError
                    except Exception:
                        raise ValueError("ORBITAL_INFO must have a valid nested python list type structure.")
                
                
                elif key == 'COLOR_SCHEME':
                    if self.params['PLOT_OPTION'] == 0:
                        try:
                            val = ast.literal_eval(value)

                            # single integer case
                            if isinstance(val, int):
                                self.params[key] = val

                            #second case: list of strings (color names)
                            elif isinstance(val, list) and all(isinstance(v, str) for v in val):
                                self.params[key] = val

                            else:
                                raise ValueError
                        except Exception:
                            raise ValueError(
                                "COLOR_SCHEME must be either a single integer or a list of color strings when PLOT_OPTION is 0."
                            )
                    else:
                        # When PLOT_OPTION is 1, it must be a matplotlib colormap string
                        self.params[key] = value.strip()
                elif key in ['ISPIN', 'PLOT_OPTION','SCALE']:
                    self.params[key] = int(value)
                elif key in ['YMIN', 'YMAX', 'FIGSIZEX', 'FIGSIZEY','DPI','LINEWIDTH','TRANSPARENCY']:
                    try:
                        self.params[key] = float(value)
                    except ValueError:
                        raise ValueError(f"{key} must be a numerical value.")
                elif key == 'EFERMI':
                    try:
                        self.params[key] = float(value)
                    except ValueError:
                        raise ValueError("EFERMI must be a float if provided.")
                elif key == 'SAVEAS':
                    val = value.strip()
                    if not (val.lower().endswith('.jpg') or val.lower().endswith('.png')):
                        raise ValueError("SAVEAS must end with .jpg or .png")
                    self.params[key] = val
                else:
                    self.params[key] = value
    
    def _validate(self):
        if self.params['ORBITAL_INFO'] is None:
            raise ValueError("ORBITAL_INFO is Required and cannot be None.")

        if self.params['PLOT_OPTION'] not in [0, 1]:
            raise ValueError("PLOT_OPTION must be 0 or 1.")

        if self.params['COLOR_SCHEME'] is None:
            raise ValueError("COLOR_SCHEME must be defined.")

        if self.params['PLOT_OPTION'] == 1:
            if not isinstance(self.params['COLOR_SCHEME'], str):
                raise ValueError("When PLOT_OPTION is 1, COLOR_SCHEME must be a valid colormap name.")
    
    def _apply_default_color_scheme(self):
        if self.params['COLOR_SCHEME'] is None:
            self.params['COLOR_SCHEME'] = 0 if self.params['PLOT_OPTION'] == 0 else "plasma"
    #utility functions to be called later in the code for easy calling
    def get(self, key):
        return self.params.get(key.upper())

    def as_dict(self):
        return self.params.copy()