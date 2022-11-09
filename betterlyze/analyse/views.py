from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin

from .models import Event, Donation
from .crawler import crawl as external_crawl
from . import event_dashboards
#from . import event_dashboards
# Create your views here.

def details(request):
    all_events_list = Event.objects.order_by('-end')
    context = {
        'all_events_list' : all_events_list,
    }
    return render(request, 'analyse/index.html', context)

class DetailView (DetailView):
    model = Event
    template_name = 'analyse/detail.html'

class EventDetail (SingleObjectMixin, ListView):
    paginate_by = 20
    template_name = 'analyse/event_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Event.objects.all())
        return super(EventDetail,self).get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(EventDetail, self).get_context_data(**kwargs)
        context['event'] = self.object
        return context

    def get_queryset(self):
        return self.object.donation_set.all()

def crawl(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    external_crawl(event_id=event_id)
    return HttpResponseRedirect(reverse('analyse:detail', args=(event.id,)))

def compare (request):
    return render(request, 'analyse/compare.html')