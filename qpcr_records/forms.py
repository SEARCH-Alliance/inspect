from django import forms
from django.forms import ValidationError
from django.db.models import Q
from qpcr_records.models import test_results

sample_tracking_choice = [('Sample_Plated', 'Sample Plated into 96 well Plates'),
                          ('Sample_Stored', 'Sample Stored in -180'),
                          ('RNA_Extraction', 'RNA Extraction Performed'),
                          ('Sample_Arrayed', 'RNA Plated onto 384 well Plate'),
                          ('qPCR_Reaction', 'Sample Loaded for qPCR Reaction'),
                          ('Result_Generation', 'qPCR Result has been Recorded')]
result_choices = [('', ''), ('Undetermined', 'Undetermined'), ('Inconclusive', 'Inconclusive'), ('Positive', 'Positive'),
                  ('Negative', 'Negative'), ('Invalid', 'Invalid')]


# SEARCH FIELDS
class SearchForm(forms.Form):
    barcode = forms.CharField(max_length=30, label='Sample Barcode', required=False, initial='')
    sampling_date = forms.DateField(help_text='(MM/DD/YYYY)', required=False, initial='',
                                    widget=forms.DateInput(format='%m/%d/%Y'), input_formats=('%m/%d/%Y',))
    plate_id = forms.CharField(help_text='Enter a Plate Barcode', max_length=15, required=False, initial='')
    technician = forms.CharField(max_length=30, label=' Technician', required=False, initial='')
    final_results = forms.CharField(label='Final Result', required=False, widget=forms.Select(choices=result_choices), initial='')
    sample_bag_id = forms.CharField(help_text='Enter a Sample Bag Barcode', max_length=15, required=False, initial='')

    def clean(self):
        cleaned_data = self.cleaned_data
        if 'sampling_date' in cleaned_data.keys():
            cleaned_data['sampling_date'] = str(cleaned_data['sampling_date'])

        empty_count = 0
        for field_name, value in cleaned_data.items():
            if value == '' or value is None:
                empty_count += 1

        # All fields can't be empty
        if empty_count == len(cleaned_data):
            raise ValidationError("Enter at least one field to search records.", code="invalid")
        return cleaned_data


# FORM TO CAPTURE RNA EXTRACTION PLATE IDs WHEN MERGING PLATES INTO A SINGLE RNA WORKING PLATE
# Needs valid and existing rna extraction plate IDs
# All entered rna extraction palte IDs will be linked to a single rna extraction plate ID using this form
class ArrayingForm(forms.Form):
    epm_id = forms.CharField(max_length=15, label='EpMotion ID', help_text="Enter EpMotion ID")
    barcode1 = forms.CharField(max_length=30, label='First 96-Well Plate in Array Position B2', required=True)
    barcode2 = forms.CharField(max_length=30, label='Second 96-Well Plate in Array Position B3', required=False)
    barcode3 = forms.CharField(max_length=30, label='Third 96-Well Plate in Array Position B4', required=False)
    barcode4 = forms.CharField(max_length=30, label='Fourth 96-Well Plate in Array Position B5', required=False)
    rwp_id = forms.CharField(max_length=15, label='RNA Working Plate Barcode', help_text="Scan or Enter Barcode of RNA Working Plate (RWP)")

    def clean(self):
        barcode1 = self.cleaned_data['barcode1']
        barcode2 = self.cleaned_data['barcode2']
        barcode3 = self.cleaned_data['barcode3']
        barcode4 = self.cleaned_data['barcode4']

        barcodes = [barcode1, barcode2, barcode3, barcode4]

        errors = []
        for b, f in zip(barcodes, ['barcode1', 'barcode2', 'barcode3', 'barcode4']):
            if b == '':
                continue
            elif not test_results.objects.filter(rep_id__iexact=b).exists():
                errors.append((f, ValidationError(f"RNA extraction plate \"{b}\" does not exist.")))
            else:
                continue

        if test_results.objects.filter(rep_id__in=barcodes).exclude(rwp_id='').exists():
            raise ValidationError("One or more RNA elution plate IDs are already assigned to an RNA working plate.")

        barcodes_no_empty = [b for b in barcodes if b]
        if len(barcodes_no_empty) != len(set(barcodes_no_empty)):
            raise ValidationError("Duplicated RNA elution plate IDs not allowed.")

        for e in errors:
            self.add_error(*e)

        return self.cleaned_data

    def clean_rwp_id(self):
        rwp_id = self.cleaned_data['rwp_id']
        if test_results.objects.filter(rwp_id__iexact=rwp_id).exists():
            raise ValidationError("RNA working plate ID already exists.", code='invalid')
        return rwp_id


# FORM TO UPLOAD FILE CONTAINING EXPECTED BARCODES
class PlatemapUploadForm(forms.Form):
    platemap_file = forms.FileField(required=True)
    ssp_id = forms.CharField(max_length=30, label='Sample Storage Plate ID. Leave blank if no SSP', required=False)
    sep_id = forms.CharField(max_length=30, label='Sample Extraction Plate ID. Leave blank if no SEP', required=False)
    sample_bag_id = forms.CharField(max_length=30, label='Sample Storage Bag ID. Leave blank if no SSB', required=False)

    def clean_platemap_file(self):
        platemap_file = self.cleaned_data['platemap_file']

        # TODO validations
        # if not test_results.objects.filter(?).exists():
        #     raise ValidationError(f'File not uploaded. {barcodes_file.name}' ??, code="invalid")

        return platemap_file

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


# FORM TO CHOOSE QPCR PLATE FOR WHICH RESULTS FILE WILL BE UPLOADED
class QPCRResultsUploadForm(forms.Form):
    qpcr_results_file = forms.FileField(required=True)

    def clean_qpcr_results_file(self):
        qpcr_results_file = self.cleaned_data['qpcr_results_file']

        qrp_id = qpcr_results_file.name.split('.')[0]
        if not test_results.objects.filter(qrp_id=qrp_id).exists():
            raise ValidationError(f'File not uploaded. Plate \"{qrp_id}\" does not exist.', code="invalid")

        if test_results.objects.filter(~Q(decision_tree_results='Undetermined'), qrp_id=qrp_id):
            raise ValidationError(f'File not uploaded. Plate \"{qrp_id}\" already has data.', code="invalid")

        return qpcr_results_file

