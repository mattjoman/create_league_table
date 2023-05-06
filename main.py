import numpy as np
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class Client:
    def __init__(self, keyfile, scopes, workbook_name):
        creds = ServiceAccountCredentials.from_json_keyfile_name("secretkey.json", scopes=scopes)
        self.client = gspread.authorize(creds)
        self.workbook = self.client.open(workbook_name)
        return

    def worksheet(self, name):
        return self.workbook.worksheet(name)

    def worksheets(self):
        return self.workbook.worksheets()

    def worksheet_get_all_values(self, name):
        return self.workbook.worksheet(name).get_all_values()

    def worksheet_clear(self, name):
        #self.workbook.worksheet(name).clear()
        self.workbook.worksheet(name).batch_clear(["A1:G100"])
        return

    def worksheet_update(self, name, df):
        self.workbook.worksheet(name).update([df.columns.values.tolist()] + df.values.tolist())
        return


def generate_team_game_lines(df):

    lines = {
        "Game ID": [],
        "Team": [],
        "Win": [],
        "Loss": [],
        "Draw": [],
        "Points": [],
        "Scored": [],
        "Conceded": [],
        "GD": []
    }

    for game_num, df_row in enumerate(df.iterrows()):
        row = df_row[1]

        home_team = row["Home Team"]
        away_team = row["Away Team"]
        home_scored = row["Home Team Goals"]
        away_scored = row["Away Team Goals"]
        home_gd = home_scored - away_scored
        away_gd = away_scored - home_scored

        # draw
        home_win = 0
        home_loss = 0
        home_draw = 1
        home_pts = 1
        away_win = 0
        away_loss = 0
        away_draw = 1
        away_pts = 1

        # home team win
        if home_scored > away_scored:
            home_win = 1
            home_loss = 0
            home_draw = 0
            home_pts = 3
            away_win = 0
            away_loss = 1
            away_draw = 0
            away_pts = 0

        # away team win
        elif away_scored > home_scored:
            home_win = 1
            home_loss = 0
            home_draw = 0
            home_pts = 3
            away_win = 0
            away_loss = 1
            away_draw = 0
            away_pts = 0

        lines["Game ID"].append(game_num)
        lines["Team"].append(home_team)
        lines["Win"].append(home_win)
        lines["Loss"].append(home_loss)
        lines["Draw"].append(home_draw)
        lines["Points"].append(home_pts)
        lines["Scored"].append(home_scored)
        lines["Conceded"].append(away_scored)
        lines["GD"].append(home_gd)

        lines["Game ID"].append(game_num)
        lines["Team"].append(away_team)
        lines["Win"].append(away_win)
        lines["Loss"].append(away_loss)
        lines["Draw"].append(away_draw)
        lines["Points"].append(away_pts)
        lines["Scored"].append(away_scored)
        lines["Conceded"].append(home_scored)
        lines["GD"].append(away_gd)

    return pd.DataFrame.from_dict(lines)


def main():
    keyfile = "../data/secretkey.json"
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    workbook_name = "test1"

    client = Client(keyfile, scopes, workbook_name)

    raw = client.worksheet_get_all_values("Sheet2")
    cols = raw[0]
    data = raw[1:]

    df = pd.DataFrame(data)
    df.columns = cols

    df["Home Team Goals"] = pd.to_numeric(df["Result"].str.split("-").str[0])
    df["Away Team Goals"] = pd.to_numeric(df["Result"].str.split("-").str[1])

    df = generate_team_game_lines(df)
    print(df)

    ## Aggregations
    pt = pd.pivot_table(df, values = ["Win", "Loss", "Draw", "GD", "Points"], index = "Team", aggfunc=np.sum, sort=False)
    pt.reset_index(level=0, inplace=True)

    pt["numberOfMatchPlayed"] = pt["Win"] + pt["Loss"] + pt["Draw"]
    pt = pt[["Team", "numberOfMatchPlayed", "Win", "Loss", "Draw", "GD", "Points"]]
    pt = pt.sort_values(by="Points", ascending=False)
    print(pt)

    # update google sheets with the aggregated data
    client.worksheet_clear("Sheet1")
    client.worksheet_update("Sheet1", pt)

    return


if __name__ == "__main__":
    main()
