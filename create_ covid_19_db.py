import pandas as pd
import sqlite3

daily_report = pd.read_csv("data/03-09-2023.csv")
confirmed = pd.read_csv("data/time_series_covid19_confirmed_global.csv")
deaths = pd.read_csv("data/time_series_covid19_deaths_global.csv")
vaccine = pd.read_csv("data/time_series_covid19_vaccine_global.csv")

# print(daily_report.head())
# print(confirmed.head())
# print(deaths.head())
# print(vaccine.head())


# 調整 confirmed 與 deaths 的格式
# 使用 pd.melt() 由寬格式調整為長格式。
# id_vars: Province/State, Country/Region, Lat, Long
# value_vars: 除了 id_vars 以外的變數。
# var_name: Date
# value_name: Confirmed, Deaths
id_variables = ["Province/State", "Country/Region", "Lat", "Long"]
melted_confirmed = pd.melt(confirmed, id_vars=id_variables, var_name="Date", value_name="Confirmed")
melted_deaths = pd.melt(deaths, id_vars=id_variables, var_name="Date", value_name="Deaths")
# print(melted_confirmed.head())
# print(melted_deaths.head())

# 調整 melted_confirmed 與 melted_deaths 的日期變數
# 使用 pd.to_datetime() 函數。
# format="%m/%d/%y"
melted_confirmed["Date"] = pd.to_datetime(melted_confirmed["Date"], format="%m/%d/%y")
melted_deaths["Date"] = pd.to_datetime(melted_deaths["Date"], format="%m/%d/%y")
# print(melted_confirmed.head())
# print(melted_deaths.head())

# 調整 vaccine 數個欄位
# Province_State: 資料類型調整。
# Date: 資料類型調整。
# 重新命名 Province_State 與 Country_Region
vaccine["Province_State"] = vaccine["Province_State"].astype(object)
vaccine["Date"] = pd.to_datetime(vaccine["Date"])
vaccine = vaccine.rename(columns={"Province_State": "Province/State", "Country_Region": "Country/Region"})
# print(vaccine.head())

# 選擇需要用到的欄位
daily_report = daily_report[["Country_Region", "Province_State", "Admin2", "Confirmed", "Deaths", "Lat", "Long_"]]
melted_confirmed = melted_confirmed.drop(labels=["Lat", "Long"], axis=1)
melted_deaths = melted_deaths.drop(labels=["Lat", "Long"], axis=1)
vaccine = vaccine.drop(labels=["UID", "People_at_least_one_dose"], axis=1)

# 調整 daily_report 欄位名稱
daily_report.columns = ["country", "province", "county", "confirmed", "deaths", "latitude", "longitude"]
# print(daily_report.head())

# 連接資料框
join_keys = ["Province/State", "Country/Region", "Date"]
time_series = pd.merge(melted_confirmed, melted_deaths, left_on=join_keys, right_on=join_keys, how="left")
time_series = pd.merge(time_series, vaccine, left_on=join_keys, right_on=join_keys, how="left")
time_series = time_series.drop(labels="Province/State", axis=1)
#分組聚合，加總
time_series = time_series.groupby(["Country/Region", "Date"])[["Confirmed", "Deaths", "Doses_admin"]].sum().reset_index()
# print(time_series)

#調整 time_series 欄位名稱與資料型別
time_series.columns = ["country", "reported_on", "confirmed", "deaths", "doses_administered"]
time_series["doses_administered"] = time_series["doses_administered"].astype(int)
# print(time_series)

# 整理程式碼為一個類別 CreateCovid19DB
class CreateCovid19DB:
    def create_time_series(self):
        confirmed = pd.read_csv("data/time_series_covid19_confirmed_global.csv")
        deaths = pd.read_csv("data/time_series_covid19_deaths_global.csv")
        vaccine = pd.read_csv("data/time_series_covid19_vaccine_global.csv")
        id_variables = ["Province/State", "Country/Region", "Lat", "Long"]
        melted_confirmed = pd.melt(confirmed, id_vars=id_variables, var_name="Date", value_name="Confirmed")
        melted_deaths = pd.melt(deaths, id_vars=id_variables, var_name="Date", value_name="Deaths")
        melted_confirmed["Date"] = pd.to_datetime(melted_confirmed["Date"], format="%m/%d/%y")
        melted_deaths["Date"] = pd.to_datetime(melted_deaths["Date"], format="%m/%d/%y")
        vaccine["Province_State"] = vaccine["Province_State"].astype(object)
        vaccine["Date"] = pd.to_datetime(vaccine["Date"])
        vaccine = vaccine.rename(columns={"Province_State": "Province/State", "Country_Region": "Country/Region"})
        join_keys = ["Province/State", "Country/Region", "Date"]
        time_series = pd.merge(melted_confirmed, melted_deaths, left_on=join_keys, right_on=join_keys, how="left")
        time_series = pd.merge(time_series, vaccine, left_on=join_keys, right_on=join_keys, how="left")
        time_series = time_series.drop(labels="Province/State", axis=1)
        time_series = time_series.groupby(["Country/Region", "Date"])[["Confirmed", "Deaths", "Doses_admin"]].sum().reset_index()
        time_series.columns = ["country", "reported_on", "confirmed", "deaths", "doses_administered"]
        time_series["doses_administered"] = time_series["doses_administered"].astype(int)
        return time_series
    def create_daily_report(self):
        daily_report = pd.read_csv("data/03-09-2023.csv")
        daily_report = daily_report[["Country_Region", "Province_State", "Admin2", "Confirmed", "Deaths", "Lat", "Long_"]]
        daily_report.columns = ["country", "province", "county", "confirmed", "deaths", "latitude", "longitude"]
        return daily_report
    def create_database(self):
        time_series = self.create_time_series()
        #保留到日期就好，不需要時間
        time_series["reported_on"] = time_series["reported_on"].map(lambda x: x.strftime("%Y-%m-%d"))
        daily_report = self.create_daily_report()
        connection = sqlite3.connect("data/covid_19.db")
        time_series.to_sql("time_series", con=connection, if_exists="replace", index=False)
        daily_report.to_sql("daily_report", con=connection, if_exists="replace", index=False)
        connection.close()

create_covid_19_db = CreateCovid19DB()
create_covid_19_db.create_database()