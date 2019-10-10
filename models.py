from django.db import models
#from dcodex_bible import BibleVerse
import re
import sys, os
from collections import defaultdict

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
    def __str__(self):
        siglum = self.siglum_set.first()
        if siglum:
            return str(siglum)
        return str(self.intf_id)
    class Meta:
        verbose_name_plural = 'Witnesses'
    def all_sigla_names(self):
        return [str(siglum) for siglum in self.siglum_set.all()]


class Siglum(models.Model):
    witness = models.ForeignKey( Witness, on_delete=models.CASCADE )
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = 'Sigla'
    
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


class Location(models.Model):
    verse_labels = models.ManyToManyField(VerseLabel)
    base_text = models.CharField(max_length=200)
    macros = models.ManyToManyField( Macro )
    
    def __str__(self):
        return self.base_text
    
class SubLocation(models.Model):
    location = models.ForeignKey( Location, on_delete=models.CASCADE )
    order    = models.IntegerField( )
    def __str__(self):
        return "%s:%d" % (str(self.location), self.order)
    class Meta:
        ordering = ['order']
    
class Reading(models.Model):
    sublocation = models.ForeignKey( SubLocation, on_delete=models.CASCADE )
    text = models.CharField(max_length=200)
    order = models.IntegerField( )
    def __str__(self):
        return self.text
    class Meta:
        ordering = ['order']

    
class Attestation( models.Model ):
    sublocation = models.ForeignKey( SubLocation, on_delete=models.CASCADE )
    code      = models.CharField(max_length=1)
    witness   = models.ForeignKey( Witness, on_delete=models.CASCADE )
    corrector = models.IntegerField( default=None, null=True )
    parallel  = models.ForeignKey( Parallel, on_delete=models.SET_DEFAULT, default=None, null=True )
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


def make_greek_unicode(text):
    return text.strip()
    
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
                    print("Parallel:", parallel)
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
                    parallel, created = Parallel.objects.get_or_create( code=parallel_code )                
            
                sigla_names = match[1].split()
            
                for siglum_name in sigla_names:
                    witness = get_witness_or_create_from_siglum_name( siglum_name )
                    suppression = Suppression(parallel=parallel, witness=witness)
                    suppression.save()
                    print(suppression)
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
        
                location = Location(base_text=make_greek_unicode(base_text))
                location.save()
                self.locations.add(location)     
            
        
                print("-----------")        
                macro_matches = re.findall("/*([a-z])* =([\-\+]*) (.*?);", prev_location_data)
                for match in macro_matches:
                    parallel = None
                    parallel_code = match[0]
                    if len(parallel_code) > 0:
                        parallel, created = Parallel.objects.get_or_create( code=parallel_code )                
                
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
                    print(macro)
                    location.macros.add(macro)
                
                verse_matches = re.findall("/*([a-z])* @ ([^\s]+)", prev_location_data)
                for match in verse_matches:
                    parallel = None
                    parallel_code = match[0]
                    if len(parallel_code) > 0:
                        parallel, created = Parallel.objects.get_or_create( code=parallel_code )                
                
                    verse_ref = match[1]
                
                    verse_label = VerseLabel( reference=verse_ref, parallel=parallel )
                    verse_label.save()                

                    location.verse_labels.add(verse_label)
                    print(verse_label)
                
                print("Base:", base_text)
                print("Sublocations:", sublocations)
                print( "Parallels:", parallels )     

            
                sublocation_objects = []
                for order, sublocation_text in enumerate(sublocations):
                    sublocation = SubLocation( location=location, order=order )
                    sublocation.save()
                    sublocation_objects.append(sublocation)
                
                    readings = sublocation_text.strip().split()
                    for reading_index, reading in enumerate( readings ):
                        reading = Reading( sublocation=sublocation, text=make_greek_unicode(reading), order=reading_index+1 )
                        reading.save()
            
                for parallel in re.findall('(.*?)<(.*?)>', parallels):
                    parallel_code = parallel[0].strip()
                    collation_codes = parallel[1].strip().split("|")
                
                    print("Parallel:", parallel_code)
                    parallel = None
                    if len(parallel_code) > 0:
                        parallel, created = Parallel.objects.get_or_create( code=parallel_code )
                
                    for collation_code in collation_codes:
                        sigla = collation_code.strip().split()
                        vector = sigla.pop(0)
                    
                        print("Vector:", vector)
                        print("Sigla:", sigla)
                    

                        
                        for siglum_text in sigla:
                            siglum_components = siglum_text.split(":")
                            siglum_text = siglum_components[0]
                            corrector = None
                            if len(siglum_components) > 1:
                                corrector = int(siglum_components[1])

                            witness = get_witness_or_create_from_siglum_name( siglum_text )
                            for code, sublocation in zip(vector, sublocation_objects):                    
                                attestation = Attestation( witness=witness, sublocation=sublocation, code=code, corrector=corrector, parallel=parallel )
                                attestation.save()

                prev_location_data = location_data
                            

    def export(self):
        print("* %s %s ;" % (
            " ".join(["/%s" % parallel.code for parallel in self.parallels.all()]),
            " ".join(["~".join(witness.all_sigla_names()) for witness in self.witnesses.all()]),
            ) )
        for suppression in self.suppressions.all():
            print(suppression)

        for location in self.locations.all():
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

        
    