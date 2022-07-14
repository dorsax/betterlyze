from django.urls import path

from . import views

app_name='analyse'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:event_id>/', views.detail, name='detail'),
    path('compare/<int:event_id_1>/<int:event_id_2>/', views.compare, name='compare'),
    path('<int:event_id>/crawl/', views.crawl, name='crawl'),
    
]
