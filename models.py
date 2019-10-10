from django.db import models
#from dcodex_bible import BibleVerse

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

class Collation( models.Model ):
    parallels = models.ManyToManyField(Parallel)
    witnesses = models.ManyToManyField(Witness)
    locations = models.ManyToManyField(Location)
    suppressions = models.ManyToManyField(Suppression)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name
    
    
    

