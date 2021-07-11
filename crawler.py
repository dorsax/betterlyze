# this script will crawl all new data
import yaml
import os

# get the config

configstream = open(os.path.dirname(os.path.realpath(__file__))+os.path.sep+config_filename, 'r')
config = yaml.safe_load (configstream)
event = config.get('event')
currentpage = config.get('lastpage',0)

# get from database: where has the last iteration stopped? As in which page. 

# get the same page again

# get current max entries and calculate the max pages

# if there are more pages, get the pages, too.

# write all data into the database

# data contains: all fetched, last page
