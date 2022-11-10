from django_tables2 import SingleTableView
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.decorators import login_required

from .models import Event, Donation
from .crawler import crawl as external_crawl
from .tables import DonationTable
from . import event_dashboards
#from . import event_dashboards
# Create your views here.

class EventList(ListView):
    model = Event
    template_name = 'analyse/event_list.html'


class EventDetail (SingleObjectMixin, SingleTableView):
    paginate_by = 20
    template_name = 'analyse/event_detail.html'
    table_class = DonationTable

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Event.objects.all())
        return super(EventDetail,self).get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(EventDetail, self).get_context_data(**kwargs)
        context['event'] = self.object
        return context

    def get_queryset(self):
        return self.object.donation_set.all()

@login_required
def crawl(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    external_crawl(event_id=event_id)
    return HttpResponseRedirect(reverse('analyse:detail', args=(event.id,)))

@login_required
def purge(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.donation_set.all().delete()
    return HttpResponseRedirect(reverse('analyse:detail', args=(event.id,)))

def compare (request):
    return render(request, 'analyse/compare.html')