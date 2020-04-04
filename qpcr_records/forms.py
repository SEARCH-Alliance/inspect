from django import forms


class SearchRecords(forms.Form):
    barcode = forms.CharField(max_length=30, label='Sample Barcode', required=False, initial='', widget=forms.TextInput(
        attrs={'placeholder': 'Enter Sample Barcode To Search By', 'size': 35}))
    technician = forms.CharField(max_length=30, label='Lab Technician Name', required=False, initial='',
                                 widget=forms.TextInput(
                                     attrs={'placeholder': 'Enter Lab Technician Name To Search By', 'size': 35}))
    lab = forms.CharField(max_length=30, label='Lab', required=False, initial='', widget=forms.TextInput(
        attrs={'placeholder': 'Enter Name of Lab To Search By', 'size': 35}))
    sampling_date = forms.DateField(help_text='(mm/dd/yy)', required=False, initial='',
                                    widget=forms.DateInput(format='%m/%d/%Y'),
                                    input_formats=('%m/%d/%Y',))
    plate_id = forms.CharField(help_text='Enter plate ID or Barcode', max_length=15, required=False, initial='')
