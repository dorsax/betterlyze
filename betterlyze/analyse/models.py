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
