import sys
import glob
import gspread
from ruamel.yaml import YAML


if __name__ == "__main__":
    json_name = glob.glob("json/*.json")
    if len(json_name) != 1:
        print("json file is not one")
        sys.exit(1)

    try:
        yaml = YAML()
        with open("sheet_structure.yaml", "r", encoding="utf-8") as fin:
            structure = yaml.load(fin)

        spread_name = structure["Structure"]["name"]

        print("trying to connect " + spread_name + "...")
        gc = gspread.service_account(filename=json_name[0])
        sh = gc.open(spread_name)
        print("success!")

    except:
        print("ERROR: cannot connect to google spread sheet")
