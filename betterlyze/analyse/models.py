import pandas as pd

from datetime import timedelta

from django.db import models

# Create your models here.


class Event(models.Model):
    id = models.IntegerField('Event-ID',primary_key=True, default=0)
    start = models.DateTimeField('begin of the event')
    end = models.DateTimeField('end of the event')
    description = models.CharField(max_length=2000)

    def year(self):
        return self.start.year
    
    def __str__ (self):
        return ("[{year}] {name}".format(year=self.year(),name=self.description))

    def donation_sum(self):
        if (self.donation_count()==0): return 0
        return  self.donation_set.all().aggregate(models.Sum('donated_amount_in_cents'))['donated_amount_in_cents__sum']

    def donation_sum_euro(self):
        return self.donation_sum()/100

    def donation_count(self):
        return len(self.donation_set.all())

class Donation(models.Model):
    id = models.CharField(primary_key=True,max_length=64)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    donated_amount_in_cents = models.BigIntegerField('Spende in Cents')
    page = models.BigIntegerField('Seite')
    donated_at = models.DateTimeField('Spendenzeitpunkt')
    was_zero = models.IntegerField('Geldbetrag anonym', default=0)
    donor = models.CharField('Spender',max_length=255,default='Anonym')
    message = models.TextField('Nachricht',default='')

class EventStatistic (models.Model):
    event = models.OneToOneField(Event,on_delete=models.CASCADE)
    total = models.BigIntegerField('Gesamt',default=0)


    def _default_categories() -> dict:
        donation_ranges = [0,1000,10000,100000,1000000000000000]
        return dict.fromkeys(donation_ranges,{'donations':0,'total':0})

    def _default_timeslice() -> dict :
        return {}
    
    categories = models.JSONField('Kategoriestatistik',default=_default_categories)
    timeslice = models.JSONField('Zeitstatistik',default=_default_timeslice)

    def get_categories(self) -> pd.DataFrame :
        return pd.DataFrame.from_dict(self.categories)
    def get_timeslice(self) -> pd.DataFrame :
        return pd.DataFrame.from_dict(self.timeslice)
    
    def calculate(self):
        '''calculates the statistics, thus manipulates the object!'''

        self.total = self.event.donation_set.all().aggregate(models.Sum('donated_amount_in_cents'))['donated_amount_in_cents__sum']
        # timeline_index = pd.timedelta_range(start='-1h',
        #                             end = (self.event.end - self.event.start) + timedelta(hours=2),
        #                             freq='1h',
        #                             )
        # timeline = pd.DataFrame(index=timeline_index)
        # timeline['timestamp'] = timeline_index + self.event.start
        # timeline.iloc[len(timeline)-1].timestamp = timeline.iloc[len(timeline)-1].timestamp + timedelta(days=365) # set the maximum to be grouped to to 1 year after 
        # donations = pd.DataFrame.from_records(es.event.donation_set.values())
        # slicer = pd.cut(donations['donated_at'], 
        #                 timeline['timestamp'],
        #                 include_lowest=True,
        #                 )
        # timeline.drop(timeline.tail(1).index,inplace=True) # remove last entry: only needed for the upper boundary

        # grouped_total = donations['donated_amount_in_cents'].groupby(slicer,observed=False).sum()
        # grouped_count = donations['donor'].groupby(slicer,observed=False).count()

        donations = pd.DataFrame.from_records(self.event.donation_set.values())
        donations['donated_at'] = pd.to_datetime(donations.donated_at)
        donations = donations.set_index('donated_at')

        donations.drop([
            'event_id',
            'was_zero',
            'id',
            'page',
            'message'
        ],axis=1,inplace=True)

        donation_totals = donations.drop(['donor'],axis=1).groupby(pd.Grouper(freq='1h')).sum()
        donation_donors = donations.drop(['donated_amount_in_cents'],axis=1).groupby(pd.Grouper(freq='1h')).count()
        delta_list = [
            timedelta(days=-1),
            timedelta(hours=-1),
        ]
        additionals = {'totals':{},'donors':{}}

        current_index = -1 * len(delta_list)
        for stage in factory(delta_list,self.event) :
            if (self.event.start >= stage): # before event starts
                loced_dataframe = donations.loc[stage:]

            if (self.event.start < stage and self.event.end <= stage): # after event ended
                loced_dataframe = donations.loc[:stage]
                
            if (self.event.end == stage):
                current_index = 1

            additionals['totals'][current_index] = loced_dataframe.donated_amount_in_cents.sum()
            additionals['donors'][current_index] = loced_dataframe.donated_amount_in_cents.count()
            
            
            donations = donations.loc[:self.event.start + difference]
            current_index+=1

        total_timeframe = donations.loc[self.event.end:]
        donations = donations.loc[:self.event.end]

        current_index = 1
        differences= -1*differences
        for difference in differences :
            loced_dataframe = donations.loc[self.event.start + difference:]
            additionals['totals'][current_index] = loced_dataframe.donated_amount_in_cents.sum()
            additionals['donors'][current_index] = loced_dataframe.donated_amount_in_cents.count()
            donations = donations.loc[:self.event.start + difference]
            current_index+=1
        additional_totals[-2] = donations.loc[self.event.start - timedelta(hours = 1):].donated_amount_in_cents.sum()
        additional_totals[-1] = donations.loc[self.event.start - timedelta(seconds = 1):].donated_amount_in_cents.sum()

        grouped_total.reset_index(
            inplace=True,
            drop=True,
        )
        grouped_count.reset_index(
            inplace=True,
            drop=True,
        )

        donation_ranges = [0,1000,10000,100000,1000000000000000]
        donation_labels = ['<= 10 €','<= 100 €','<= 1000 €','> 1000 €']
        donation_slice = pd.cut(donations['donated_amount_in_cents'], donation_ranges, labels=donation_labels)
        pie_count = donations["donor"].groupby(donation_slice, observed=False).count()
        pie_sum = donations["donated_amount_in_cents"].groupby(donation_slice, observed=False).sum()
        self.categories = pd.concat([pie_count,pie_sum], axis=1).to_dict()

        # sanity check
        assert self.total == grouped_total.sum()

        self.timeslice = pd.concat([grouped_count,grouped_total], axis=1).to_dict()
        
    def __str__(self) -> str:
        return f"{self.total}: {self.categories} | {self.timeslice}"
    
def factory (delta_list = list, event = Event) :
    """
    returns a list in the form of ranges...start,end,...ranges
    """
    serie = pd.Series(delta_list)
    dictator = list()
    # serie.add converts tiimedeltas to timestamps
    dictator+=(serie.sort_values(axis=0,ascending=True).add(event.start)).to_list()
    # adding start end end to identify boundaries
    dictator+=[pd.Timestamp(event.start),pd.Timestamp(event.end)]
    # do the same as above but with positive numbers
    dictator+=(-1 * serie).sort_values(axis=0,ascending=True).add(event.end).to_list()
    return dictator
