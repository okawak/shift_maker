import sys
import glob
import gspread
from ruamel.yaml import YAML


if __name__ == "__main__":
    json_array = glob.glob("json/*.json")
    if len(json_array) != 1:
        print("json key file is not one")
        sys.exit(1)

    yaml = YAML()
    with open("sheet_structure.yaml", "r", encoding="utf-8") as fin:
        yaml_input = yaml.load(fin)

    in_spread_name = yaml_input["Input"]["name"]
    out_spread_name = yaml_input["Output"]["name"]

    try:
        print("trying to connect Input gspread... : " + in_spread_name)
        gc = gspread.service_account(filename=json_array[0])
        sh_in = gc.open(in_spread_name)
        print("success!")

        print("trying to connect Output gspread... : " + out_spread_name)
        sh_out = gc.open(out_spread_name)
        print("success!")

    except:
        print("ERROR: cannot connect to google spread sheet")
