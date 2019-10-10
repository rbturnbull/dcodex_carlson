from dcodex_carlson.models import *
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

    collation.export()