from django.test import TestCase

# Models that we create in the database
from qpcr_records.models import personnel_list
from qpcr_records.models import test_results

# Import the Model Forms that we validate with clean functions
from django.forms import ValidationError
from qpcr_records.models import *

######################################################################
# Models test
######################################################################

class PersonnelListTest(TestCase):
	def setUp(self):
		"""Create two personnel: one with default parameters, one with params filled"""
		personnel_list.objects.create(technician_name="Default_Fields")
		personnel_list.objects.create(technician_name="John Doe", 
			technician_lab="John Doe", 
			technician_institute="UCSD")
		
	def test_default_personnel_creation(self):
		"""Test if default parameters are set properly"""
		p = personnel_list.objects.get(technician_name="Default_Fields")
		self.assertTrue(isinstance(p, personnel_list))
		self.assertEqual(p.technician_name, "Default_Fields")
		self.assertEqual(p.technician_lab, "")
		self.assertEqual(p.technician_institute, "")

	def test_personnel_creation(self):
		"""Test if personnel fields are set properly"""
		p = personnel_list.objects.get(technician_name="John Doe")
		self.assertTrue(isinstance(p, personnel_list))
		self.assertEqual(p.technician_name, "John Doe")
		self.assertEqual(p.technician_lab, "John Doe")
		self.assertEqual(p.technician_institute, "UCSD")

class TestResultsTest(TestCase):
	def setUp(self):
		"""Create a test result entry with mostly default parameters"""
		test_results.objects.create(barcode="Default_Fields", fake_name="Default")

	def test_default_test_results_creation(self):
		"""Test if non-date default parameters are set properly"""
		f = test_results.objects.get(barcode="Default_Fields", fake_name="Default")
		self.assertTrue(isinstance(f, test_results))
		
		# Andersson Lab Information
		self.assertEqual(f.lrl_id, "M6246109105")

		# Knight Lab Information
		self.assertEqual(f.ms2_lot_id, "2003001")
		
		# Laurent Lab Information
		self.assertEqual(f.enzyme_mix_id, "2219127")
		self.assertEqual(f.mhv_id, "MHV-041")

		# Results Information
		self.assertEqual(f.ms2_ct_value, -1)
		self.assertEqual(f.n_ct_value, -1)
		self.assertEqual(f.orf1ab_ct_value, -1)
		self.assertEqual(f.s_ct_value, -1)
		self.assertEqual(f.decision_tree_results, "Undetermined")
		self.assertEqual(f.is_reviewed, False)
		self.assertEqual(f.file_transfer_status, "Not Complete")
		self.assertEqual(f.sample_release, "No")

######################################################################
# ModelForms test
######################################################################

class TestSampleStoragenAndExtractionPlateForm(TestCase):
    def setUp(self):
        """Create a test result entry with sample storage and extraction info"""
        test_results.objects.create(ssp_id="SSP1", sep_id="SEP1", sample_bag_id="SB1")

    def test_sample_valid(self):
        """Test if new sample storage and extraction info can be added"""
        f = SampleStorageAndExtractionPlateForm(dict(ssp_id="SSP2", sep_id="SEP2", sample_bag_id="SB2"))
        self.assertEqual(len(f.errors),0)
        self.assertTrue(f.is_valid()) # should be a valid entry without errors

    def test_ssp_repeat(self):
        """Test if duplicate Sample Storage Plates are detected"""
        f = SampleStorageAndExtractionPlateForm(dict(ssp_id="SSP1", sep_id="SEP2", sample_bag_id="SB2"))
        self.assertEqual(len(f.errors),1) # duplicate SSP1
        self.assertRaises(ValidationError) 

    def test_sep_repeat(self):
        """Test if duplicate Sample Extraction Plates are detected"""
        f = SampleStorageAndExtractionPlateForm(dict(ssp_id="SSP2", sep_id="SEP1", sample_bag_id="SB2"))
        self.assertEqual(len(f.errors),1) # duplicate SEP1
        self.assertRaises(ValidationError) 

    def test_sb_repeat(self):
        """Test if duplicate Sample Extraction Plates are detected"""
        f = SampleStorageAndExtractionPlateForm(dict(ssp_id="SSP2", sep_id="SEP2", sample_bag_id="SB1"))
        self.assertEqual(len(f.errors),1) # duplicate SB1
        self.assertRaises(ValidationError) 

    def test_ssp_sep_repeat(self):
        """Test if duplicate Sample Storage Plate and Extraction plate are detected"""
        f = SampleStorageAndExtractionPlateForm(dict(ssp_id="SSP1", sep_id="SEP1", sample_bag_id="SB2"))
        self.assertEqual(len(f.errors),2) # duplicate SSP1 and SEP1

    def test_ssp_sb_repeat(self):
        """Test if duplicate Sample Storage Plate and Sample Bag are detected"""
        f = SampleStorageAndExtractionPlateForm(dict(ssp_id="SSP1", sep_id="SEP2", sample_bag_id="SB1"))
        self.assertEqual(len(f.errors),2) # duplicate SSP1 and SB1

    def test_sep_sb_repeat(self):
        """Test if duplicate Sample Extraction Plate and Sample Bag are detected"""
        f = SampleStorageAndExtractionPlateForm(dict(ssp_id="SSP2", sep_id="SEP1", sample_bag_id="SB1"))
        self.assertEqual(len(f.errors),2) # duplicate SEP1 and SB1

