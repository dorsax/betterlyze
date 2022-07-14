from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Event
from .crawler import crawl as external_crawl
from . import event_dashboards
#from . import event_dashboards
# Create your views here.

def index(request):
    all_events_list = Event.objects.order_by('-end')
    context = {
        'all_events_list' : all_events_list,
    }
    return render(request, 'analyse/index.html', context)

def detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    return render(request, 'analyse/detail.html', {'event': event})

def crawl(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    external_crawl(event_id=event_id,max_pages_per_cycle=2,per_page=10)
    return HttpResponseRedirect(reverse('analyse:detail', args=(event.id,)))

def compare (request, event_id_1, event_id_2):
    event1 = get_object_or_404(Event, pk=event_id_1)
    event2 = get_object_or_404(Event, pk=event_id_2)
    context = {
        'event1': event1,
        'event2' : event2,
        'dash_context' : {
        'event_old' : event_id_1,
        'event_new' : event_id_2,
        },
    }
    return render(request, 'analyse/compare.html', context)
