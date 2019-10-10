from dcodex_carlson.models import *
import re
import sys, os
#https://django-extensions.readthedocs.io/en/latest/runscript.html

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
    
    if len(args) == 0:
        print("Usage: --script-args staleonly")
        return
    filename = args[0]
    with open(filename) as file:
        collation = Collation(name=os.path.basename(filename) )
        collation.save()
        
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
                collation.parallels.add(parallel)
            else:
                sigla = ms.split("~")
                witness = None
                for siglum_name in sigla:
                    if witness == None:                
                        witness = get_witness_or_create_from_siglum_name(siglum_name)
                        collation.witnesses.add(witness)                        
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
                collation.suppressions.add( suppression )
        
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
            collation.locations.add(location)     
            
        
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
                        
