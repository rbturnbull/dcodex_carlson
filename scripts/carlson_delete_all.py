from dcodex_carlson.models import *


def run(*args):   
    Location.objects.all().delete()
    SubLocation.objects.all().delete()
    Reading.objects.all().delete()
    Attestation.objects.all().delete()
    Siglum.objects.all().delete()
    Parallel.objects.all().delete()
    Witness.objects.all().delete()
    Macro.objects.all().delete()
    VerseLabel.objects.all().delete()
    Suppression.objects.all().delete()
    Collation.objects.all().delete()
