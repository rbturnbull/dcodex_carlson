from dcodex_carlson.models import *

import re
import sys
from collections import defaultdict
#https://django-extensions.readthedocs.io/en/latest/runscript.html


def run(*args):       
    if len(args) == 0:
        print("Usage: --script-args [collation_name]")
        return
    collation_name = args[0]
    
    collation = Collation.objects.filter( name=collation_name ).first()
    if not collation:
        print("Cannot find collation by name:", collation_name )
        return

    
    print("* %s %s ;" % (
        " ".join(["/%s" % parallel.code for parallel in collation.parallels.all()]),
        " ".join(["~".join(witness.all_sigla_names()) for witness in collation.witnesses.all()]),
        ) )
    for suppression in collation.suppressions.all():
        print(suppression)

    for location in collation.locations.all():
        for verse_label in location.verse_labels.all():
            print(verse_label)
        for macro in location.macros.all():
            if macro.description:
                print('" %s "' % macro.description )
            print(macro)
            
#        print(location)
        print("{{}")
        print( "[ %s" % (location.base_text) )
        sublocations = location.sublocation_set.all()
        for sublocation in sublocations:
            print(" | %s" % ( " ".join( [reading.text for reading in sublocation.reading_set.all()] )   ))
        print("]")
        
        if len(sublocations) == 0:
            continue
        parallels = Parallel.objects.filter( attestation__sublocation__location=location ).distinct()
        if len(parallels) == 0:
            parallels = [None]
        for parallel in parallels:
            if parallel != None:
                print(parallel.code)
            print("<")
            codes_dict = defaultdict(list)

            for witness in Witness.objects.filter( attestation__sublocation__location=location, attestation__parallel=parallel ).distinct():

                correctors = Attestation.objects.filter( sublocation=sublocation, witness=witness, parallel=parallel ).order_by('corrector').values('corrector').distinct()
#                print("correctors:", correctors)
                for corrector in correctors:
                    corrector = corrector['corrector']
#                    print("Corrector:", corrector)
                    codes = ""                
                    for sublocation in sublocations:
                        attestation = Attestation.objects.filter( sublocation=sublocation, witness=witness, parallel=parallel, corrector=corrector ).first()
#                        print("attestation", attestation)
                        symbol = attestation.code if attestation else "?"
                        codes += symbol
                    
                    corrector_suffix = ":%d" % corrector if corrector else ""
                    witness_string = "%s%s" % (witness, corrector_suffix)
#                    print(codes, witness_string)
                    codes_dict[codes].append( witness_string )
            delimiter = ""
            for code in codes_dict:                
                print(" %s %s %s " % (delimiter, code, " ".join(codes_dict[code]) ) )
            
                delimiter = "|"

            print(">")
        

        print("}")        
#        return

        
