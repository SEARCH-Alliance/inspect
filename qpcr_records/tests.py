from django.test import TestCase

import datetime
from qpcr_records.models import personnel_list
from qpcr_records.models import test_results

from qpcr_records.models import SampleStorageAndExtractionPlateForm
from qpcr_records.models import RNAExtractionPlateForm
from qpcr_records.models import QPCRStorageAndReactionPlateForm
from qpcr_records.models import QPCRResultsUploadForm
from qpcr_records.models import SelectQRPPlateForm

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
		tr = test_results.objects.get(barcode="Default_Fields", fake_name="Default")
		self.assertTrue(isinstance(tr, test_results))
		
		# Andersson Lab Information
		self.assertEqual(tr.lrl_id, "M6246109105")

		# Knight Lab Information
		self.assertEqual(tr.ms2_lot_id, "2003001")
		
		# Laurent Lab Information
		self.assertEqual(tr.enzyme_mix_id, "2219127")
		self.assertEqual(tr.mhv_id, "MHV-041")

		# Results Information
		self.assertEqual(tr.ms2_ct_value, -1)
		self.assertEqual(tr.n_ct_value, -1)
		self.assertEqual(tr.orf1ab_ct_value, -1)
		self.assertEqual(tr.s_ct_value, -1)
		self.assertEqual(tr.decision_tree_results, "Undetermined")
		self.assertEqual(tr.is_reviewed, False)
		self.assertEqual(tr.file_transfer_status, "Not Complete")
		self.assertEqual(tr.sample_release, "No")
