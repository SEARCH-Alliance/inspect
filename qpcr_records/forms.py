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


class SearchRecords(forms.Form):
    barcode = forms.CharField(max_length=30, label='Sample Barcode', required=False, initial='', widget=forms.TextInput(
        attrs={'placeholder': 'Enter Sample Barcode To Search By', 'size': 35}))
    sampling_date = forms.DateField(help_text='(YYYY-MM-DD)', required=False, initial='',
                                    widget=forms.DateInput(format='%m/%d/%Y'),
                                    input_formats=('%m/%d/%Y',))
    ssp_id = forms.CharField(help_text='Enter Sample Storage Plate (SSP) Barcode', max_length=15, required=False,
                             initial='')
    sep_id = forms.CharField(help_text='Enter Sample Extraction Plate (SEP) Barcode', max_length=15, required=False,
                             initial='')
    rep_id = forms.CharField(help_text='Enter RNA Elution Plate (REP) Barcode', max_length=15, required=False,
                             initial='')
    rsp_id = forms.CharField(help_text='Enter RNA Storage Plate (RSP) Barcode', max_length=15, required=False,
                             initial='')
    rwp_id = forms.CharField(help_text='Enter RNA Working Plate (RWP) Barcode', max_length=15, required=False,
                             initial='')
    qrp_id = forms.CharField(help_text='Enter qRT-PCR Reaction Plate (QRP) Barcode', max_length=15, required=False,
                             initial='')
    sampling_extraction_technician = forms.CharField(max_length=30, label='Sample Extraction Technician',
                                                     required=False, initial='', widget=forms.TextInput(
            attrs={'placeholder': 'Enter Name of Sample Extraction Technician', 'size': 35}))
    rna_extraction_technician = forms.CharField(max_length=30, label='RNA Extraction Technician', required=False,
                                                initial='', widget=forms.TextInput(
            attrs={'placeholder': 'Enter Name of RNA Extraction Technician', 'size': 35}))
    qpcr_technician = forms.CharField(max_length=30, label='qRT-PCR Technician', required=False, initial='',
                                      widget=forms.TextInput(attrs={'placeholder': 'Enter Name of qRT-PCR Technician',
                                                                    'size': 35}))


class ArrayingForm(forms.Form):
    barcode1 = forms.CharField(max_length=30, label='First 96-Well Plate and Plate into Array Position B2', required=True)

    barcode2 = forms.CharField(max_length=30, label='Second 96-Well Plate and Plate into Array Position B3', required=True)

    barcode3 = forms.CharField(max_length=30, label='Third 96-Well Plate and Plate into Array Position B4', required=True)

    barcode4 = forms.CharField(max_length=30, label='Fourth 96-Well Plate and Plate into Array Position B5', required=True)


class TrackSamplesForm(forms.Form):
    track_samples = forms.MultipleChoiceField(required=True, widget=forms.CheckboxSelectMultiple,
                                              choices=sample_tracking_choice)
