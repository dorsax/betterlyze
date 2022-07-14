from django.contrib import admin

# Register your models here.

from .models import Donation, Event

admin.site.register(Event)
admin.site.register(Donation)