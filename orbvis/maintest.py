from band.parser import VASPStyleParser
from band.plotter_new import orbscatter  # 
from dos.plotter import plot_pdos
def main():
    #config_path = "sample_config.txt"
    config_path = "dosconfig.txt"
    parser = VASPStyleParser(config_path)
    params = parser.as_dict()
    print(params)
    mode = parser.get("MODE")
    plot_option = parser.get("PLOT_OPTION")

    if mode == "dos":
        plot_pdos(**params)

    elif mode == "band":
        if plot_option == 0:
            orbscatter(**params)
        elif plot_option == 1:
            plot_orb_parametric_from_parser(parser)
        else:
            raise ValueError("Invalid PLOT_OPTION for 'band' mode. Must be 0 or 1.")

    else:
        raise ValueError(f"Unknown mode: {mode}")
   
    
    #if params["PLOT_OPTION"] == 0:
    #   orbscatter(**params)
    #else:
    #   raise NotImplementedError("Parametric plot not implemented yet.")

if __name__ == "__main__":
    main()
