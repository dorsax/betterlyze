from django.urls import path

from . import views

app_name='analyse'
urlpatterns = [
    path('', views.compare, name='index'),
    path('<int:event_id>/', views.detail, name='detail'),
    path('compare/', views.compare, name='compare'),
    path('<int:event_id>/crawl/', views.crawl, name='crawl'),
    
]
