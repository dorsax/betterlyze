# this script will crawl all new data
import yaml
import os
import requests
import json 
import setup
import argparse
from datetime import datetime as dt

parser = argparse.ArgumentParser()

parser.add_argument('--old', action='store_true')
args = parser.parse_args()

config_filename = 'config.yml'
cache_filename = 'cache.json'
# get the config

def crawl(year,per_cycle=None):
    configstream = open(os.path.dirname(os.path.realpath(__file__))+os.path.sep+config_filename, 'r')
    config = yaml.safe_load (configstream)
    event = config[year].get('event')
    per_page = config.get('per_page')
    address = config["database"].get('address')
    username = config["database"].get('username')
    password = config["database"].get('password')
    database = config["database"].get('database')

    if (per_cycle is None):
        max_pages_per_cycle = config.get('max_pages_per_cycle')
    else:
        max_pages_per_cycle = per_cycle


    uri = 'https://api.betterplace.org/de/api_v4/fundraising_events/'+str(event)+'/opinions.json'
    parameters = '?order=created_at:ASC&per_page=%%per_page%%&page=%%page%%'
    page = 50000000 # ensures no data at all and gets the key param to be loaded: total_pages !

    def build_uri ():
        return uri+parameters.replace('%%per_page%%',str(per_page)).replace('%%page%%',str(page))


    def fetch () :
        return requests.get(build_uri()).json()

    def create_connection ():
        return setup.create_connection(username=username,password=password,address=address,database=database)

    currentpage = 1
    last_id = -1
    # new cache from db:
    connection = create_connection()
    if connection is not None:
        cursor = connection.cursor()
        cursor.execute("SELECT id,page FROM donations WHERE event_id=%s ORDER BY donated_at DESC;",(event,))
        
        #rows = cursor.fetchall()
        last_run = cursor.fetchone()
        if type(last_run) == tuple:
            currentpage = int(last_run[1])
            last_id = int(last_run[0])
            print (f'page is {currentpage} and last was {last_id}')


    jresponse = fetch()

    # do a maximum of x pages per cycle, but don't try to get more pages than available (results in NULL data)
    maxpages_fetched = jresponse['total_pages']
    maxpages = currentpage + max_pages_per_cycle  
    if maxpages > maxpages_fetched:
        maxpages = maxpages_fetched

    # if no cache exists, do not check cached entries
    if (last_id==-1):
        skip=False
    else:
        skip=True

    # call all newly available pages
    for index in range(currentpage,maxpages+1):
        page = index
        response = fetch()
        response = response['data']  # get the data from the page set above
        if len(response) >= 0:
            connection = create_connection()
            if connection is not None:
                cursor = connection.cursor()
                for index2 in range (len(response)): # go through response
                    if (not(skip)): # if this entry should be skipped due to caching
                        cursor.execute("INSERT INTO donations (donated_at,id,donated_amount_in_cents,page,event_id) VALUES (%s,%s,%s,%s,%s)", (response[index2].get('created_at',0), response[index2].get('id',-1),response[index2].get('donated_amount_in_cents',0),page,event))
                        last_id = response[len(response)-1].get('id',0) # set the latest id to the cache to avoid wrong caches
                        
                    if (skip & (last_id == response[index2].get("id"))): # latest index reached. checked after calculation to avoid double calcs
                        skip = False
                currentpage = page # set the latest page for caching
                connection.commit()
                connection.close()

    connection = create_connection()
    if connection is not None:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO last_run (created_at,id,last_page,event_id) VALUES (%s,%s,%s,%s)", (dt.now() ,last_id,currentpage,event,))
        connection.commit()
        connection.close()

if __name__ == '__main__':
    if args.old :
        crawl("past_year",1000)
    else:
        crawl("current_year")
