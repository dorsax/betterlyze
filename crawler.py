# this script will crawl all new data
import yaml
import os
import requests
import json 

config_filename = 'config.yml'
# get the config

configstream = open(os.path.dirname(os.path.realpath(__file__))+os.path.sep+config_filename, 'r')
config = yaml.safe_load (configstream)
event = config.get('event')
per_page = config.get('per_page')

uri = 'https://api.betterplace.org/de/api_v4/fundraising_events/'+str(event)+'/opinions.json'
parameters = '?order=created_at:ASC&per_page=%%per_page%%&page=%%page%%'
page = 50000000 # ensures no data at all and gets the key param to be loaded: total_pages !

def build_uri ():
    return uri+parameters.replace('%%per_page%%',str(per_page)).replace('%%page%%',str(page))

def fetch () :
    return requests.get(build_uri()).json()

jresponse = requests.get(build_uri()).json()


# get current max pages
maxpages = jresponse['total_pages']
currentpage=0
amount = 0
donors = 0
for index in range(currentpage,maxpages+1):
    page = index
    response = fetch()['data']
    for index2 in range (len(response)):
        donated_amount = response[index2].get('donated_amount_in_cents',0)
        if (donated_amount):
            amount += donated_amount
            donors += 1
            
        
print (str(donors) + " donors donated "+ str(amount))
uri = 'https://api.betterplace.org/de/api_v4/fundraising_events/'+str(event)+'.json'
parameters = ''
response = fetch()
donors = response.get('donations_count')
amount = response.get('donated_amount_in_cents')
print (str(donors) + " donors donated "+ str(amount))


# get from database: where has the last iteration stopped? As in which page. 

# get the same page again

# if there are more pages, get the pages, too.

# write all data into the database

# data contains: all fetched, last page
