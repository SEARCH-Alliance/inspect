from django.db import models
from django.forms import ModelForm, HiddenInput, TextInput, CheckboxInput, ValidationError
import datetime
import django_tables2 as tables


sample_bag_is_stored_choices = ((True, True), (False, False))
sample_result_choices = (('', ''), ('Undetermined', 'Undetermined'), ('Invalid', 'Invalid'), ('Inconclusive', 'Inconclusive'),
                         ('Positive', 'Positive'), ('Negative', 'Negative'))
is_reviewed_choices = ((True, True), (False, False))
sample_release_choices = ((True, True), (False, False))
file_transfer_status_choices = (
    ('Complete', 'Complete'), ('Not Complete', 'Not Complete'))


class test_results(models.Model):
    # SAMPLE INFORMATION : MOST UPSTREAM INFORMATION TO CAPTURE
    barcode = models.CharField(max_length=20, null=False, default='')
    fake_name = models.CharField(max_length=60, null=False, default='')

    # SAMPLE PLATING LAB INFORMATION
    lrl_id = models.CharField(max_length=15, null=False, default='M6246109105', help_text='Lysis Reagent Lot #')
    ssp_id = models.CharField(max_length=15, null=False, default='', help_text='Sample Storage Plate (SSP)')
    ssp_well = models.CharField(max_length=3, null=False, default='')
    sampling_date = models.DateField(null=False, default=datetime.date.today().strftime('%m/%d/%Y'))
    sampling_time = models.TimeField(null=False, default=datetime.datetime.now().strftime("%H:%M:%S"))

    sep_id = models.CharField(max_length=15, null=False, default='', help_text='Scan or Enter Barcode of Sample Extraction Plate (SEP)')
    sep_well = models.CharField(max_length=3, null=False, default='')
    andersson_lab_frz_id = models.CharField(max_length=15, null=False, default='', help_text='Enter Sample Storage Freezer Number')
    personnel1_andersen_lab = models.CharField(max_length=25, null=False, default='')
    personnel2_andersen_lab = models.CharField(max_length=25, null=False, default='', help_text='Name of Assisting Technician')
    sample_bag_id = models.CharField(max_length=15, null=False, default='')
    sampling_plate_csv = models.URLField(max_length=300, null=False, default='')
    sample_bag_is_stored = models.BooleanField(default=True, choices=sample_bag_is_stored_choices)

    # RNA EXTRACTION LAB INFORMATION
    epm_id = models.CharField(max_length=15, null=False, default='', help_text='Enter EpMotion ID')
    rna_extract_kit_id = models.CharField(max_length=20, null=False, default='', help_text='Enter RNA extraction kit lot #')
    megabeads_id = models.CharField(max_length=20, null=False, default='', help_text='Enter Mag-Bind particles CNR Lot #')
    carrier_rna_id = models.CharField(max_length=20, null=False, default='', help_text='Enter Carrier RNA Lot #')
    kfr_id = models.CharField(max_length=20, null=False, default='', help_text='Enter KingFisher Number')
    rep_id = models.CharField(max_length=15, null=False, default='', help_text='Scan or Enter Barcode of RNA Elution Plate (REP)')
    rep_well = models.CharField(max_length=3, null=False, default='')
    rsp_id = models.CharField(max_length=15, null=False, default='', help_text='Scan or Enter Barcode of RNA Storage Plate (RSP)')
    rsp_well = models.CharField(max_length=3, null=False, default='')
    knight_lab_frz_id = models.CharField(max_length=15, null=False, default='', help_text='Enter RNA Storage Freezer Number')
    rwp_id = models.CharField(max_length=15, null=False, default='', help_text='Scan or Enter Barcode of RNA Working Plate (RWP)')
    rwp_well = models.CharField(max_length=3, null=False, default='')
    personnel_knight_lab = models.CharField( max_length=25, null=False, default='')
    re_date = models.DateField(null=False, default=datetime.date.today().strftime('%Y-%m-%d'))
    rna_extraction_time = models.TimeField(null=False, default=datetime.datetime.now().strftime("%H:%M:%S"))
    arraying_time = models.TimeField(null=False, default=datetime.datetime.now().strftime("%H:%M:%S"))
    ms2_lot_id = models.CharField(max_length=15, null=False, default='2003001', help_text='Enter MS2 Control Lot #')

    # QPCR LAB INFORMATION
    qrp_id = models.CharField(max_length=15, null=False, default='', help_text='Scan or Enter Barcode of qRTPCR Reaction Plate (QRP)')
    qrp_well = models.CharField(max_length=3, null=False, default='')
    probe_mix_id = models.CharField(max_length=15, null=False, default='', help_text='Enter qRTPCR Reaction Probe Mix Lot Number')
    enzyme_mix_id = models.CharField(max_length=15, null=False, default='2219127', help_text='Enter qRTPCR Reaction Enzyme Mix Lot Number')
    mhv_id = models.CharField(max_length=15, null=False, default='MHV-041', help_text='Enter Mosquito HV Number')
    qs5_id = models.CharField(max_length=15, null=False, default='', help_text='Enter QS5 Number')
    laurent_lab_frz_id = models.CharField(max_length=15, null=False, default='', help_text='Enter RNA Storage Freezer Number')
    personnel_laurent_lab = models.CharField(max_length=25, null=False, default='')
    personnel_qpcr_file_upload = models.CharField(max_length=25, null=False, default='')
    qpcr_date = models.DateField(null=False, default=datetime.date.today().strftime('%Y-%m-%d'))
    qpcr_reaction_time = models.TimeField(null=False, default=datetime.datetime.now().strftime("%H:%M:%S"))
    qpcr_file_upload_time = models.TimeField(null=False, default=datetime.datetime.now().strftime("%H:%M:%S"))

    # RESULTS INFORMATION
    ms2_ct_value = models.FloatField(null=False, default=-1)
    n_ct_value = models.FloatField(null=False, default=-1)
    orf1ab_ct_value = models.FloatField(null=False, default=-1)
    s_ct_value = models.FloatField(null=False, default=-1)
    decision_tree_results = models.CharField(max_length=15, null=False, default='Undetermined',
                                             choices=sample_result_choices)
    final_results = models.CharField(max_length=15, null=False, default='Undetermined', choices=sample_result_choices)
    is_reviewed = models.BooleanField(default=False, choices=is_reviewed_choices)

    qpcr_results_file = models.URLField(max_length=300, null=False, default='')
    eds_results_csv = models.URLField(max_length=300, null=False, default='')

    file_transfer_status = models.CharField(max_length=15, null=False, default='Not Complete',
                                            choices=file_transfer_status_choices)
    sample_release = models.BooleanField(default=False, choices=sample_release_choices)

    class Meta:
        indexes = [models.Index(fields=['barcode', 'fake_name', 'ssp_id', 'sep_id', 'rep_id', 'rsp_id', 'rwp_id', 'qrp_id'])]


