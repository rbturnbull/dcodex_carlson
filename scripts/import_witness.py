from dcodex_carlson.models import *


def run(*args):       
    if len(args) < 3:
        print("Usage: --script-args path collation siglum")
        return
    path = args[0]
    collation_name = args[1]
    siglum_text = args[2]
    siglum = Siglum.objects.filter(name=siglum_text).first()
    if not siglum:
        print("Cannot find witness with siglum", siglum_text)
        return

    witness = siglum.witness
        
    collation = Collation.objects.filter( name=collation_name ).first()
    if not collation:
        print("Cannot find collation with name", collation_name)
        return

    collation.import_witness_from_file( witness, path )
        
