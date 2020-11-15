from django.test import TestCase
from dcodex_carlson.models import Collation
import os
import difflib
import tempfile
import shutil

# Create your tests here.
class CollationModelTests(TestCase):

    def assert_files_identical( self, path1, path2, extension = "" ):
        """
        tests contents of two files are identical.
        Optional ability to append extension to both paths
        """    
        with open( path1+extension ) as file1:
            data1 = file1.readlines()
        with open( path2+extension ) as file2:
            data2 = file2.readlines()
        self.assertEqual(data1, data2)

    def compare_import_export(self, path):
        """
        tests roundtrip of importing a Carlson collation file and exporting it
        """
        package_dir = os.path.dirname(os.path.abspath(__file__))
        absolute_path = os.path.join(package_dir,path)
        
        print("Importing:", absolute_path )
        collation = Collation(name=os.path.basename(absolute_path) )
        collation.save()
        collation.import_from_file( absolute_path )
        
        # Save collation to file
        dirpath = tempfile.mkdtemp()
        tmp_filename = "tmp_file"
        output_path = os.path.join(dirpath,tmp_filename)
        print("Exporting to:", output_path )
        with open( output_path, "w" ) as output_file:
            collation.export( output_file )
            
        # Run prep
        os.system("prep "+output_path)
        
        # diff on output files with gold standard
        self.assert_files_identical( output_path, absolute_path, ".no" )
        self.assert_files_identical( output_path, absolute_path, ".tx" )
        self.assert_files_identical( output_path, absolute_path, ".vr" )        
        
        # Remove temp files
        shutil.rmtree(dirpath)


    def test_import_export_caesarean( self ):
        """
        tests roundtrip of importing Carlson's 'Caesarean' collation file and exporting it
        """
        return self.compare_import_export( '../dcodex_carlson/data/caes' )
        
    def test_import_export_galatians( self ):
        """
        tests roundtrip of importing Carlson's 'Galatians' collation file and exporting it
        """
        return self.compare_import_export( '../dcodex_carlson/data/gal' )        