from django.contrib import admin

# Register your models here.
from .models import *

class SublocationInline(admin.TabularInline):
    model = SubLocation
    extra = 0
    
@admin.register(Location)    
class LocationAdmin(admin.ModelAdmin):
    inlines = [SublocationInline]


class AttestationInline(admin.TabularInline):
    model = Attestation
    extra = 0

@admin.register(SubLocation)    
class SubLocationAdmin(admin.ModelAdmin):
    inlines = [AttestationInline]


admin.site.register(Reading)
admin.site.register(Siglum)
admin.site.register(Witness)
admin.site.register(Parallel)
admin.site.register(Attestation)
admin.site.register(Macro)
admin.site.register(Collation)
admin.site.register(VerseLabel)
