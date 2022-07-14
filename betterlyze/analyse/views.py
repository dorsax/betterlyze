from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Event
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
    return HttpResponseRedirect(reverse('analyse:detail', args=(event.id,)))
