from django.db import models
from django.forms import ModelForm, HiddenInput, TextInput
import datetime
import django_tables2 as tables
from django.utils import timezone


class personnel_list(models.Model):
    technician_name = models.CharField(max_length=20, null=False, default='', primary_key=True)
    technician_lab = models.CharField(max_length=20, null=False, default='')
    technician_institute = models.CharField(max_length=20, null=False, default='')


sample_release_choices = (('Yes', 'Yes'), ('No', 'No'))
sample_result_choices = (('Undetermined', 'Undetermined'), ('Invalid', 'Invalid'), ('Inconclusive', 'Inconclusive'),
                         ('Positive', 'Positive'), ('Negative', 'Negative'))
file_transfer_status_choices = (('Complete', 'Complete'), ('Not Complete', 'Not Complete'))


class test_results(models.Model):
    # SAMPLE INFORMATION : MOST UPSTREAM INFORMATION TO CAPTURE
    barcode = models.CharField(max_length=20, null=False, default='')
    fake_name = models.CharField(max_length=30, null=False, default='')

    # ANDERSSON LAB INFORMATION
    lrl_id = models.CharField(max_length=15, null=False, default='',
                              help_text='Lysis Reagent Lot #')
    ssp_id = models.CharField(max_length=15, null=False, default='',
                              help_text='Sample Storage Plate (SSP)')
    ssp_well = models.CharField(max_length=3, null=False, default='')
    sampling_date = models.DateField(null=False, default=datetime.date.today().strftime('%Y-%m-%d'))

    sep_id = models.CharField(max_length=15, null=False, default='',
                              help_text='Scan or Enter Barcode of Sample Extraction Plate (SEP)')
    sep_well = models.CharField(max_length=3, null=False, default='')
    andersson_lab_frz_id = models.CharField(max_length=15, null=False, default='',
                                            help_text='Enter Sample Storage Freezer Number')
    personnel1_andersen_lab = models.CharField(max_length=25, null=False, default='')
    personnel2_andersen_lab = models.CharField(max_length=25, null=False, default='',
                                               help_text='Name of Assisting Technician')
    sample_bag_id = models.CharField(max_length=10, null=False, default='')

    # KNIGHT LAB INFORMATION
    ms2_lot_id = models.CharField(max_length=15, null=False, default='',
                                  help_text='Enter MS2 Control Lot #')
    epm_id = models.CharField(max_length=15, null=False, default='', help_text='Enter EpMotion ID')
    rna_extract_reagent_ids = models.CharField(max_length=200, null=False, default='',
                                               help_text='Enter list of RNA extraction reagent IDs')
    kfr_id = models.CharField(max_length=15, null=False, default='', help_text='Enter KingFisher Number')
    rep_id = models.CharField(max_length=15, null=False, default='',
                              help_text='Scan or Enter Barcode of RNA Elution Plate')
    rep_well = models.CharField(max_length=3, null=False, default='')
    rsp_id = models.CharField(max_length=15, null=False, default='',
                              help_text='Scan or Enter Barcode of RNA Storage Plate')
    rsp_well = models.CharField(max_length=2, null=False, default='')
    knight_lab_frz_id = models.CharField(max_length=15, null=False, default='',
                                         help_text='Enter RNA Storage Freezer Number')
    rwp_id = models.CharField(max_length=15, null=False, default='',
                              help_text='Scan or Enter Barcode of RNA Working Plate')
    rwp_well = models.CharField(max_length=3, null=False, default='')
    personnel_knight_lab = models.CharField(max_length=25, null=False, default='')
    re_date = models.DateField(null=False, default=datetime.date.today().strftime('%Y-%m-%d'))

    # LAURENT LAB INFORMATION
    qsp_id = models.CharField(max_length=15, null=False, default='',
                              help_text='Scan or Enter Barcode of qPCR_Storage Plate')
    qsp_well = models.CharField(max_length=3, null=False, default='')
    qrp_id = models.CharField(max_length=15, null=False, default='',
                              help_text='Scan or Enter Barcode of qRTPCR Reaction Plate')
    qrp_well = models.CharField(max_length=3, null=False, default='')
    probe_mix_id = models.CharField(max_length=15, null=False, default='',
                                    help_text='Enter qRTPCR Reaction Probe Mix Lot Number')
    enzyme_mix_id = models.CharField(max_length=15, null=False, default='',
                                     help_text='Enter qRTPCR Reaction Enzyme Mix Lot Number')
    mhv_id = models.CharField(max_length=15, null=False, default='',
                              help_text='Enter Mosquito HV Number')
    qs5_id = models.CharField(max_length=15, null=False, default='',
                              help_text='Enter QS5 Number')
    laurent_lab_frz_id = models.CharField(max_length=15, null=False, default='',
                                          help_text='Enter RNA Storage Freezer Number')
    personnel_laurent_lab = models.CharField(max_length=25, null=False, default='')
    qpcr_date = models.DateField(null=False, default=datetime.date.today().strftime('%Y-%m-%d'))

    # RESULTS INFORMATION
    ms2_ct_value = models.FloatField(null=False, default=-1)
    n_ct_value = models.FloatField(null=False, default=-1)
    orf1ab_ct_value = models.FloatField(null=False, default=-1)
    s_ct_value = models.FloatField(null=False, default=-1)
    decision_tree_results = models.CharField(max_length=15, null=False, default='Undetermined',
                                             choices=sample_result_choices)
    final_results = models.CharField(max_length=15, null=False, default='Undetermined', choices=sample_result_choices)

    pcr_results_csv = models.URLField(max_length=300, null=False, default='')
    eds_results_csv = models.URLField(max_length=300, null=False, default='')

    file_transfer_status = models.CharField(max_length=15, null=False, default='Not Complete',
                                            choices=file_transfer_status_choices)
    sample_release = models.CharField(max_length=15, null=False, default='No', choices=sample_release_choices)

    class Meta:
        indexes = [
            models.Index(fields=['barcode', 'ssp_id', 'sep_id', 'rep_id', 'rsp_id', 'rwp_id', 'qrp_id']), ]