# RESULT SEARCH COLUMNS TO DISPLAY
class SearchResultsTable(tables.Table):
    class Meta:
        model = test_results
        fields = ('barcode', 'sampling_date', 'ssp_id', 'ssp_well', 'sep_id', 'sep_well', 'sample_bag_id',
                  'sampling_plate_csv', 'rep_id', 'rep_well', 'rsp_id', 'rsp_well', 'rwp_id', 'rwp_well', 'qrp_id',
                  'qrp_well', 'ms2_ct_value', 'n_ct_value', 'orf1ab_ct_value', 's_ct_value', 'decision_tree_results',
                  'final_results', 'qpcr_results_file', 'sample_release')


# COLUMNS TO DISPLAY WHEN REVIEWING QPCR RESULTS
class ReviewTable(tables.Table):
    class Meta:
        model = test_results
        fields = ['barcode', 'fake_name', 'sep_id', 'rep_id', 'rwp_id', 'qrp_id', 'qrp_well', 'ms2_ct_value',
                  'n_ct_value', 'orf1ab_ct_value', 's_ct_value', 'decision_tree_results', 'final_results']


# COLUMNS TO DISPLAY WHEN MARKING SAMPLES FOR RELEASE
class SampleReleaseTable(tables.Table):
    class Meta:
        model = test_results
        fields = ['sampling_date', 'barcode', 'sep_id', 'rep_id', 'rwp_id', 'qrp_id', 'qrp_well', 'final_results']
        orderable = False


# SAMPLE PLATING START FORM
class LysisReagentLotForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['lrl_id', 'personnel2_andersen_lab']
        labels = {'lrl_id': 'Lysis Reagent Lot #', 'personnel2_andersen_lab': 'Assisting Technician Name'}


# SAMPLE EXTRACTION FORM TO CAPTURE SAMPLE BARCODE AND PLATE WELL
# It is assumed that the sample wells in extraction and storage plates will be identical.
# Sample well in storage plate is automatically set as the value as the well in extraction plate
class SampleStorageAndExtractionWellForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['barcode', 'ssp_well', 'sep_well']
        labels = {'barcode': 'Sample Barcode', 'ssp_well': 'Sample Storage Plate Well',
                  'sep_well': 'Sample Extraction Plate Well'}
        widgets = {'barcode': TextInput(attrs={'autofocus': 'autofocus'}), 'ssp_well':
                   HiddenInput(attrs={'readonly': True}), 'sep_well': HiddenInput(attrs={'readonly': True})}


