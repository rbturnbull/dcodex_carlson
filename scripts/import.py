from dcodex_carlson.models import *


def run(*args):       
    if len(args) == 0:
        print("Usage: --script-args staleonly")
        return
    path = args[0]
        
    collation = Collation(name=os.path.basename(path) )
    collation.save()
    collation.import_from_file( path )
        
