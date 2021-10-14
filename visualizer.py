import pandas as pd
import setup
import yaml
import os
import datetime
import pytz
from datetime import datetime as dt
import matplotlib.pyplot as plt


utc=pytz.UTC

# get the config
config_filename = 'config.yml'
configstream = open(os.path.dirname(os.path.realpath(__file__))+os.path.sep+config_filename, 'r')
config = yaml.safe_load (configstream)
address = config["database"].get('address')
username = config["database"].get('username')
password = config["database"].get('password')
database = config["database"].get('database')
startdate= dt.fromisoformat(config.get('starttime'))
enddate= dt.fromisoformat(config.get('endtime'))
# this will visualize the data previously fetched.

# define the SELECT statements for the graphs

# compute results and maybe write statistical tables to db

# build the forms and graphs
def create_connection ():
    return setup.create_connection(username=username,password=password,address=address,database=database)
# Read sqlite query results into a pandas DataFrame
connection = create_connection ()
dataframe = pd.read_sql_query("SELECT * from donations", connection)


# convert timestamps to datetime
dataframe['donated_at_datetime'] = dataframe.donated_at
# convert amount to euro
# dataframe['donated_amount_in_cents'] = pd.to_numeric(dataframe.donated_amount_in_cents) 
dataframe['donated_amount_in_Euro'] = dataframe.donated_amount_in_cents.div(100).round(2)
# cumulate 
dataframe['cumulated_sum'] = dataframe.donated_amount_in_Euro.cumsum(axis = 0, skipna = True)
# startdate=0
# enddate = 0
maxval = 0
# startdate = pd.to_datetime('2020-11-14T12:00:00+01:00', format='%Y-%m-%dT%H:%M:%S%z')-datetime.timedelta(hours=9, minutes=30)

enddate_from_data = dataframe['donated_at_datetime'].max().to_pydatetime()
enddate_from_data = utc.localize(enddate_from_data)
if enddate_from_data < enddate:
    enddate = enddate_from_data
maxval = dataframe['cumulated_sum'].max() # + 10000
print (f'from {startdate} - {enddate} with max. {maxval}')
print(dataframe.head())

# dataframe.to_sql("converted",connection,if_exists="replace")
connection.close()
#Visualize the donated money
#plt.figure(figsize=(64,16))
# #plt.figure(figsize=(320,80))
# plt.title('donated money')
# plt.bar(dataframe['donated_at_datetime'],dataframe['cumulated_sum'])
# # plt.plot(dataframe['donated_at_datetime'],dataframe['cumulated_sum'], linewidth=2.0)
# # ham = plt.axis([startdate, enddate, 0, maxval])
# #print (ham)
# plt.xlim (1,2)
# plt.xlabel('Datetime', fontsize=18)
# plt.ylabel('Euro', fontsize=18)
# plt.autoscale(True)
# plt.grid(True)

#dataframe2 = pd.DataFrame(dataframe,index=dataframe.donated_at_datetime)
hlim = dataframe.plot(x="donated_at_datetime",y="cumulated_sum",xlim=(startdate,enddate),ylim=(0,100000))


plt.show()