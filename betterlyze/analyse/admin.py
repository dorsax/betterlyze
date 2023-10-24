from django.contrib import admin
from django.apps import apps
from django.contrib import auth
from django_plotly_dash import admin as dpdadmin 
# Register your models here.

# De-register all models from other apps
# !!! Django_Cron cannot be removed by this, as it isn't registered when this script is executed.
#  We need thos logs anyway, so this isn't 
for app_config in apps.get_app_configs():
    for model in app_config.get_models():
        print(model)
        if admin.site.is_registered(model):
            admin.site.unregister(model)

# reregister Users until we rip out the admin completely
admin.site.register(auth.models.User)