# FORM TO CAPTURE EXTRACTION PLATE ID, STORAGE PLATE ID AND STORAGE BAG ID
class SampleStorageAndExtractionPlateForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['ssp_id', 'sep_id', 'sample_bag_id']
        labels = {'ssp_id': 'Sample Storage Plate Barcode', 'sep_id': 'Sample Extraction Plate Barcode',
                  'sample_bag_id': 'Sample Storage Bag'}

    def clean_ssp_id(self):
        ssp_id = self.cleaned_data['ssp_id']
        if test_results.objects.filter(ssp_id__iexact=ssp_id).exists():
            raise ValidationError("Sample storage plate ID already exists.", code='invalid')
        return ssp_id

    def clean_sep_id(self):
        sep_id = self.cleaned_data['sep_id']
        if test_results.objects.filter(sep_id__iexact=sep_id).exists():
            raise ValidationError("Sample extraction plate ID already exists.", code='invalid')
        return sep_id

    def clean_sample_bag_id(self):
        sample_bag_id = self.cleaned_data['sample_bag_id']
        if test_results.objects.filter(sample_bag_id__iexact=sample_bag_id).exists():
            raise ValidationError("Sample bag ID already exists.", code='invalid')
        return sample_bag_id


# FORM TO CAPTURE RNA EXTRACTION PLATE ID
# Needs a valid and existing sample extraction plate ID.
# The sample extraction plate ID and rna extraction plate ID will be linked using this form
class RNAExtractionPlateForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['sep_id', 'rep_id', 'kfr_id', 'ms2_lot_id',
                  'rna_extract_kit_id', 'megabeads_id', 'carrier_rna_id', 'ms2_lot_id']
        labels = {'sep_id': 'Sample Extraction Plate Barcode',
                  'rep_id': 'RNA Elution Plate Barcode',
                  'kfr_id': 'KingFisher ID', 'ms2_lot_id': 'MS2 Phage Lot #',
                  'rna_extract_kit_id': 'RNA Extraction Kit Lot #', 'megabeads_id': 'Mag-bind Particles CNR Lot #',
                  'carrier_rna_id': 'Carrier RNA Lot #'}


    def clean_sep_id(self):
        sep_id = self.cleaned_data['sep_id']
        if not test_results.objects.filter(sep_id__iexact=sep_id).exists():
            raise ValidationError("Sample extraction plate ID does not exist.", code='invalid')
        if test_results.objects.filter(sep_id__iexact=sep_id).exclude(rep_id='').exists():
            raise ValidationError(f"Sample extraction plate \"{sep_id}\" has already been assigned an RNA elution plate ID.")
        return sep_id

    def clean_rep_id(self):
        rep_id = self.cleaned_data['rep_id']
        if test_results.objects.filter(rep_id__iexact=rep_id).exists():
            raise ValidationError("RNA elution plate ID already exists.", code='invalid')
        return rep_id


# FORM TO CAPTURE QPCR REACTION PLATE ID
# Needs a valid and existing rna working plate ID.
# The rna working plate ID and qpcr reaction plate ID will be linked using this form
class QPCRStorageAndReactionPlateForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['rwp_id', 'qrp_id']
        labels = {'rwp_id': 'RNA Working Plate Barcode',
                  'qrp_id': 'qRT-PCR Plate Barcode'}

    def clean_rwp_id(self):
        rwp_id = self.cleaned_data['rwp_id']
        if not test_results.objects.filter(rwp_id__iexact=rwp_id).exists():
            raise ValidationError("RNA working plate ID does not exist.", code='invalid')
        if test_results.objects.filter(rwp_id__iexact=rwp_id).exclude(qrp_id='').exists():
            raise ValidationError(f"qRT-PCR reaction plate ID is already assigned to RNA working plate ID {rwp_id}.", code="invalid")
        return rwp_id

    def clean_qrp_id(self):
        qrp_id = self.cleaned_data['qrp_id']
        if test_results.objects.filter(qrp_id__iexact=qrp_id).exists():
            raise ValidationError("qRT-PCR reaction plate ID already exists.", code='invalid')
        return qrp_id


# FORM TO CHOOSE QPCR PLATE WHEN REVIEWING RESULTS
class SelectQRPPlateForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['qrp_id']
        labels = {'qrp_id': 'qRT-PCR Plate Barcode'}

    def clean_qrp_id(self):
        qrp_id = self.cleaned_data['qrp_id']
        if not test_results.objects.filter(qrp_id__iexact=qrp_id).exists():
            raise ValidationError(f"qRT-PCR reaction plate \"{qrp_id}\" does not exist.", code='invalid')

        if True in test_results.objects.filter(qrp_id__iexact=qrp_id).values_list('is_reviewed', flat=True):
            raise ValidationError(f"qRT-PCR reaction plate \"{qrp_id}\" has already been reviewed.", code='invalid')
        return qrp_id


# FORM TO SELECT BAG ID WHEN DISCARDING SAMPLES IN A BAG
class SelectBagForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['sample_bag_id']
        labels = {'sample_bag_id': 'Sample Bag ID'}

    def clean_sample_bag_id(self):
        sample_bag_id = self.cleaned_data['sample_bag_id']
        if not test_results.objects.filter(sample_bag_id__iexact=sample_bag_id).exists():
                raise ValidationError(f"Sample bag ID \"{sample_bag_id}\" does not exist.", code = 'invalid')

        return sample_bag_id
