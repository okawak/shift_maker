import sys
import glob
import gspread
import pandas as pd
import string
from ruamel.yaml import YAML


def data_preprocessor(df, yaml):
    alphabet = string.ascii_uppercase

    slot_array = yaml["timeslots"]
    slot_low_index = alphabet.index(slot_array[0])
    slot_high_index = alphabet.index(slot_array[-1])

    for i in range(slot_low_index, slot_high_index + 1):
        df.iloc[:, i] = df.iloc[:, i].apply(lambda x: [s.strip() for s in x.split(",")])

    comment_index = alphabet.index(yaml["comment"])
    name_index = alphabet.index(yaml["shiftername"])

    print("making comments.txt")
    with open("comments.txt", mode="w") as ftxt:
        for i in range(df.shape[0]):
            if df.iat[i, comment_index] != "":
                ftxt.write("name: " + df.iat[i, name_index] + "\n")
                ftxt.write(df.iat[i, comment_index] + "\n\n")

    return df


if __name__ == "__main__":
    json_name = glob.glob("json/*.json")
    if len(json_name) != 1:
        print("json file is not one")
        sys.exit(1)

    yaml = YAML()
    with open("sheet_structure.yaml", "r", encoding="utf-8") as fin:
        structure = yaml.load(fin)

    spread_name = structure["Structure"]["name"]
    form_sheet_yaml = structure["Structure"]["sheets"][0]

    gc = gspread.service_account(filename=json_name[0])
    sh = gc.open(spread_name)
    print("connect to " + spread_name)
    df = pd.DataFrame(sh.sheet1.get_values()[1:], columns=sh.sheet1.get_values()[0])

    df_new = data_preprocessor(df, form_sheet_yaml)

    print("making data.csv")
    df_new.to_csv("data.csv")
