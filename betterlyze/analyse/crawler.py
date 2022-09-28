from math import floor
import requests
from django.db.models import Count, Sum

from .models import Event, Donation

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

    # find last id somehow
    try:
        donation_count = Donation.objects.filter(event=event.id).aggregate(Count('id'))['id__count']
        currentpage = floor (donation_count/per_page)
        if (donation_count%per_page==0):
            currentpage -= 1
        if (currentpage==0):
            currentpage = 1
    except Donation.DoesNotExist:
        currentpage = 1
    
    jresponse = fetch()

    # do a maximum of x pages per cycle, but don't try to get more pages than available (results in NULL data)
    maxpages_fetched = jresponse['total_pages']
    maxpages = currentpage + max_pages_per_cycle  
    if maxpages > maxpages_fetched:
        maxpages = maxpages_fetched

    # call all newly available pages
    for index in range(currentpage,maxpages+1):
        page = index
        response = fetch()
        response = response['data']  # get the data from the page set above
        if len(response) >= 0:
            for json_donation in response: # go through response
                setwaszero=0
                if json_donation.get('donated_amount_in_cents',0)==0:
                    setwaszero=1
                try:
                    Donation.objects.get(event_id=event.id,id=json_donation.get('id',-1))
                except Donation.DoesNotExist:
                    Donation.objects.create (id=json_donation.get('id',-1),event_id=event.id,donated_amount_in_cents=json_donation.get('donated_amount_in_cents',0),page=page,donated_at=json_donation.get('created_at',0), was_zero=setwaszero)
                    



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

