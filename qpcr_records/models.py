from django.db import models
from django.forms import ModelForm
import datetime
import django_tables2 as tables

rna_extraction_protocol_choices = (('1', 'P1'), ('2', 'P2'), ('3', 'P3'))
qpcr_instrument_choices = (('1', 'BioRad CFX_384'), ('2', 'BioRad CFX_XXX'))


class test_results(models.Model):
    barcode = models.CharField(max_length=20, null=False, blank=False, default='X')
    sample_box_number = models.CharField(max_length=20, null=False, blank=False, default='X')
    sample_box_x_position = models.CharField(max_length=20, null=False, blank=False, default='X')
    sample_box_y_position = models.CharField(max_length=20, null=False, blank=False, default='X')

    plate_id = models.CharField(max_length=15, null=False, blank=False, default='X')
    sampling_plate_well = models.CharField(max_length=5, null=False, blank=False, default='X')
    sampling_date = models.DateField(max_length=20, null=False, blank=False, default=datetime.date.today)
    rna_extraction_protocol = models.CharField(max_length=50, null=False, blank=False,
                                               choices=rna_extraction_protocol_choices,
                                               default='1')

    qpcr_n1_well = models.CharField(max_length=5, null=False, blank=False, default='X')
    qpcr_n2_well = models.CharField(max_length=5, null=False, blank=False, default='X')
    qpcr_rp_well = models.CharField(max_length=5, null=False, blank=False, default='X')
    qpcr_instrument = models.CharField(max_length=50, null=False, blank=False, choices=qpcr_instrument_choices,
                                       default='1')

    technician = models.CharField(max_length=20, null=False, blank=False, default='X')
    lab = models.CharField(max_length=20, null=False, blank=False, default='X')
    institute = models.CharField(max_length=20, null=False, blank=False, default='X')

    pcr_results_csv = models.FileField(upload_to='documents/')
    pcr_platemap_csv = models.FileField(upload_to='documents/')

    class Meta:
        indexes = [
            models.Index(fields=['barcode', 'technician', 'sampling_date']),
        ]


class test_resultsTable(tables.Table):
    class Meta:
        model = test_results
        template_name = 'django_tables2/bootstrap.html'


class SamplingForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['sampling_date', 'rna_extraction_protocol', 'qpcr_instrument', 'technician', 'lab', 'institute']


class SamplingForm_v2(ModelForm):
    class Meta:
        model = test_results
        fields = ['sample_box_number', 'sample_box_x_position', 'sample_box_y_position', 'plate_id', 'sampling_plate_well']
