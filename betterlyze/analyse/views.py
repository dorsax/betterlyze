from django_tables2 import SingleTableMixin
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView
from bootstrap_datepicker_plus.widgets import DateTimePickerInput

from django.urls import reverse_lazy

from django_filters.views import FilterView
from .filter import DonationFilter

from .models import Event, Donation
from .crawler import crawl as external_crawl
from .tables import DonationTable
from . import event_dashboards
#from . import event_dashboards
# Create your views here.

class EventCreateView (CreateView):
    model = Event
    fields = [  "id" ,"start" ,"end","description" ]
    template_name = "analyse/event_create.html"
    def get_form(self):
        form = super().get_form()
        form.fields["start"].widget = DateTimePickerInput()
        form.fields["end"].widget = DateTimePickerInput()
        return form
    def get_success_url(self) -> str:
        return reverse('analyse:list')

class EventEditView (UpdateView):
    model = Event
    fields = [  "id" ,"start" ,"end","description" ]
    template_name = "analyse/event_edit.html"
    def get_form(self):
        form = super().get_form()
        form.fields["start"].widget = DateTimePickerInput()
        form.fields["end"].widget = DateTimePickerInput()
        form.fields['id'].disabled = True
        return form
    def get_success_url(self) -> str:
        return reverse('analyse:detail', args=(self.get_object().id,))

class EventList(ListView):
    model = Event
    template_name = 'analyse/event_list.html'


class EventDetail (SingleObjectMixin, SingleTableMixin, FilterView):
    paginate_by = 50
    template_name = 'analyse/event_detail.html'
    table_class = DonationTable
    filterset_class = DonationFilter

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

@login_required
def anonymize(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.donation_set.all().update(message='') 
    event.donation_set.all().update(donor='anonymized') 
    return HttpResponseRedirect(reverse('analyse:detail', args=(event.id,)))

def compare (request):
    return render(request, 'analyse/compare.html')