class TestRNAExtractionPlateForm(TestCase):
    def setUp(self):
        """Create a test result entry with RNA extraction info"""
        test_results.objects.create(sep_id="SEP1",rep_id="REP1") # sep with rep already added
        test_results.objects.create(sep_id="SEP2")               # sep with rep not added yet

    def test_rna_extraction_valid(self):
        """Test if new RNA extraction information can be added for a plate (SEP2)"""
        f = RNAExtractionPlateForm(dict(sep_id="SEP2",rep_id="REP2",
            # The KingFisherID, MS2 Lot Number, RNA Extraction Kit ID, 
            # Megabeads ID, and Carrier RNA ID are required entires
            kfr_id="KFR",ms2_lot_id="MS2",rna_extract_kit_id="KIT",
            megabeads_id="MEGA",carrier_rna_id="CARRIER"))
        
        self.assertEqual(len(f.errors),0)

    ##### Test all of the mandatory fields that need to be included 
    ##### (all of the lot numbers for different extraction kits and machines)

    def test_kfr_id(self):
        """Test if an error is called when KingFisherID is omitted"""
        f = RNAExtractionPlateForm(dict(sep_id="SEP2",rep_id="REP2",
            ms2_lot_id="MS2",rna_extract_kit_id="KIT",
            megabeads_id="MEGA",carrier_rna_id="CARRIER"))
        self.assertEqual(len(f.errors),1)

    def test_ms2_id(self):
        """Test if an error is called when MS2 Lot Number is omitted"""
        f = RNAExtractionPlateForm(dict(sep_id="SEP2",rep_id="REP2",
            kfr_id="KFR",rna_extract_kit_id="KIT",
            megabeads_id="MEGA",carrier_rna_id="CARRIER"))
        self.assertEqual(len(f.errors),1)

    def test_rna_extract_kit_id(self):
        """Test if an error is called when RNA Extraction Kit Lot Number is omitted"""
        f = RNAExtractionPlateForm(dict(sep_id="SEP2",rep_id="REP2",
            kfr_id="KFR",ms2_lot_id="MS2",
            megabeads_id="MEGA",carrier_rna_id="CARRIER"))
        self.assertEqual(len(f.errors),1)

    def test_megabeads_id(self):
        """Test if an error is called when Megabeads ID is omitted"""
        f = RNAExtractionPlateForm(dict(sep_id="SEP2",rep_id="REP2",
            kfr_id="KFR",ms2_lot_id="MS2",rna_extract_kit_id="KIT",
            carrier_rna_id="CARRIER"))
        self.assertEqual(len(f.errors),1)

    def test_carrier_rna_id(self):
        """Test if an error is called when Carrier RNA ID is omitted"""
        f = RNAExtractionPlateForm(dict(sep_id="SEP2",rep_id="REP2",
            kfr_id="KFR",ms2_lot_id="MS2",rna_extract_kit_id="KIT",
            megabeads_id="MEGA"))
        self.assertEqual(len(f.errors),1)

    ##### Test that we don't add duplicate entries to the database or conflicting entries

    def test_sep_multiple_rep(self):
        """Test if duplicate Sample Extraction plate is detected"""
        f = RNAExtractionPlateForm(dict(sep_id="SEP1",rep_id="REP2",
            kfr_id="KFR",ms2_lot_id="MS2",rna_extract_kit_id="KIT",
            megabeads_id="MEGA",carrier_rna_id="CARRIER"))
        self.assertEqual(len(f.errors),1)
        self.assertRaises(ValidationError)

    def test_sep_dne_rep(self):
        """Test if Sample Extraction plate to associate with a RNA Elution plate does not exist"""
        f = RNAExtractionPlateForm(dict(sep_id="SEP3",rep_id="REP3",
            kfr_id="KFR",ms2_lot_id="MS2",rna_extract_kit_id="KIT",
            megabeads_id="MEGA",carrier_rna_id="CARRIER"))
        self.assertEqual(len(f.errors),1)
        self.assertRaises(ValidationError)

    def test_rep_multiple(self):
        """Test if duplicate RNA Elution plates are detected"""
        f = RNAExtractionPlateForm(dict(sep_id="SEP2",rep_id="REP1",
            kfr_id="KFR",ms2_lot_id="MS2",rna_extract_kit_id="KIT",
            megabeads_id="MEGA",carrier_rna_id="CARRIER"))
        self.assertEqual(len(f.errors),1)
        self.assertRaises(ValidationError)        

class TestQPCRStorageAndReactionPlateForm(TestCase):
    def setUp(self):
        test_results.objects.create(rwp_id="RWP1",qrp_id="QRP1") # rwp with qrp added
        test_results.objects.create(rwp_id="RWP2")               # rwp with qrp not added yet

    def test_qpcr_reaction_valid(self):
        """Test if new qPCR reaction information can be added for a plate (RWP2)"""
        f = QPCRStorageAndReactionPlateForm(dict(rwp_id="RWP2",qrp_id="QRP2"))
        self.assertEqual(len(f.errors),0)

    def test_rwp_dne(self):
        """Test if RNA Working Plate to associate with a qPCR Reaction plate does not exist"""
        f = QPCRStorageAndReactionPlateForm(dict(rwp_id="RWP3",qrp_id="QRP3"))
        self.assertEqual(len(f.errors),1)
        self.assertRaises(ValidationError)

    def test_rep_multiple_qrp(self):
        """Test if multiple qPCR Reaction plates are detected to associate with a single RNA Working plate"""
        f = QPCRStorageAndReactionPlateForm(dict(rwp_id="RWP1",qrp_id="QRP2"))
        self.assertEqual(len(f.errors),1)
        self.assertRaises(ValidationError)

    def test_qrp_multiple(self):
        """Test if duplicate qPCR Reaction plates are detected"""
        f = QPCRStorageAndReactionPlateForm(dict(rwp_id="RWP2",qrp_id="QRP1"))
        self.assertEqual(len(f.errors),1)
        self.assertRaises(ValidationError)