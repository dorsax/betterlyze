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

class Donation(models.Model):
    id = models.CharField(primary_key=True,max_length=64)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    donated_amount_in_cents = models.BigIntegerField('Donation in Cents')
    page = models.BigIntegerField()
    donated_at = models.DateTimeField()
    was_zero = models.IntegerField(default=0)
