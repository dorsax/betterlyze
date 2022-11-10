import django_filters
from .models import Donation

class DonationFilter(django_filters.FilterSet):
    class Meta:
        model = Donation
        fields = {
            'donor': ['icontains'],
            'message': ['icontains'],
        }
