from django.db import models
from django.db.models import Max, Min
import re
import sys, os
from collections import defaultdict
import unicodedata
import logging
from dcodex.models import Manuscript
from dcodex_bible.models import BibleVerse




def convert_greek_unicode(text):
    betacode = "YFPAULOSTKQNRDEWIXHGMhCZB" + "i"
    unicode  = "ψφπαυλοστκθνρδεωιχηγμ῾ξζβ" + "\u0345"
    trans = str.maketrans(betacode, unicode)
    text = text.translate(trans)
    text = text.replace("σ ", "ς ")
    text = text.replace("σ.", "ς.")
    text = text.replace("σ)", "ς)")
    if len(text) > 0 and text[-1] == "σ":
        text = text[:-1] + "ς"
    text = text.replace("_"," ")
    return unicodedata.normalize("NFC", text) # This isn't working for rough breathing...

class Parallel(models.Model):
    code = models.CharField(max_length=10)
    description = models.CharField(max_length=100)
    def __str__(self):
        return self.code

# Create your models here.
class Witness(models.Model):
    intf_id = models.IntegerField(null=True, default=None)
    year_min = models.IntegerField(null=True, default=None)
    year_max = models.IntegerField(null=True, default=None)
    manuscript = models.ForeignKey( Manuscript, on_delete=models.SET_DEFAULT, default=None, null=True )
    
    def __str__(self):
        siglum = self.siglum_set.first()
        if siglum:
            return str(siglum)
        return str(self.intf_id)
    class Meta:
        verbose_name_plural = 'Witnesses'
    def all_sigla_names(self):
        return [str(siglum) for siglum in self.siglum_set.all()]
    def attests_reading(self, sublocation, code, parallel = None, corrector=None ):
        attestation_count = Attestation.objects.filter( sublocation=sublocation, witness=self, code=code, parallel=parallel, corrector=corrector ).count()        
        if attestation_count:
            return True
        return False
    
    def get_attestation(self, sublocation, corrector=None, parallel=None):
        return Attestation.objects.filter( witness=self, sublocation=sublocation, corrector=corrector, parallel=parallel ).first()
    
    def set_attestation(self, sublocation, code, corrector=None, parallel=None):
        Attestation.objects.filter( witness=self, sublocation=sublocation, corrector=corrector, parallel=parallel ).all().delete()
        attestation = Attestation( witness=self, sublocation=sublocation, code=code, corrector=corrector, parallel=parallel )
        attestation.save()
                
        return attestation
    
class Siglum(models.Model):
    witness = models.ForeignKey( Witness, on_delete=models.CASCADE )
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = 'Sigla'
        ordering = ['name']

    @classmethod
    def get_with_corrector( cls, text ):
        siglum_components = text.split(":")
        siglum_name = siglum_components[0]
        corrector = None
        if len(siglum_components) > 1:
            corrector = int(siglum_components[1])
        return cls.objects.filter( name=siglum_name ).first(), corrector
    
    
class Macro(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200, default="")
    
    witnesses = models.ManyToManyField( Witness )
    mode = models.CharField(max_length=1, default="")
    parallel = models.ForeignKey( Parallel, on_delete=models.SET_DEFAULT, default=None, null=True )

    def __str__(self):
        parallel_switch = ""
        if self.parallel:
            parallel_switch = "/%s " % (self.parallel.code)
        
        witnesses_sigla_names = [str(witness) for witness in self.witnesses.all()]
        
        return "%s=%s %s %s ;" % (parallel_switch, self.mode, self.name, " ".join(witnesses_sigla_names) )
        
class VerseLabel(models.Model):
    reference = models.CharField(max_length=50)
    parallel = models.ForeignKey( Parallel, on_delete=models.SET_DEFAULT, default=None, null=True )
