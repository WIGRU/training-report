import csv
import os
import configparser
from datetime import datetime
from tabulate import tabulate
import pdfkit


#
# Functions
#

# Build html file
def create_html(fout, data):
    with open(fout, 'w', encoding="utf-8") as file: # open file
        
        # html "start"
        file.write("""<!DOCTYPE html>
            <html>
                <head>
                    <meta charset="UTF-8">
                </head>
                <body>\n""")
        
        # content
        file.write(data)
        
        # end
        file.write("""</body>
                    </html>""")

# Validate csv file
def validate_csv(in_file):
    dt_format = '%Y-%m-%d %H:%M:%S' # (activty start)
    t_format = '%H:%M:%S' # (activity length)

    def validate_dt(date_text, format):
        try:
            datetime.strptime(date_text, format)
            return True
        except ValueError:
            raise ValueError("Incorrect data format")

    def validate_float(fl):
        try:
            if fl == '--': # no value
                pass
            else:
                float(fl.replace(',','.'))
            return True
        except ValueError:
            raise ValueError("Incorrect float value")
    
    def validate_int(i):
        try:
            if i == '--': # no value
                pass
            else:
                float(i)
            return True
        except ValueError:
            raise ValueError("Incorrect int value")


    with open(in_file, "r", encoding="utf-8") as csvfile: # open file
        rows = csv.reader(csvfile, delimiter=',', quotechar='"') # parse csv

        for row in rows:
            #print(f'{rows.line_num}') # for debug
            if row[0] == "Aktivitetstyp": # header
                if len(row) != 40: 
                    raise IndexError("Not enough columns")
                
            else:
                row[0].isalpha()
                validate_dt(row[1], dt_format)
                if row[2] != 'false' and row[2] != 'true':
                    raise ValueError("Incorrect data value")
                validate_float(row[4])
                validate_int(row[5])
                validate_dt(row[6].split(',')[0], t_format)
                validate_int(row[7])
                validate_int(row[8])
                validate_float(row[9])
                validate_int(row[10])
                validate_int(row[11])


#
# Settings
#

# Open config
config = configparser.ConfigParser()
config.read('settings.ini', encoding="utf-8")

types = config['DEFAULT']['activity_types'].split(",")
name = config["DEFAULT"]["user_name"]

# Date/Time
time_format = '%Y-%m-%d'
start_date = datetime.strptime(config['DEFAULT']["start_date"], time_format)
end_date = datetime.strptime(config['DEFAULT']["end_date"], time_format)

# Booleans
sum_months = (config['DEFAULT']['summarize_months'] == 'True')
activities_ls = (config['DEFAULT']['activities'] == 'True')

# Files
in_file = config['DEFAULT']["in_file"]
tmp_file_activities = f'{config["DEFAULT"]["tmp_folder"]}activities.html'
tmp_file_months = f'{config["DEFAULT"]["tmp_folder"]}months.html'
file_out_activities = f'{config["DEFAULT"]["out_path"]}activities.pdf'
file_out_months = f'{config["DEFAULT"]["out_path"]}months.pdf'

#
# Variables
#

activities = [] # dictlist with activities
all_activities = [] # dictlist with all activities
monthsum = [] # totals each month

#
# Main code
#

print("validating file")
validate_csv(in_file)

print("reading file...")
with open(in_file, newline='', encoding='utf-8') as csvfile: # open file
    rows = csv.reader(csvfile, delimiter=',', quotechar='"') # read csv
    
    for row in rows: # go through file
        if row[0] in types or row[0] == "Aktivitetstyp": # only add decided activty types to list or header
            date = datetime(1, 1, 1)

            header = row[0] == "Aktivitetstyp"

            if not header:
                date_str = row[1].split(" ")[0] # YYYY-MM-DD HH:MM:SS to YYYY-MM-DD
                date = datetime.strptime(date_str, '%Y-%m-%d') # str to date

            if activities_ls:
                if start_date <= date <= end_date or header: # only add activties between set date, for activity list
                    activities.append({'aktivitetstyp': row[0], 'datum': row[1].split(" ")[0], 'namn': row[3], 'sträcka': row[4], 'tid': row[6], 'medelpuls': row[7], 'medeltempo': row[12], 'stigning': row[14]})    
                
            if sum_months:
                all_activities.append({'aktivitetstyp': row[0], 'datum': row[1].split(" ")[0], 'namn': row[3], 'sträcka': row[4], 'tid': row[6], 'medelpuls': row[7], 'medeltempo': row[12], 'stigning': row[14]})
                

#Monthly sum
if sum_months:
    monthsum = []
    monthsum.append({'key': 'Månad', 'dist': 'Distans', 'time': 'Tid', 'count': 'Antal'})

    for activity in all_activities:
        if activity["datum"] != "Datum": #if not header

            # Get activity date
            d = activity["datum"].split('-')
            m_str = f'{d[0]}-{d[1]}'

            dist = float(activity['sträcka'].replace(",",".")) # distance
            t = datetime.strptime(activity["tid"].split(",")[0], "%H:%M:%S") # time
            hours = round(t.hour + t.minute / 60 + t.second / 3600, 2) #hours
            
            exists = False
            for v in monthsum: # search for month
                if m_str in v.values(): # if exists add to values
                    exists = True
                    new_dist = v['dist'] + dist
                    new_time = v['time'] + hours
                    count = v['count'] + 1

                    # Change data in dictlist
                    monthsum[monthsum.index(v)]['dist'] = new_dist
                    monthsum[monthsum.index(v)]['time'] = new_time
                    monthsum[monthsum.index(v)]['count'] = count

            if not exists: # create month sum
                monthsum.append({'key': m_str, 'dist': dist, 'time': hours, 'count': 0})


print("creating html...")

# create list with activities
if activities_ls:
    activities.reverse() # Revert list, earliest date first
    activities.insert(0, activities[-1]) # Add last row (header) to first
    activities.pop(-1) # Remove last row

    ym = str(start_date.year) + "-" + str(start_date.month)

    data = f"<h1>Träningsdagbok, {ym}</h1>\n"
    data += f"<b>{ name }</b>\n"
    data += "<h2>Aktiviteter</h2>\n"
    data += tabulate(activities, headers="firstrow", tablefmt="html")

    create_html(tmp_file_activities, data)

# create table with monthy sum
if sum_months:
    data = "<h2>Summering</h2>\n"
    data += tabulate(monthsum, headers="firstrow", tablefmt="html")

    create_html(tmp_file_months, data)


print("converting to pdf...")

if activities_ls: # activities
    pdfkit.from_file(tmp_file_activities, file_out_activities, css="style.css")

if sum_months: # months
    pdfkit.from_file(tmp_file_months, file_out_months, css="style.css")