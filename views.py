from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from dcodex.util import get_request_dict
import logging



from .models import *

def index(request):
    return HttpResponse("Hello, world. You're at the DCodex Carlson index.")
    
    
    
def location_siglum( request, location_id, siglum_text ):
    location = get_object_or_404(Location, id=location_id) 
    sublocations = location.sublocation_set.all()
    #siglum = Siglum.objects.filter(name=siglum_text).first()

    siglum = get_object_or_404(Siglum, name=siglum_text) 

    return render(request, 'dcodex_carlson/location.html', {'location': location, 'sublocations': sublocations, 'siglum':siglum, 'witness':siglum.witness, 'parallel':None} )

def location( request, location_id ):
    location = get_object_or_404(Location, id=location_id) 
    sublocations = location.sublocation_set.all()

    return render(request, 'dcodex_carlson/location.html', {'location': location, 'sublocations': sublocations} )


def attestations( request ):
    request_dict = get_request_dict(request)

    reading_code = request_dict.get('code')
    sublocation_id = request_dict.get('sublocation_id')
    sublocation = get_object_or_404(SubLocation, id=sublocation_id) 
    
    parallels = sublocation.get_parallels()
    html = ""
    for parallel in parallels:
        parallel_switch = ""
        if parallel:
            parallel_switch = "/%s " % parallel.code
        html += "<div>" + str(parallel_switch) + sublocation.code_attestations_string(reading_code, parallel) + "</div>"

    return HttpResponse(html)
    

def set_attestation( request ):
    request_dict = get_request_dict(request)

    reading_code = request_dict.get('code')
    corrector = request_dict.get('corrector')    

    sublocation_id = request_dict.get('sublocation_id')
    sublocation = get_object_or_404(SubLocation, id=sublocation_id) 

    witness_id = request_dict.get('witness_id')
    witness = get_object_or_404(Witness, id=witness_id) 
    

    parallel = None
    parallel_id = request_dict.get('parallel_id')
    if parallel_id:
        parallel = get_object_or_404(Parallel, id=parallel_id) 
    
    response = witness.set_attestation( sublocation=sublocation, code=reading_code, parallel=parallel, corrector=corrector )
    return HttpResponse("OK" if response else "FAIL")
    
