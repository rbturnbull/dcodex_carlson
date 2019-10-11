from dcodex_carlson.models import *

def run(*args):       
    if len(args) == 0:
        print("Usage: --script-args collation_name [output_path]")
        return
    collation_name = args[0]
    collation = Collation.objects.filter( name=collation_name ).first()
    if not collation:
        print("Cannot find collation by name:", collation_name )
        return
    
    if len(args) > 1:
        output_path = args[1]
        with open(output_path, 'w') as output_file:
            collation.export( output_file )
    else:    
        collation.export()