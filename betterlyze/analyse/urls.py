from django.urls import path

from . import views

app_name='analyse'
urlpatterns = [
    path('', views.compare, name='index'),
    path('<int:pk>/', views.EventDetail.as_view(), name='detail'),
    path('details/', views.EventList.as_view(), name='details'),
    path('<int:event_id>/crawl/', views.crawl, name='crawl'),
    path('<int:event_id>/purge/', views.purge, name='purge'),
]
