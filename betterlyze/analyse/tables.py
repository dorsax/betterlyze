import django_tables2 as tables

from .models import Donation

class DonationTable(tables.Table):
    class Meta:
        model = Donation
        template_name = "django_tables2/bootstrap.html"
        fields = ("donated_amount_in_cents", "was_zero", "donated_at",  "donor", "message" )