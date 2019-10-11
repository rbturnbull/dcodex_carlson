from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:location_id>/<int:sublocation_id>/<str:ms_siglum>', views.location_sublocation_ms, name='location_sublocation_ms'),
]