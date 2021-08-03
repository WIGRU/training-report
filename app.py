import csv
from tabulate import tabulate
from datetime import datetime, timedelta
import pdfkit
import configparser
import os
import glob

config = configparser.ConfigParser()
config.read('settings.ini', encoding="utf-8")

types = config['DEFAULT']['activity_types'].split(",")
print(types)
time_format = '%Y-%m-%d'

start_date = datetime.strptime(config['DEFAULT']["start_date"], time_format)
end_date = datetime.strptime(config['DEFAULT']["end_date"], time_format)

activities = [] #dictlist with all activities
all_activities = []

dist_sum = float()
time_sum = timedelta()

print("reading file...")
with open(config['DEFAULT']["in_file"], newline='', encoding='utf-8') as csvfile:
    rows = csv.reader(csvfile, delimiter=',', quotechar='"')
    
    for row in rows:
        if row[0] in types or row[0] == "Aktivitetstyp":
            date = datetime.strptime("2000-01-01", time_format)
            header = False
            if row[1] == "Datum":
                header = True
            else:
                date_str = row[1].split(" ")[0]
                date = datetime.strptime(date_str, '%Y-%m-%d')
            if start_date <= date <= end_date or header:
                activities.append({'aktivitetstyp': row[0], 'datum': row[1].split(" ")[0], 'namn': row[3], 'sträcka': row[4], 'tid': row[6], 'medelpuls': row[7], 'medeltempo': row[12], 'stigning': row[14]})    
                if not row[0] == "Aktivitetstyp":
                    dist_sum += float(row[4].replace(",","."))
                    t = datetime.strptime(row[6], "%H:%M:%S")
                    time_sum += timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
            all_activities.append({'aktivitetstyp': row[0], 'datum': row[1].split(" ")[0], 'namn': row[3], 'sträcka': row[4], 'tid': row[6], 'medelpuls': row[7], 'medeltempo': row[12], 'stigning': row[14]})
                    
print("creating html...")
activities.reverse()
activities.insert(0, activities[-1])
activities.pop(-1)

sum = []
sum.append({'key': 'Månad', 'dist': 'Distans', 'time': 'Tid', 'count': 'Antal'})
#Monthly sum
if config['DEFAULT']['summarize_months'] == 'True':
    months = set()
    for activity in all_activities:
        if activity["datum"] != "Datum":
            print(activity["datum"])
            m = datetime.strptime(activity["datum"], time_format)
            m_str = f"{m.year}-{m.month}"

            dist = float(activity['sträcka'].replace(",","."))
            t = datetime.strptime(activity["tid"], "%H:%M:%S")
            hours = round(t.hour + t.minute / 60 + t.second / 3600, 2)
            
            exists = False
            for v in sum:
                if m_str in v.values():
                    exists = True
                    new_dist = v['dist'] + dist
                    new_time = v['time'] + hours
                    count = v['count'] + 1
                    sum[sum.index(v)]['dist'] = new_dist
                    sum[sum.index(v)]['time'] = new_time
                    sum[sum.index(v)]['count'] = count

            if not exists:
                sum.append({'key': m_str, 'dist': dist, 'time': hours, 'count': 0})


ym = str(start_date.year) + "-" + str(start_date.month)
with open(f'{ config["DEFAULT"]["tmp_folder"] }activities.html', 'w', encoding="utf-8") as file:
    file.write("""
                <!DOCTYPE html>
                <html>
                <head>
                <meta charset="UTF-8">
                <style>
                table {
                    border-collapse: collapse;
                    width: auto;
                }

                th, td {
                    text-align: left;
                    padding: 8px;
                }

                tr:nth-child(even){background-color: #f2f2f2}

                th {
                    background-color: #3399ff;
                    color: white;
                }
                </style>
                </head>
                <body>
            """)
    file.write(f"<h1>Träningsdagbok, {ym}</h1>")
    name = config["DEFAULT"]["user_name"]
    file.write(f"<b>{ name }</b>")
    file.write("<h2>Aktiviteter</h2>")
    file.write(tabulate(activities, headers="firstrow", tablefmt="html"))
    file.write("<h2>Summering</h2>")
    file.write(tabulate(sum, headers="firstrow", tablefmt="html"))
    file.write("""
                </body>
                </html>
                """)


print("converting to pdf...")

pdfkit.from_file(f'{config["DEFAULT"]["tmp_folder"]}activities.html', f'{ config["DEFAULT"]["out_path"]}activities_{ ym }.pdf')