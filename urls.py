from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:location_id>/<str:siglum_text>/', views.location_siglum, name='location_siglum'),
    path('<int:location_id>/', views.location, name='location'),
    path('attestations/', views.attestations, name='attestations'),
    path('set_attestation/', views.set_attestation, name='set_attestation'),
]