#    verse = models.ForeignKey( BibleVerse, on_delete=models.SET_DEFAULT, default=None, null=True )
    def __str__(self):
        parallel_switch = ""
        if self.parallel:
            parallel_switch = "/%s " % (self.parallel.code)
        return "%s@ %s" % (parallel_switch, self.reference )
    def bible_verse(self):
        return BibleVerse.get_from_string( self.reference )

class Location(models.Model):
    verse_labels = models.ManyToManyField(VerseLabel, blank=True)
    base_text = models.CharField(max_length=200)
    macros = models.ManyToManyField( Macro, blank=True )
    
    def __str__(self):
        return self.base_text
    def base_text_greek(self):
        return convert_greek_unicode( self.base_text )
    def get_parallels(self):
        parallels = Parallel.objects.filter( attestation__sublocation__location=self ).distinct()
        if len(parallels) == 0:
            parallels = [None]
        return parallels
    def next(self):
        return Location.objects.filter( id__gt=self.id ).order_by('id').first()
    def prev(self):
        return Location.objects.filter( id__lt=self.id ).order_by('-id').first()
        
    def closest_verse_labels(self):
        closest_location_with_labels = Location.objects.filter( id__lte=self.id).exclude(verse_labels=None ).order_by('-id').first()
        if closest_location_with_labels:
            return closest_location_with_labels.verse_labels
        return None
    def max_sublocations_order( self ):
        dictionary = self.sublocation_set.all().aggregate(Max('order'))
        return dictionary.get( "order__max" )
    def add_sublocation( self, reading_text, sigla_for_zero = None, parallel = None ):
        prev_order = self.max_sublocations_order()
        order = prev_order + 1 if prev_order is not None else 0
        sublocation = SubLocation( location=self, order=order )
        sublocation.save()
        
        reading = Reading( sublocation=sublocation, text=reading_text, order=1 )
        reading.save()
        
        code = 0
        for siglum_text in sigla_for_zero:        
            siglum, corrector = Siglum.get_with_corrector(siglum_text)
            if not siglum:
                print("Cannot find",siglum_text)
                continue
                            
            siglum.witness.set_attestation(sublocation=sublocation, code=code, corrector=corrector, parallel=parallel)

        return sublocation
            
class SubLocation(models.Model):
    location = models.ForeignKey( Location, on_delete=models.CASCADE )
    order    = models.IntegerField( )
    weighting = models.CharField(max_length=10, default="", blank=True)
    def __str__(self):
        readings = [str(reading) for reading in self.reading_set.all()]
        return "id %d - %s: %s [%d]" % (self.id, str(self.location), " ".join(readings), self.order)
    class Meta:
        ordering = ['order']
    def get_parallels(self):
        parallels = Parallel.objects.filter( attestation__sublocation=self ).distinct()
        if len(parallels) == 0:
            parallels = [None]
        return parallels
    def attestations(self, parallel=None):
        return Attestation.objects.filter( sublocation=self, parallel=parallel )
    def code_attestations(self, code, parallel=None):
        return Attestation.objects.filter( sublocation=self, code=code, parallel=parallel )
    def attestations_string(self, parallel=None):
        attestations = self.attestations(parallel)
        return " ".join( [str(attestation.witness) for attestation in attestations] )        
    def code_attestations_string(self, code, parallel=None):
        attestations = self.code_attestations(code, parallel)
        return " ".join( [str(attestation.witness) for attestation in attestations] )        
    
class Reading(models.Model):
    sublocation = models.ForeignKey( SubLocation, on_delete=models.CASCADE )
    text = models.CharField(max_length=200)
    order = models.IntegerField( )
    def __str__(self):
        return self.text
    class Meta:
        ordering = ['order']
    def text_greek(self):
        return convert_greek_unicode( self.text )
        

    
