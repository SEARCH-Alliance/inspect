from django.db import models
from django.forms import ModelForm
import datetime
import django_tables2 as tables

rna_extraction_protocol_choices = (('1', 'P1'), ('2', 'P2'), ('3', 'P3'))
qpcr_instrument_choices = (('1', 'BioRad CFX_384'), ('2', 'BioRad CFX_XXX'))


class test_results(models.Model):
    barcode = models.CharField(max_length=20, null=False, blank=False, default='X')
    fake_name = models.CharField(max_length=30, null=False, blank=False, default='X')

    plate_1_id = models.CharField(max_length=15, null=False, blank=False, default='X', help_text='Scan or Enter for 96-well Plate 1')
    plate_1_well = models.CharField(max_length=5, null=False, blank=False, default='X')
    sampling_date = models.DateField(max_length=20, null=False, blank=False, default=datetime.date.today)

    plate_2_id = models.CharField(max_length=15, null=False, blank=False, default='X',
                                  help_text='Scan or Enter Barcode of 96-well Storage Plate')
    plate_2_well = models.CharField(max_length=5, null=False, blank=False, default='X')
    rna_extraction_protocol = models.CharField(max_length=50, null=False, blank=False,
                                               choices=rna_extraction_protocol_choices,
                                               default='1')

    plate_3_id = models.CharField(max_length=15, null=False, blank=False, default='X',
                                  help_text='Scan or Enter Barcode of Elution Plate from KingFisher')
    plate_3_well = models.CharField(max_length=5, null=False, blank=False, default='X')

    plate_4_id = models.CharField(max_length=15, null=False, blank=False, default='X',
                                  help_text='Scan or Enter Barcode of Arraying EpMotion 394 Well Plate')
    plate_4_well = models.CharField(max_length=5, null=False, blank=False, default='X')

    plate_5_id = models.CharField(max_length=15, null=False, blank=False, default='X',
                                  help_text='Scan or Enter Barcode of qPCR back-up Plate')
    plate_5_well = models.CharField(max_length=5, null=False, blank=False, default='X')

    plate_6_id = models.CharField(max_length=15, null=False, blank=False, default='X',
                                  help_text='Scan or Enter Barcode of qPCR Reaction Plate')
    plate_6_well = models.CharField(max_length=5, null=False, blank=False, default='X')

    ms2_ct_value = models.FloatField(null=False, blank=False, default=0)
    ms2_ct_mean_value = models.FloatField(null=False, blank=False, default=0)
    ms2_ct_sd_value = models.FloatField(null=False, blank=False, default=0)

    n_ct_value = models.FloatField(null=False, blank=False, default=0)
    n_ct_mean_value = models.FloatField(null=False, blank=False, default=0)
    n_ct_sd_value = models.FloatField(null=False, blank=False, default=0)

    orf1ab_ct_value = models.FloatField(null=False, blank=False, default=0)
    orf1ab_ct_mean_value = models.FloatField(null=False, blank=False, default=0)
    orf1ab_ct_sd_value = models.FloatField(null=False, blank=False, default=0)

    s_ct_value = models.FloatField(null=False, blank=False, default=0)
    s_ct_mean_value = models.FloatField(null=False, blank=False, default=0)
    s_ct_sd_value = models.FloatField(null=False, blank=False, default=0)

    technician = models.CharField(max_length=20, null=False, blank=False, default='X')
    lab = models.CharField(max_length=20, null=False, blank=False, default='X')
    institute = models.CharField(max_length=20, null=False, blank=False, default='X')

    pcr_results_csv = models.URLField(max_length=300, null=False, blank=False, default='X')
    # pcr_results_csv = models.FileField(upload_to='documents/')
    # pcr_platemap_csv = models.FileField(upload_to='documents/')

    class Meta:
        indexes = [
            models.Index(fields=['barcode', 'technician', 'sampling_date', 'plate_1_id', 'plate_2_id', 'plate_3_id',
                                 'plate_4_id', 'plate_5_id', 'plate_6_id']),]


class test_resultsTable(tables.Table):
    class Meta:
        model = test_results
        template_name = 'django_tables2/bootstrap.html'


class Plate_1_2_Form(ModelForm):
    class Meta:
        model = test_results
        fields = ['plate_1_id', 'plate_2_id']


class Plate_3_Form(ModelForm):
    class Meta:
        model = test_results
        fields = ['plate_3_id']


class Plate_4_Form(ModelForm):
    class Meta:
        model = test_results
        fields = ['plate_4_id']


class Plate_5_Form(ModelForm):
    class Meta:
        model = test_results
        fields = ['plate_5_id']


class Plate_6_Form(ModelForm):
    class Meta:
        model = test_results
        fields = ['plate_6_id']


class Sampling_Form(ModelForm):
    class Meta:
        model = test_results
        fields = ['barcode', 'plate_1_well', 'plate_2_well']


class Extraction_Form(ModelForm):
    class Meta:
        model = test_results
        fields = ['barcode', 'plate_3_well']


class EpMotion384_Form(ModelForm):
    class Meta:
        model = test_results
        fields = ['barcode', 'plate_4_well']


class QPCR_Backup_Form(ModelForm):
    class Meta:
        model = test_results
        fields = ['barcode', 'plate_5_well']


class QPCR_Reaction_Form(ModelForm):
    class Meta:
        model = test_results
        fields = ['barcode', 'plate_5_well']


class qpcrResultUploadForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['pcr_results_csv']
