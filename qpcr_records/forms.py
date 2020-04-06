from django import forms

sample_tracking_choice = [('Sample_Plated', 'Sample Plated into 96 well Plates'),
                          ('Sample_Stored', 'Sample Stored in -180'), ('RNA_Extraction', 'RNA Extraction Performed'),
                          ('Sample_Arrayed', 'Sample Plated into 384 well Plate'), ('qPCR_BackUp', 'qPCR BackUp Stored'),
                          ('qPCR_Reaction', 'Sample Loaded for qPCR Reaction')]


class SearchRecords(forms.Form):
    barcode = forms.CharField(max_length=30, label='Sample Barcode', required=False, initial='', widget=forms.TextInput(
        attrs={'placeholder': 'Enter Sample Barcode To Search By', 'size': 35}))
    fake_name = forms.CharField(max_length=30, label='Fake Name', required=False, initial='', widget=forms.TextInput(
        attrs={'placeholder': 'Enter Fake Name To Search By', 'size': 35}))
    technician = forms.CharField(max_length=30, label='Lab Technician Name', required=False, initial='',
                                 widget=forms.TextInput(
                                     attrs={'placeholder': 'Enter Lab Technician Name To Search By', 'size': 35}))
    lab = forms.CharField(max_length=30, label='Lab', required=False, initial='', widget=forms.TextInput(
        attrs={'placeholder': 'Enter Name of Lab To Search By', 'size': 35}))
    sampling_date = forms.DateField(help_text='(YYYY-MM-DD)', required=False, initial='',
                                    widget=forms.DateInput(format='%m/%d/%Y'),
                                    input_formats=('%m/%d/%Y',))
    plate_1_id = forms.CharField(help_text='Enter Sampling Plate Barcode', max_length=15, required=False, initial='')
    plate_2_id = forms.CharField(help_text='Enter Sample Storage Plate Barcode', max_length=15, required=False, initial='')
    plate_3_id = forms.CharField(help_text='Enter KingFisher Elution Plate Barcode', max_length=15, required=False, initial='')
    plate_4_id = forms.CharField(help_text='Enter Arrayed 384-Well Plate Barcode', max_length=15, required=False, initial='')
    plate_5_id = forms.CharField(help_text='Enter qPCR BackUp Plate Barcode', max_length=15, required=False, initial='')
    plate_6_id = forms.CharField(help_text='Enter qPCR Reaction Plate Barcode', max_length=15, required=False, initial='')


class ArrayingForm(forms.Form):
    barcode1 = forms.CharField(max_length=30, label='First 96-Well Plate', required=True, widget=forms.TextInput(
        attrs={'placeholder': 'Scan or Enter Barcode of First 96-Well Plate', 'size': 35}))
    barcode2 = forms.CharField(max_length=30, label='Second 96-Well Plate', required=True, widget=forms.TextInput(
        attrs={'placeholder': 'Scan or Enter Barcode of Second 96-Well Plate', 'size': 35}))
    barcode3 = forms.CharField(max_length=30, label='Third 96-Well Plate', required=True, widget=forms.TextInput(
        attrs={'placeholder': 'Scan or Enter Barcode of Third 96-Well Plate', 'size': 35}))
    barcode4 = forms.CharField(max_length=30, label='Third 96-Well Plate', required=True, widget=forms.TextInput(
        attrs={'placeholder': 'Scan or Enter Barcode of Third 96-Well Plate', 'size': 35}))


class TrackSamplesForm(forms.Form):
    track_samples = forms.MultipleChoiceField(required=True, widget=forms.CheckboxSelectMultiple,
                                                choices=sample_tracking_choice)
