from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the DCodex Carlson index.")
    
    
def location_sublocation_ms( request, location_id, sublocation_id, ms_siglum ):
    return HttpResponse("%d %d %s" % (location_id, sublocation_id, ms_siglum) )


