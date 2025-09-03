import argparse
from orbvis.band.parser import VASPStyleParser
from orbvis.band.plotter import orbscatter  # 
from orbvis.dos.plotter import plot_pdos

def run_from_config(config_path):
    parser = VASPStyleParser(config_path)
    params = parser.as_dict()
    print("[INFO] Parsed parameters:", params)

    mode = parser.get("MODE")

    if mode == "dos":
        plot_pdos(**params)

    elif mode == "band":
        orbscatter(**params)

    else:
        raise ValueError(f"Unknown mode: '{mode}'. Must be 'band' or 'dos'.")

def main():
    parser = argparse.ArgumentParser(
        description="Orbital-resolved band structure and DOS plotter"
    )
    parser.add_argument(
        "config",
        type=str,
        help="Path to the configuration file (.txt)",
    )

    args = parser.parse_args()
    run_from_config(args.config)

if __name__ == "__main__":
    main()
