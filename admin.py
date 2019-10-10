from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Location)
admin.site.register(SubLocation)
admin.site.register(Reading)
admin.site.register(Siglum)
admin.site.register(Witness)
admin.site.register(Parallel)
admin.site.register(Attestation)
admin.site.register(Macro)
admin.site.register(Collation)
