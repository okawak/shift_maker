import pandas as pd
import os
import glob
import sys
import string
import pulp
import gspread
from ruamel.yaml import YAML
from gspread_dataframe import set_with_dataframe


class Scheduling:
    alphabet = string.ascii_uppercase
    # list of (personname, attribute_id)
    __list_pa = []
    # list of (day, time, shift)
    __list_dts = []

    def __init__(self):
        print("initializing Scheduling class...")
        yaml = YAML()
        with open("model.yaml", "r", encoding="utf-8") as fin:
            self.__modelyaml = yaml.load(fin)

        with open("sheet_structure.yaml", "r", encoding="utf-8") as fin:
            self.__sheetyaml = yaml.load(fin)

        with open("schedule.yaml", "r", encoding="utf-8") as fin:
            self.__scheduleyaml = yaml.load(fin)

        json_array = glob.glob("json/*.json")
        if len(json_array) != 1:
            print("json file is not one")
            sys.exit(1)
        self.__jsonname = json_array[0]

        is_file = os.path.isfile("data.csv")
        if not is_file:
            print("execute first read_data.py")
            sys.exit(1)
        self.__datadf = pd.read_csv("data.csv")

        self.__Ndate = len(self.__scheduleyaml["schedule"])
        self.__Nslot = len(self.__scheduleyaml["timeslots"])
        self.__Nwork = len(self.__scheduleyaml["shiftworks"])

        self.InitOutputArray()
        self.InitVariable()
        print("Initialization finished!")

    def InitOutputArray(self):
        schedule_yaml = self.__scheduleyaml["schedule"]
        name_rawindex = self.__sheetyaml["Input"]["sheets"][0]["shiftername"]

        # table1 : shift table based on name
        table1_Ncolumn = self.__Ndate + 2
        table1_Nindex = self.__Nwork * self.__Nslot + 2

        self.__table1_array = [
            ["" for _ in range(table1_Ncolumn)] for _ in range(table1_Nindex)
        ]
        for i in range(table1_Ncolumn - 2):
            self.__table1_array[0][i + 2] = schedule_yaml[i]["date"]
            self.__table1_array[1][i + 2] = schedule_yaml[i]["site"]

        for j in range(table1_Nindex - 2):
            index = j % self.__Nwork
            group = j // self.__Nwork
            if index == 0:
                self.__table1_array[j + 2][0] = self.__scheduleyaml["timeslots"][group]
                self.__table1_array[j + 2][1] = self.__scheduleyaml["shiftworks"][index]
            else:
                self.__table1_array[j + 2][1] = self.__scheduleyaml["shiftworks"][index]

        # table2 : shift table based on person
        table2_Ncolumn = self.__Ndate * self.__Nslot + 1
        table2_Nindex = len(self.__datadf) + 2
        self.__table2_array = [
            ["" for _ in range(table2_Ncolumn)] for _ in range(table2_Nindex)
        ]
        for i in range(table2_Ncolumn - 1):
            index = i % self.__Nslot
            group = i // self.__Nslot
            if index == 0:
                self.__table2_array[0][i + 1] = schedule_yaml[group]["date"]
                self.__table2_array[1][i + 1] = self.__scheduleyaml["timeslots"][index]
            else:
                self.__table2_array[1][i + 1] = self.__scheduleyaml["timeslots"][index]

        for j in range(table2_Nindex - 2):
            name_index = self.alphabet.index(name_rawindex)
            self.__table2_array[j + 2][0] = self.__datadf.iat[j, name_index]

    def InitVariable(self):
        schedule_yaml = self.__scheduleyaml["schedule"]
        name_rawindex = self.__sheetyaml["Input"]["sheets"][0]["shiftername"]
        name_index = self.alphabet.index(name_rawindex)

        attribute_index = self.__datadf.columns.get_loc("attribute")

        for i in range(len(self.__datadf)):
            self.__list_pa.append(
                (
                    self.__datadf.iat[i, name_index],
                    self.__datadf.iat[i, attribute_index],
                )
            )

        for i in range(self.__Ndate):
            for j in range(len(schedule_yaml[i]["contents"])):
                for k in range(len(schedule_yaml[i]["contents"][j]["work"])):
                    self.__list_dts.append(
                        (
                            schedule_yaml[i]["date"],
                            schedule_yaml[i]["contents"][j]["time"],
                            schedule_yaml[i]["contents"][j]["work"][k],
                        )
                    )

    # ====== main function========
    def SolveProblem(self):
        print("solving the problem...")

        ShiftScheduling = pulp.LpProblem("ShiftScheduling", pulp.LpMinimize)

        """
        valiable: x (__x)
        x[p, a, d, t, s] => the (p, a) person take (d, t, s) shift = 1, not take = 0
          p: person name
          a: person attribute (like new-person)
          d: day of the work
          t: time of the work
          s: shift name
        """
        self.__x = {}
        for p, a in self.__list_pa:
            for d, t, s in self.__list_dts:
                self.__x[p, a, d, t, s] = pulp.LpVariable(
                    "x({:},{:},{:},{:},{:})".format(p, a, d, t, s), 0, 1, pulp.LpInteger
                )

        # default object functiion
        obj_default = pulp.lpSum(self.__x)
        ShiftScheduling += obj_default

        # condition setting
        # need one shift for each table
        for d, t, s in self.__list_dts:
            ShiftScheduling += (
                pulp.lpSum(self.__x[p, a, d, t, s] for p, a in self.__list_pa) >= 1
            )

        # in one slot, double prohibition
        # + prohibit continuous shift
        isContinuousOkay = bool(self.__modelyaml["continuous_shift"])
        isFirst = True
        for p, a in self.__list_pa:
            for d, t, s in self.__list_dts:
                if isFirst:
                    d1 = d
                    t1 = t
                    slot_sum_before = 0
                    slot_sum = 0
                    isFirst = False

                if d == d1 and t == t1:
                    slot_sum += self.__x[p, a, d, t, s]
                else:
                    if not isContinuousOkay:
                        ShiftScheduling += slot_sum_before + slot_sum <= 1
                    slot_sum_before = slot_sum
                    ShiftScheduling += slot_sum <= 1
                    slot_sum = 0
                    d1 = d
                    t1 = t
                    slot_sum += self.__x[p, a, d, t, s]

            ShiftScheduling += slot_sum <= 1

        # considering NG schedule
        NG_list = self.GetNGList()
        for p, a, d, t, s in NG_list:
            ShiftScheduling += self.__x[p, a, d, t, s] == 0

        # "need" from model.yaml
        for i in range(len(self.__modelyaml["need"])):
            att_id = self.__modelyaml["need"][i]["attribute"]
            shift_name = self.__modelyaml["need"][i]["shift"]
            if att_id == None:
                continue
            for d, t, s in self.__list_dts:
                if s == shift_name:
                    need_sum = 0
                    for p, a in self.__list_pa:
                        if a == att_id:
                            need_sum += self.__x[p, a, d, t, s]
                    ShiftScheduling += need_sum >= 1

        # "avoid" from model.yaml
        for i in range(len(self.__modelyaml["avoid"])):
            att_id = self.__modelyaml["avoid"][i]["attribute"]
            shift_name = self.__modelyaml["avoid"][i]["shift"]
            if att_id == None:
                continue
            for d, t, s in self.__list_dts:
                if s == shift_name:
                    avoid_sum = 0
                    for p, a in self.__list_pa:
                        if a == att_id:
                            avoid_sum += self.__x[p, a, d, t, s]
                    ShiftScheduling += avoid_sum == 0

        # "avoidtime" from model.yaml
        for i in range(len(self.__modelyaml["avoidtime"])):
            att_id = self.__modelyaml["avoidtime"][i]["attribute"]
            day_name = self.__modelyaml["avoidtime"][i]["day"]
            time_name = self.__modelyaml["avoidtime"][i]["time"]
            if att_id == None:
                continue
            for d, t, s in self.__list_dts:
                if d == day_name and t == time_name:
                    avoidtime_sum = 0
                    for p, a in self.__list_pa:
                        if a == att_id:
                            avoidtime_sum += self.__x[p, a, d, t, s]
                    ShiftScheduling += avoidtime_sum == 0

        # solve
        try:
            results = ShiftScheduling.solve(pulp.PULP_CBC_CMD(msg=False))
            print()
            print(
                "optimality = {:}, target value = {:}".format(
                    pulp.LpStatus[results], pulp.value(ShiftScheduling.objective)
                )
            )
            print()
        except:
            print("NOT solved...")

    # ====== end =================

    def GetNGList(self):
        result_list = []

        name_rawindex = self.__sheetyaml["Input"]["sheets"][0]["shiftername"]
        name_index = self.alphabet.index(name_rawindex)

        attribute_index = self.__datadf.columns.get_loc("attribute")

        timeslot_rawindexarray = self.__sheetyaml["Input"]["sheets"][0]["timeslots"]
        timeslot_indexarray = []
        for i in range(len(timeslot_rawindexarray)):
            timeslot_indexarray.append(self.alphabet.index(timeslot_rawindexarray[i]))

        timeslots_array = self.__scheduleyaml["timeslots"]

        for _, data in self.__datadf.iterrows():
            for i in timeslot_indexarray:
                if type(data[i]) == float:
                    continue
                for day_str in [s.strip() for s in data[i].split(",")]:
                    for d, t, s in self.__list_dts:
                        if (
                            d == day_str
                            and t == timeslots_array[i - timeslot_indexarray[0]]
                        ):
                            result_list.append(
                                (data[name_index], data[attribute_index], d, t, s)
                            )

        return result_list

    def SetResult(self):
        print("setting the solved result...")

        for d, t, s in self.__list_dts:
            for p, a in self.__list_pa:
                if pulp.value(self.__x[p, a, d, t, s]) == 1:
                    # for table1
                    day_id = self.__table1_array[0].index(d)
                    time_id = [r[0] for r in self.__table1_array].index(t)
                    shift_id = [r[1] for r in self.__table1_array].index(s) - 2
                    self.__table1_array[time_id + shift_id][day_id] = p

                    # for table2
                    day_id2 = self.__table2_array[0].index(d)
                    time_id2 = self.__table2_array[1].index(t) - 1
                    person_id2 = [r[0] for r in self.__table2_array].index(p)
                    self.__table2_array[person_id2][day_id2 + time_id2] = s

        # set "x" for NG schedule for table2
        NG_list = self.GetNGList()
        for p, a, d, t, s in NG_list:
            day_id2 = self.__table2_array[0].index(d)
            time_id2 = self.__table2_array[1].index(t) - 1
            person_id2 = [r[0] for r in self.__table2_array].index(p)
            self.__table2_array[person_id2][day_id2 + time_id2] = "x"

    def SendOutputSpreadSheet(self):
        print("start sending data...")
        spread_name = self.__sheetyaml["Output"]["name"]
        sheetsyaml = self.__sheetyaml["Output"]["sheets"]
        if len(sheetsyaml) != 2:
            print("Set two Output sheets in sheet_structure.yaml")
            sys.exit(1)

        try:
            print("trying to connect " + spread_name + "...")
            gc = gspread.service_account(filename=self.__jsonname)
            sh = gc.open(spread_name)
            print("connect to spreadsheet: " + spread_name)

            ws1 = sh.worksheet(sheetsyaml[0]["name"])
            ws1.clear()
            set_with_dataframe(
                ws1, pd.DataFrame(self.__table1_array), include_column_header=False
            )
            print("connect to sheet: " + sheetsyaml[0]["name"])

            ws2 = sh.worksheet(sheetsyaml[1]["name"])
            ws2.clear()
            set_with_dataframe(
                ws2, pd.DataFrame(self.__table2_array).T, include_column_header=False
            )
            print("connect to sheet: " + sheetsyaml[1]["name"])

        except:
            print("ERROR: cannot connect to google spread sheet")
            sys.exit(1)


if __name__ == "__main__":
    scheduling = Scheduling()
    scheduling.SolveProblem()
    scheduling.SetResult()
    scheduling.SendOutputSpreadSheet()
    print("finish!")
