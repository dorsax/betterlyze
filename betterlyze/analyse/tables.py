import django_tables2 as tables
from django.utils.html import format_html

from .models import Donation

class DonationTable(tables.Table):
    class Meta:
        model = Donation
        fields = ("donated_amount_in_cents", "was_zero", "donated_at",  "donor", "message", )
        order_by = ('donated_at', )

    def render_was_zero(self, value):
        if (value):
            return format_html('<span class="bi bi-check"/>',)
        else:
            return format_html('<span class="bi bi-x"/>',)