class Attestation( models.Model ):
    sublocation = models.ForeignKey( SubLocation, on_delete=models.CASCADE )
    code      = models.CharField(max_length=1)
    witness   = models.ForeignKey( Witness, on_delete=models.CASCADE )
    corrector = models.IntegerField( default=None, null=True, blank=True )
    parallel  = models.ForeignKey( Parallel, on_delete=models.SET_DEFAULT, default=None, null=True )
    text      = models.TextField( default=None, blank=True, null=True)
    def __str__(self):
        return "%s %s %s %s %s" % (self.sublocation, self.code, self.witness, self.corrector, self.parallel)

class Suppression( models.Model ):
    parallel = models.ForeignKey( Parallel, on_delete=models.SET_DEFAULT, default=None, null=True )
    witness  = models.ForeignKey( Witness, on_delete=models.CASCADE )
    def __str__(self):
        parallel_switch = ""
        if self.parallel:
            parallel_switch = "/%s " % (self.parallel.code)
        return "%s- %s ;" % (parallel_switch, str(self.witness) )

    
def get_witness_or_create_from_siglum_name( siglum_text ):
    siglum = Siglum.objects.filter(name=siglum_text).first()
    if not siglum:
        witness = Witness()
        witness.save()
        siglum = Siglum(name=siglum_text, witness=witness)
        siglum.save()
    else:
        witness = siglum.witness
    return witness

