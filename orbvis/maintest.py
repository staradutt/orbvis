from band.parser import VASPStyleParser
from band.plotter_new import orbscatter  # 
def main():
    config_path = "sample_config.txt"
    parser = VASPStyleParser(config_path)
    params = parser.as_dict()
    print(params)
    if params["PLOT_OPTION"] == 0:
       orbscatter(**params)
    else:
       raise NotImplementedError("Parametric plot not implemented yet.")

if __name__ == "__main__":
    main()
