from django.db import models
from django.forms import ModelForm
import datetime
import django_tables2 as tables
from django.utils.html import format_html

collection_protocol_choices = (('1', 'P1'), ('2', 'P2'), ('3', 'P3'))
processing_protocol_choices = (('1', 'P1'), ('2', 'P2'), ('3', 'P3'))
collection_site_choices = (('1', 'S1'), ('2', 'S2'), ('3', 'S3'))


class test_results(models.Model):
    barcode = models.CharField(max_length=20, null=False, blank=False, primary_key=True,
                               unique=True)
    collection_site = models.CharField(max_length=20, null=False, blank=False, choices=collection_site_choices)
    collection_protocol = models.CharField(max_length=50, null=False, blank=False, choices=collection_protocol_choices)
    processing_protocol = models.CharField(max_length=50, null=False, blank=False, choices=processing_protocol_choices)
    technician = models.CharField(max_length=20, null=False, blank=False)
    lab = models.CharField(max_length=20, null=False, blank=False)
    institute = models.CharField(max_length=20, null=False, blank=False)
    collection_date = models.DateField(max_length=20, null=False, blank=False, default=datetime.date.today)
    processing_date = models.DateField(max_length=20, null=False, blank=False, default=datetime.date.today)
    machine_model = models.CharField(max_length=20, null=False, blank=False)
    reagents = models.CharField(max_length=100, null=False, blank=False)
    pcr_results_csv = models.FileField(null=False, blank=False, upload_to='documents/')
    pcr_platemap_csv = models.FileField(null=False, blank=False, upload_to='documents/')

    class Meta:
        indexes = [
            models.Index(fields=['barcode', 'collection_site', 'technician', 'lab']),
        ]


class test_resultsTable(tables.Table):

    class Meta:
        model = test_results
        template_name = 'django_tables2/bootstrap.html'


class ResultsForm(ModelForm):
    class Meta:
        model = test_results
        fields = ['barcode', 'collection_site', 'collection_protocol', 'processing_protocol', 'technician', 'lab',
                  'institute', 'collection_date', 'processing_date', 'machine_model', 'reagents', 'pcr_results_csv',
                  'pcr_platemap_csv']