class Collation( models.Model ):
    parallels = models.ManyToManyField(Parallel)
    witnesses = models.ManyToManyField(Witness)
    locations = models.ManyToManyField(Location)
    suppressions = models.ManyToManyField(Suppression)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name
    
    def import_from_file(self, path):
        with open(path) as file:        
            data = file.read().replace('\n', ' ')
        
            # Save Comments
            comments = re.findall('"(.*?)"', data)
        
            # Remove comments
            data = re.sub('".*?"','',data)
        
            locations = data.split("[")
            initial_data = locations.pop(0)
        
        
            ###### Save manuscripts ######
            mss = re.search( "\* (.*?);", initial_data )
            if not mss:
                print("No MSS found.")
                return
            mss = mss[1].split()
            for ms in mss:
                if len(ms) == 0:
                    continue
                if ms[0] == '/':
                    parallel_code = ms[1:]
                    parallel, created = Parallel.objects.get_or_create( code=parallel_code )                
                    self.parallels.add(parallel)
                else:
                    sigla = ms.split("~")
                    witness = None
                    for siglum_name in sigla:
                        if witness == None:                
                            witness = get_witness_or_create_from_siglum_name(siglum_name)
                            self.witnesses.add(witness)                        
                        else:
                            siglum = Siglum.objects.filter(name=siglum_name, witness=witness).first()
                            if not siglum:
                                siglum = Siglum(name=siglum_name, witness=witness)
                                siglum.save()

                

            ###### Save suppressions ######
            suppression_matches = re.findall("/*([a-z])* - (.*?);", initial_data)
            for match in suppression_matches:
                parallel = None
                parallel_code = match[0]
                if len(parallel_code) > 0:
                    parallel = self.parallels.filter( code=parallel_code ).get()           
            
                sigla_names = match[1].split()
            
                for siglum_name in sigla_names:
                    witness = get_witness_or_create_from_siglum_name( siglum_name )
                    suppression = Suppression(parallel=parallel, witness=witness)
                    suppression.save()
                    self.suppressions.add( suppression )
        
            prev_location_data = initial_data
            for location_data in locations:
                components = re.search( "(.*)\](.*)", location_data )
                if  not components:
                    print("NO components")
                    sys.exit()
            
                sublocations = components.group(1).strip().split("|")
                parallels = components.group(2).strip()

                base_text = sublocations.pop(0)
        
                location = Location(base_text=base_text.strip())
                location.save()
                self.locations.add(location)     
            
        
                macro_matches = re.findall("/*([a-z])* =([\-\+]*) (.*?);", prev_location_data)
                for match in macro_matches:
                    parallel = None
                    parallel_code = match[0]
                    if len(parallel_code) > 0:
                        parallel = self.parallels.filter( code=parallel_code ).get()           
                
                    mode = match[1]
                    sigla_names = match[2].split()
                    macro_name = sigla_names.pop(0)
                
                    description = ""
                    for comment in comments:
                        match = re.search( re.escape(macro_name), comment )
                        if match:
                            description += comment
                    
                
                    macro = Macro( name=macro_name, mode=mode, parallel=parallel, description=description.strip() )
                    macro.save()                
                    for siglum_name in sigla_names:
                        witness = get_witness_or_create_from_siglum_name( siglum_name )
                        macro.witnesses.add( witness )
                    location.macros.add(macro)
                
                verse_matches = re.findall("/*([a-z])* @ ([^\s]+)", prev_location_data)
                for match in verse_matches:
                    parallel = None
                    parallel_code = match[0]
                    if len(parallel_code) > 0:
                        parallel = self.parallels.filter( code=parallel_code ).get()           
                
                    verse_ref = match[1]
                
                    verse_label = VerseLabel( reference=verse_ref, parallel=parallel )
                    verse_label.save()                

                    location.verse_labels.add(verse_label)
                
            
                sublocation_objects = []
                for order, sublocation_text in enumerate(sublocations):
                    sublocation = SubLocation( location=location, order=order )
                    sublocation.save()
                    sublocation_objects.append(sublocation)
                    
                    # Check for weighting of variant
                    sublocation_components = re.match( "^(\*[^\s]+) (.*)", sublocation_text )
                    if sublocation_components:
                        sublocation.weighting = sublocation_components.group(1)
                        sublocation.save()
                        sublocation_text = sublocation_components.group(2)
                
                    readings = sublocation_text.strip().split()
                    for reading_index, reading in enumerate( readings ):
                        reading = Reading( sublocation=sublocation, text=reading.strip(), order=reading_index+1 )
                        reading.save()
            
                for parallel in re.findall('/*([a-z]?)\s*<(.*?)>', parallels):
                    parallel_code = parallel[0].strip()
                    collation_codes = parallel[1].strip().split("|")
                
                    parallel = None
                    if len(parallel_code) > 0:
                        parallel = self.parallels.filter( code=parallel_code ).get()           
                
                    for collation_code in collation_codes:
                        sigla = collation_code.strip().split()
                        vector = sigla.pop(0)
                    
                        for siglum_text in sigla:
                            siglum_components = siglum_text.split(":")
                            siglum_text = siglum_components[0]
                            corrector = None
                            if len(siglum_components) > 1:
                                corrector = int(siglum_components[1])

                            witness = get_witness_or_create_from_siglum_name( siglum_text )
                            for code, sublocation in zip(vector, sublocation_objects):      
                                witness.set_attestation(sublocation=sublocation, code=code, corrector=corrector, parallel=parallel)

                prev_location_data = location_data
                
    def import_witness_from_file(self, witness, path):
        with open(path) as file:        
            data = file.read().replace('\n', ' ')
        
            # Save Comments
            comments = re.findall('"(.*?)"', data)
        
            # Remove comments
            data = re.sub('".*?"','',data)
        
            locations = data.split("[")
            initial_data = locations.pop(0)
        
            prev_location_data = initial_data
            
            my_locations = self.locations.all()
            
            for location_index, location_data in enumerate(locations):
                components = re.search( "(.*)\](.*)", location_data )
                if  not components:
                    print("NO components")
                    sys.exit()
            
                sublocations = components.group(1).strip().split("|")
                parallels = components.group(2).strip()

                base_text = sublocations.pop(0).strip()
        
                location = my_locations[location_index]
                if location.base_text != base_text:
                    print("Mismatch base text:", location_index, base_text, location, location.id )
                    return

                if location.sublocation_set.count() != len(sublocations):
                    print("Mismatch sublocations:", location, location.id)
                    
                    for sublocation in location.sublocation_set.all():
                        print( sublocation.id, " ".join([str(reading) for reading in sublocation.reading_set.all()]) )
                    print("--")
                    for order, sublocation_text in enumerate(sublocations):
                        print(sublocation_text)
                    print()
                    return

                # HACK - this assumes that all the sublocation readings are the same as in the file
                sublocation_objects = location.sublocation_set.all()
                
                for parallel in re.findall('/*([a-z]?)\s*<(.*?)>', parallels):
                    parallel_code = parallel[0].strip()
                    collation_codes = parallel[1].strip().split("|")
                
                    parallel = None
                    if len(parallel_code) > 0:
                        parallel = self.parallels.filter( code=parallel_code ).get()           
                
                    for collation_code in collation_codes:
                        sigla = collation_code.strip().split()
                        vector = sigla.pop(0)
                    
                        for siglum_text in sigla:
                            # Search for this witness given in arguments for function
                            file_siglum, corrector = Siglum.get_with_corrector( siglum_text )
                            if not file_siglum or file_siglum.witness != witness:
                                continue
                            
                            for code, sublocation in zip(vector, sublocation_objects):      
                                witness.set_attestation(sublocation=sublocation, code=code, corrector=corrector, parallel=parallel)

                prev_location_data = location_data
                            

    def export(self, file=sys.stdout, binary=False):
        output = ""
        print("* %s %s ;" % (
            " ".join(["/%s" % parallel.code for parallel in self.parallels.all()]),
            " ".join(["~".join(witness.all_sigla_names()) for witness in self.witnesses.all()]),
            ), file=file )
        for suppression in self.suppressions.all():
            print(suppression, file=file)

        for location in self.locations.all():
            for verse_label in location.verse_labels.all():
                print(verse_label, file=file)
            for macro in location.macros.all():
                if macro.description:
                    print('" %s "' % macro.description, file=file )
                print(macro, file=file)
            
            print("{{}", file=file)
            print( "[ %s" % (location.base_text), file=file )
            sublocations = location.sublocation_set.all()
            for sublocation in sublocations:
                if binary:
                    for reading in sublocation.reading_set.all():
                        print(" |%s %s" % ( sublocation.weighting, reading.text ), file=file)                
                else:
                    print(" |%s %s" % ( sublocation.weighting, " ".join( [reading.text for reading in sublocation.reading_set.all()] )   ), file=file)
            print("]", file=file)
        
            if len(sublocations) == 0:
                continue
            parallels = location.get_parallels()
            for parallel in parallels:
                if parallel != None:
                    print("/"+parallel.code, file=file)
                print("<", file=file)
                codes_dict = defaultdict(list)

                for witness in Witness.objects.filter( attestation__sublocation__location=location, attestation__parallel=parallel ).distinct():

                    correctors = Attestation.objects.filter( sublocation=sublocation, witness=witness, parallel=parallel ).order_by('corrector').values('corrector').distinct()
                    for corrector in correctors:
                        corrector = corrector['corrector']
                        codes = ""                
                        for sublocation in sublocations:
                            attestation = Attestation.objects.filter( sublocation=sublocation, witness=witness, parallel=parallel, corrector=corrector ).first()
                            symbol = attestation.code if attestation else "?"
                            if binary:
                                for reading_index, reading in enumerate(sublocation.reading_set.all()):
                                    if not symbol.isdigit():
                                        codes += symbol
                                    else:
                                        if int(symbol) == reading_index+1:
                                            codes += "1"
                                        else:
                                            codes += "0"
                            else:
                                codes += symbol
                    
                        corrector_suffix = ":%d" % corrector if corrector != None else ""
                        witness_string = "%s%s" % (witness, corrector_suffix)
                        codes_dict[codes].append( witness_string )
                delimiter = ""
                for code in codes_dict:                
                    print(" %s %s %s " % (delimiter, code, " ".join(codes_dict[code]) ), file=file )
            
                    delimiter = "|"

                print(">", file=file)
        

            print("}", file=file)        

        
    