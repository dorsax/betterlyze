# this script will crawl all new data
import yaml
import os
import requests
import json 
from datetime import datetime as dt


config_filename = 'config.yml'
cache_filename = 'cache.json'
# get the config


configstream = open(os.path.dirname(os.path.realpath(__file__))+os.path.sep+config_filename, 'r')
config = yaml.safe_load (configstream)
event = config.get('event')
per_page = config.get('per_page')
try:
    with open(cache_filename, 'r') as jsonFile:
        cache = json.load(jsonFile)
        jsonFile.close()
except:
    cache = {}
currentpage = cache.get ('last_page',0)
donors = cache.get ('user_count',0)
last_id = cache.get ('last_id',-1)
amount = cache.get ('amount',0) # get from cache: where has the last iteration stopped? As in which page.

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

# if no cache exists, do not check cached entries
if (last_id==-1):
    skip=False
else:
    skip=True

cachetime = dt.now()
# call all newly available pages
for index in range(currentpage,maxpages+1):
    page = index
    response = fetch()['data'] # get the data from the page set above
    for index2 in range (len(response)): # go through response
        if (not(skip)): # if this entry should be skipped due to caching
            last_id = response[len(response)-1].get('id',0) # set the latest id to the cache to avoid wrong caches
            donated_amount = response[index2].get('donated_amount_in_cents',0)
            if (donated_amount): # only count non-zero-amounts. those might have been deleted or anonymous
                amount += donated_amount
                donors += 1
            
        if (skip & (last_id == response[index2].get("id"))): # latest index reached. checked after calculation to avoid double calcs
            skip = False
    currentpage = page # set the latest page for caching
print ((dt.now()-cachetime).seconds)
# print (str(donors) + " donors donated "+ str(amount))
# uri = 'https://api.betterplace.org/de/api_v4/fundraising_events/'+str(event)+'.json'
# parameters = ''
# response = fetch()
# donors = response.get('donations_count')
# amount = response.get('donated_amount_in_cents')
# print (str(donors) + " donors donated "+ str(amount))

# write all data into the cache

cache['last_page']=currentpage
cache['user_count']=donors
cache['last_id']=last_id
cache['amount']=amount
with open(cache_filename, 'w') as jsonFile:
    json.dump(cache, jsonFile)
    jsonFile.close()