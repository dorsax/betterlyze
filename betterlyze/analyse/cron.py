from datetime import timedelta
from django.utils import timezone
from django_cron import CronJobBase, Schedule
from .crawler import crawl
from .models import Event

class CronCrawl(CronJobBase): # only crawls currently active events
    RUN_EVERY_MINS = 5

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'analyse.cron.CronCrawl'    # a unique code

    def do(self):
        currentdatetime = timezone.now()
        # get all events started before now and ended about a cacle before now plus 10 minutes for
        events = Event.objects.filter(start__lte =currentdatetime, end__gte = currentdatetime - timedelta (minutes=self.RUN_EVERY_MINS+10)) 
        for event in events:
            crawl(event.id,1,1)

class CronCrawlAll(CronJobBase): # crawls all events
    RUN_EVERY_MINS = 1440 # each day

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'analyse.cron.CronCrawlAll'    # a unique code

    def do(self):
        events = Event.objects.all()
        for event in events:
            crawl(event.id)