class test_resultsTable(tables.Table):
    class Meta:
        model = test_results
        fields = (
            'barcode', 'ssp_id', 'ssp_well', 'sampling_date', 'sep_id', 'sep_well', 'rep_id', 'rep_well', 'rsp_id',
            'rsp_well', 'rwp_id', 'rwp_well', 'qrp_id', 'qrp_well', 'ms2_ct_value', 'n_ct_value',
            'orf1ab_ct_value', 's_ct_value', 'decision_tree_results', 'final_results', 'pcr_results_csv',
            'sample_release')


# class BarcodeScanningTable(tables.Table):
#     class Meta:
#         model = test_results
#         fields = ('barcode')


class LysisReagentLotForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['lrl_id']
        labels = {'lrl_id': 'Lysis Reagent Lot #'}


class SampleStorageAndExtractionWellForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['barcode', 'ssp_well', 'sep_well']
        labels = {'barcode': 'Sample Barcode', 'ssp_well': 'Sample Storage Plate Well',
                  'sep_well': 'Sample Extraction Plate Well'}
        widgets = {'barcode': TextInput(attrs={'autofocus': 'autofocus'}), 'ssp_well':
            HiddenInput(attrs={'readonly': True}), 'sep_well': HiddenInput(attrs={'readonly': True})}


class SampleStorageAndExtractionPlateForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['ssp_id', 'sep_id', 'sample_bag_id']
        labels = {'ssp_id': 'Sample Storage Plate Barcode', 'sep_id': 'Sample Extraction Plate Barcode',
                  'sample_bag_id': 'Sample Storage Bag'}


class RNAExtractionPlateForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['rep_id']
        labels = {'rep_id': 'RNA Extraction Plate Barcode'}


class MS2LotForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['ms2_lot_id']
        labels = {'ms2_lot_id': 'MS2 Phage Lot #'}


class RNAStorageAndWorkingPlateForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['rwp_id', 'rsp_id']
        labels = {'rwp_id': 'RNA Working Plate Barcode', 'rsp_id': 'RNA Storage Plate Barcode'}


class QPCRStorageAndReactionPlateForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['qsp_id', 'qrp_id']
        labels = {'qsp_id': 'qRDP-PCR Storage Plate Barcode', 'qrp_id': 'qRT-PCR Plate Barcode'}


class qpcrResultUploadForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['pcr_results_csv']
