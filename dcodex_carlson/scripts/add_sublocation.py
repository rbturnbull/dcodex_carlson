from dcodex_carlson.models import *


def run(*args):       
    if len(args) < 2:
        print("Usage: --script-args location_id reading_text [/parallel] [sigla_for_zero]")
        return
    location_id = args[0]
    reading_text = args[1]
    sigla_for_zero = args[2:]
    
    parallel = None
    if len(sigla_for_zero) > 0:
        if sigla_for_zero[0][0] == '/':
            parallel_switch = sigla_for_zero[0]
            sigla_for_zero = sigla_for_zero[1:]
            parallel = Parallel.objects.filter( code=parallel_switch[1:] ).first()

    print(location_id)
    print(reading_text)
    print(sigla_for_zero)
    print("parallel:", parallel)
    
    location = Location.objects.get(id=location_id)
    print(location)
    
    sublocation = location.add_sublocation( reading_text, sigla_for_zero, parallel )
    print(sublocation)
        
