import pandas as pd
import glob
import sys
import string
import pulp
import gspread
from ruamel.yaml import YAML
from gspread_dataframe import set_with_dataframe


class Scheduling:
    __modelyaml_name = "model.yaml"
    __sheetyaml_name = "sheet_structure.yaml"
    __scheduleyaml_name = "schedule.yaml"
    __datacsv_name = "data.csv"

    alphabet = string.ascii_uppercase
    list_pa = []
    list_ds = []

    def __init__(self):
        print("initializing Scheduling class...")
        yaml = YAML()
        with open(self.__modelyaml_name, "r", encoding="utf-8") as fin:
            self.__modelyaml = yaml.load(fin)

        with open(self.__sheetyaml_name, "r", encoding="utf-8") as fin:
            self.__sheetyaml = yaml.load(fin)

        with open(self.__scheduleyaml_name, "r", encoding="utf-8") as fin:
            self.__scheduleyaml = yaml.load(fin)

        json_name = glob.glob("json/*.json")
        if len(json_name) != 1:
            print("json file is not one")
            sys.exit(1)

        self.__json = json_name[0]
        self.__datadf = pd.read_csv(self.__datacsv_name)
        self.InitOutputArray()
        self.InitVariable()
        print("finished!")

    def InitOutputArray(self):
        # table1 : shift table based on name
        table1_Ncolumn = len(self.__scheduleyaml["schedule"]) + 2
        table1_Nindex = (
            len(self.__modelyaml["Work"]) * len(self.__scheduleyaml["Anchor"]) + 2
        )

        self.__table1_array = [
            ["" for i in range(table1_Ncolumn)] for j in range(table1_Nindex)
        ]
        for i in range(table1_Ncolumn - 2):
            self.__table1_array[0][i + 2] = self.__scheduleyaml["schedule"][i]["date"]
            self.__table1_array[1][i + 2] = self.__scheduleyaml["schedule"][i]["site"]

        for j in range(table1_Nindex - 2):
            index = j % len(self.__modelyaml["Work"])
            group = int(j / len(self.__modelyaml["Work"]))
            if index == 0:
                self.__table1_array[j + 2][0] = self.__scheduleyaml["Anchor"][group]
                self.__table1_array[j + 2][1] = self.__modelyaml["Work"][index]
            else:
                self.__table1_array[j + 2][1] = self.__modelyaml["Work"][index]

        # table2 : shift table based on person
        table2_Ncolumn = (
            len(self.__scheduleyaml["schedule"]) * len(self.__scheduleyaml["Anchor"])
            + 1
        )
        table2_Nindex = len(self.__datadf) + 2
        self.__table2_array = [
            ["" for i in range(table2_Ncolumn)] for j in range(table2_Nindex)
        ]
        for i in range(table2_Ncolumn - 1):
            index = i % len(self.__scheduleyaml["Anchor"])
            group = int(i / len(self.__scheduleyaml["Anchor"]))
            if index == 0:
                self.__table2_array[0][i + 1] = self.__scheduleyaml["schedule"][group][
                    "date"
                ]
                self.__table2_array[1][i + 1] = self.__scheduleyaml["Anchor"][index]
            else:
                self.__table2_array[1][i + 1] = self.__scheduleyaml["Anchor"][index]

        for j in range(table2_Nindex - 2):
            name_index = (
                self.alphabet.index(
                    self.__sheetyaml["Input"]["sheets"][0]["shiftername"]
                )
                + 1
            )
            self.__table2_array[j + 2][0] = self.__datadf.iat[j, name_index]

    def InitVariable(self):
        attribute_index = (
            self.alphabet.index(self.__sheetyaml["Input"]["sheets"][0]["attribute"]) + 1
        )
        for i in range(len(self.__datadf)):
            self.list_pa.append(
                (self.__datadf.iat[i, 0], self.__datadf.iat[i, attribute_index])
            )
        for i in range(len(self.__scheduleyaml["schedule"])):
            for j in range(len(self.__scheduleyaml["schedule"][i]["contents"])):
                # list_ds.append((i, j))
                self.list_ds.append(
                    (
                        self.__scheduleyaml["schedule"][i]["date"],
                        self.__scheduleyaml["schedule"][i]["contents"][j]["time"],
                    )
                )

    # ====== main function========
    def SolveProblem(self):
        print("solving the problem...")
        ShiftScheduling = pulp.LpProblem("ShiftScheduling", pulp.LpMinimize)

        """
        valiable: x
        x[p, a, d, s] => the (p, a) person take (d, s) shift = 1, not take = 0
          p: person id
          a: person attribute (like new-person)
          d: day of the shift
          s: shift id
        """
        self.x = {}
        for p, a in self.list_pa:
            for d, s in self.list_ds:
                self.x[p, a, d, s] = pulp.LpVariable(
                    "x({:},{:},{:},{:})".format(p, a, d, s), 0, 1, pulp.LpInteger
                )

        # default object functiion
        obj_default = pulp.lpSum(self.x)

        ShiftScheduling += obj_default

        # CONDITION
        # number of people
        for d, s in self.list_ds:
            ShiftScheduling += pulp.lpSum(
                self.x[p, a, d, s] for p, a in self.list_pa
            ) >= len(self.__modelyaml["Work"])

        # not take shift
        NG_list = self.GetNGList()
        for p, a, d, s in NG_list:
            ShiftScheduling += self.x[p, a, d, s] == 0

        # solve
        try:
            results = ShiftScheduling.solve()
            print(
                "optimality = {:}, target value = {:}".format(
                    pulp.LpStatus[results], pulp.value(ShiftScheduling.objective)
                )
            )
        except:
            print("not solved...")

    # ====== end =================

    def GetNGList(self):
        return []

    def SetResult(self):
        print("setting the solved result...")

        name_index = (
            self.alphabet.index(self.__sheetyaml["Input"]["sheets"][0]["shiftername"])
            + 1
        )
        for d, s in self.list_ds:
            itr = 0
            for p, a in self.list_pa:
                if pulp.value(self.x[p, a, d, s]) == 1:
                    # for table1
                    day_id = self.__table1_array[0].index(d)
                    slot_id = [r[0] for r in self.__table1_array].index(s)
                    self.__table1_array[slot_id + itr][day_id] = self.__datadf.iat[
                        p, name_index
                    ]

                    # for table2
                    time_id = self.__table2_array[0].index(d) + (
                        self.__table2_array[1].index(s) - 1
                    )
                    p_id = p + 2
                    self.__table2_array[p_id][time_id] = "○"

                    itr += 1

    def SendOutputSpreadSheet(self):
        print("start sending data...")
        spread_name = self.__sheetyaml["Output"]["name"]
        sheetsyaml = self.__sheetyaml["Output"]["sheets"]
        if len(sheetsyaml) != 2:
            print("\tSet two Output sheets in sheet_structure.yaml")
            sys.exit(1)

        try:
            print("\ttrying to connect " + spread_name + "...")
            gc = gspread.service_account(filename=self.__json)
            sh = gc.open(spread_name)
            print("\tconnect to spreadsheet: " + spread_name)

            ws1 = sh.worksheet(sheetsyaml[0]["name"])
            ws1.clear()
            set_with_dataframe(
                ws1, pd.DataFrame(self.__table1_array), include_column_header=False
            )
            print("\tconnect to sheet: " + sheetsyaml[0]["name"])

            ws2 = sh.worksheet(sheetsyaml[1]["name"])
            ws2.clear()
            set_with_dataframe(
                ws2, pd.DataFrame(self.__table2_array), include_column_header=False
            )
            print("\tconnect to sheet: " + sheetsyaml[1]["name"])

        except:
            print("\tERROR: cannot connect to google spread sheet")
            sys.exit(1)


if __name__ == "__main__":
    scheduling = Scheduling()
    scheduling.SolveProblem()
    scheduling.SetResult()
    scheduling.SendOutputSpreadSheet()
    print("finish!")
