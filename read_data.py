import sys
import glob
import gspread
import argparse
import pandas as pd
import string
from ruamel.yaml import YAML


# コマンドライン引数を設定する
def get_argperser_setting():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-i",
        "--input-domain",
        type=str,
        default="-",
        help="input the domain of the email address to set attribute 1",
    )
    return argparser


def data_preprocessor(df, yaml, domain):
    alphabet = string.ascii_uppercase

    # 名前がtestという行を削除する (testの名前は一つだけであることを想定しているので、すべてのtestをdropするように修正した方が良さそう)
    name_index = alphabet.index(yaml["shiftername"])
    name_list = df.iloc[:, name_index].values.tolist()
    test_index = name_list.index("test")

    df.drop(df.index[test_index], inplace=True)

    # 複数のメールアドレスが登録されていた場合(同じ人が何回かフォームを送ってきた場合)、タイムスタンプが新しい方を採用する
    # (日本語のアカウントでformを作成し、メールアドレスをONにするとラベルの名前は"メールアドレス"となる)
    df.drop_duplicates(subset="メールアドレス", keep="last", inplace=True)

    if domain == "-":
        print("all attribute column will be set 0")
        df["attribute"] = 0
    else:
        print('user of "hoge@' + str(domain) + '" will be set attribute 1')
        df["attribute"] = df["メールアドレス"].apply(chkdomain, in_domain=domain)

    comment_index = alphabet.index(yaml["comment"])

    print("making comments.txt...")
    with open("comments.txt", mode="w") as ftxt:
        for i in range(df.shape[0]):
            if df.iat[i, comment_index] != "":
                ftxt.write("name: " + df.iat[i, name_index] + "\n")
                ftxt.write(df.iat[i, comment_index] + "\n\n")

    return df


def chkdomain(address, in_domain):
    domain = address.split("@")[1]
    if domain == in_domain:
        return 1
    else:
        return 0


if __name__ == "__main__":
    json_array = glob.glob("json/*.json")
    if len(json_array) != 1:
        print("json file is not one")
        sys.exit(1)

    perser = get_argperser_setting()
    args = perser.parse_args()
    yaml = YAML()
    with open("sheet_structure.yaml", "r", encoding="utf-8") as fin:
        yaml_input = yaml.load(fin)

    spread_name = yaml_input["Input"]["name"]
    form_sheet_yaml = yaml_input["Input"]["sheets"][0]

    try:
        gc = gspread.service_account(filename=json_array[0])
        sh = gc.open(spread_name)
        print("connect to " + spread_name)
        df = pd.DataFrame(sh.sheet1.get_values()[1:], columns=sh.sheet1.get_values()[0])

        df_new = data_preprocessor(df, form_sheet_yaml, args.input_domain)

        print("making data.csv...")
        df_new.to_csv("data.csv", index=False)

    except:
        print("ERROR: cannot connect to google spread sheet")
