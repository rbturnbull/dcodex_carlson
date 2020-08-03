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
    collation = location.collation_set.first()

    siglum = get_object_or_404(Siglum, name=siglum_text) 
    
    verse_labels = location.closest_verse_labels().all()

    return render(request, 'dcodex_carlson/location.html', {'location': location, 'sublocations': sublocations, 'siglum':siglum, 'witness':siglum.witness, 'parallel':None, 'verse_labels':verse_labels,} )


def location_siglum_parallel( request, location_id, siglum_text, parallel_code ):
    location = get_object_or_404(Location, id=location_id) 
    sublocations = location.sublocation_set.all()
    siglum = get_object_or_404(Siglum, name=siglum_text) 
    parallel = get_object_or_404(Parallel, code=parallel_code) 
    verse_labels = [verse_label for verse_label in location.closest_verse_labels().all() if verse_label.parallel == parallel]
        
    transcription = None
    manuscript = None
    bible_verse = None
    if siglum.witness.manuscript and len(verse_labels) > 0:
        manuscript = siglum.witness.manuscript
        bible_verse = verse_labels[0].bible_verse()
        transcription = manuscript.transcription( bible_verse )

    return render(request, 'dcodex_carlson/location.html', {'location': location, 'manuscript':manuscript, 'bible_verse':bible_verse,'transcription':transcription, 'sublocations': sublocations, 'siglum':siglum, 'witness':siglum.witness, 'parallel':parallel, 'verse_labels':verse_labels,} )


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
    parallel_code = request_dict.get('parallel_code')    
    if parallel_id:
        parallel = get_object_or_404(Parallel, id=parallel_id) 
    elif parallel_code:
        parallel = get_object_or_404(Parallel, code=parallel_code) 
        
    logger = logging.getLogger(__name__)    

    logger.error("Parallel in view")
    logger.error(parallel)
    
    response = witness.set_attestation( sublocation=sublocation, code=reading_code, parallel=parallel, corrector=corrector )
    return HttpResponse("OK" if response else "FAIL")
    
