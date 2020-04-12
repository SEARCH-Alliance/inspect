from django import forms

sample_tracking_choice = [('Sample_Received', 'Sample Received From RCH'),
                          ('Sample_Plated', 'Sample Plated into 96 well Plates'),
                          ('Sample_Stored', 'Sample Stored in -180'),
                          ('RNA_Extraction', 'RNA Extraction Performed'),
                          ('RNA_Stored', 'RNA Plate Stored'),
                          ('Sample_Arrayed', 'RNA Plated onto 384 well Plate'),
                          ('qPCR_BackUp', 'qPCR BackUp Stored'),
                          ('qPCR_Reaction', 'Sample Loaded for qPCR Reaction'),
                          ('Result_Generation', 'qPCR Result has been Recorded')]
result_choices = [('', ''), ('Undetermined', 'Undetermined'), ('Inconclusive', 'Inconclusive'), ('Postive', 'Positive'),
                  ('Negative', 'Negative'), ('Invalid', 'Invalid')]


class SearchRecords(forms.Form):
    barcode = forms.CharField(max_length=30, label='Sample Barcode', required=False, initial='')
    sampling_date = forms.DateField(help_text='(YYYY-MM-DD)', required=False, initial='',
                                    widget=forms.DateInput(format='%m/%d/%Y'),
                                    input_formats=('%m/%d/%Y',))
    plate_id = forms.CharField(help_text='Enter a Plate Barcode', max_length=15, required=False, initial='')
    technician = forms.CharField(max_length=30, label=' Technician', required=False, initial='')
    result = forms.CharField(label='Final Result', required=False, widget=forms.Select(choices=result_choices), initial='')


class ArrayingForm(forms.Form):
    barcode1 = forms.CharField(max_length=30, label='First 96-Well Plate and Plate into Array Position B2',
                               required=True)

    barcode2 = forms.CharField(max_length=30, label='Second 96-Well Plate and Plate into Array Position B3',
                               required=True)

    barcode3 = forms.CharField(max_length=30, label='Third 96-Well Plate and Plate into Array Position B4',
                               required=True)

    barcode4 = forms.CharField(max_length=30, label='Fourth 96-Well Plate and Plate into Array Position B5',
                               required=True)


class TrackSamplesForm(forms.Form):
    track_samples = forms.MultipleChoiceField(required=True, widget=forms.CheckboxSelectMultiple,
                                              choices=sample_tracking_choice)

