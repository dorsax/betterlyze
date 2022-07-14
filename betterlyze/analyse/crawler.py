from math import floor
import requests
from django.db.models import Count, Sum

from .models import Event, Donation

# get the config

def crawl(event_id,max_pages_per_cycle=5000, per_page = 100):
    
    
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist as exc:
        raise exc
    
    uri = f'https://api.betterplace.org/de/api_v4/fundraising_events/{event.id}/opinions.json'
    uri_overview = f'https://api.betterplace.org/de/api_v4/fundraising_events/{event.id}.json'
    page = 50000000 # ensures no data at all and gets the key param to be loaded: total_pages !

    def build_uri ():
        return uri+f'?order=created_at:ASC&per_page={per_page}&page={page}'


    def fetch () :
        return requests.get(build_uri()).json()

    breakpoint()
    # find last id somehow
    try:
        lastdonation = Donation.objects.filter(event=event.id).order_by('-id')[0]
        currentpage = lastdonation.page
        last_id = lastdonation.id
    except IndexError as exc:
        currentpage = 1
        last_id = -1
    
    jresponse = fetch()

    # do a maximum of x pages per cycle, but don't try to get more pages than available (results in NULL data)
    maxpages_fetched = jresponse['total_pages']
    maxpages = currentpage + max_pages_per_cycle  
    if maxpages > maxpages_fetched:
        maxpages = maxpages_fetched

    # if no cache exists, do not check cached entries
    skip = (last_id!=-1)
    breakpoint()
    # call all newly available pages
    for index in range(currentpage,maxpages+1):
        page = index
        response = fetch()
        response = response['data']  # get the data from the page set above
        if len(response) >= 0:
            for index2 in range (len(response)): # go through response
                if (not(skip)): # if this entry should be skipped due to caching
                    setwaszero=0
                    if response[index2].get('donated_amount_in_cents',0)==0:
                        setwaszero=1
                    Donation.objects.create (id=response[index2].get('id',-1),event_id=event.id,donated_amount_in_cents=response[index2].get('donated_amount_in_cents',0),page=page,donated_at=response[index2].get('created_at',0), was_zero=setwaszero)
                    
                    last_id = response[len(response)-1].get('id',0) # set the latest id to the cache to avoid wrong caches
                    
                if (skip & (last_id == response[index2].get("id"))): # latest index reached. checked after calculation to avoid double calcs
                    skip = False


    # Count all donations which are anonymized
    anonymous_count = Donation.objects.filter(event=event.id,was_zero=1).aggregate(Count('id'))['id__count']
    if anonymous_count>0: 
        
        # Sum of all donations excluding was_zero
        non_anonymous_amount = Donation.objects.filter(event=event.id,was_zero=0).aggregate(Sum('donated_amount_in_cents'))['donated_amount_in_cents__sum']

        uri = uri_overview
        endamount = fetch().get('donated_amount_in_cents')

        # get the amount per donation
        anonymous_amount =(endamount-non_anonymous_amount)/anonymous_count
        anonymous_amount = floor(anonymous_amount)
        anonymous_amount_of_last_entry = (endamount-non_anonymous_amount)-(anonymous_count-1)*anonymous_amount
        # bulk update the donations
        Donation.objects.filter(event=event.id,was_zero=1).update(donated_amount_in_cents=anonymous_amount)
        last_entry = Donation.objects.filter(event=event.id,was_zero=1).order_by('-id')[0]
        last_entry.donated_amount_in_cents=anonymous_amount_of_last_entry
        last_entry.save()

