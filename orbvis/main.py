# orbplot/main.py

from orbvis.band.parser import VASPStyleParser as BandParser
from orbvis.dos.parser import VASPStyleParser as DOSParser

from orbvis.band.scatter import orbscatter
from orbvis.band.parametric import orbparametric
from orbvis.dos.plot import orbdos

def run_from_config(config_path, mode="band"):
    if mode == "band":
        parser = BandParser(config_path)
        params = parser.as_dict()

        plot_option = params.get("PLOT_OPTION", 0)
        if plot_option == 0:
            orbscatter(**params)
        elif plot_option == 1:
            orbparametric(**params)
        else:
            raise ValueError("Invalid PLOT_OPTION for bandplot.")

    elif mode == "dos":
        parser = DOSParser(config_path)
        params = parser.as_dict()
        orbdos(**params)

    else:
        raise ValueError("Invalid mode. Use 'band' or 'dos'.")

# Optional CLI support
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python -m orbplot.main <band|dos> <config.in>")
    else:
        mode = sys.argv[1]
        config_path = sys.argv[2]
        run_from_config(config_path, mode)
