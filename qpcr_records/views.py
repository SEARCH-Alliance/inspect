import subprocess
from django.shortcuts import render
from qpcr_records.models import *
from qpcr_records.forms import SearchRecords
from django.contrib.auth.decorators import login_required
from bokeh.models import ColumnDataSource, Grid, LinearAxis, Plot, Text
from bokeh.embed import components
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from decouple import config
from datetime import date
import boto3


# @login_required implements a check by django for login credentials. Add this tag to every function to enforce checks
# for user logins. If the check returns False, user will be automatically redirected to the login page

@login_required
def index(request):
    """
    Login page redirects here
    """
    if request.method == 'POST':
        print(request.FILES.keys())
        if 'Browse' in request.FILES.keys():

            # f = request.FILES['pcr_results_csv']
            barcode = subprocess.check_output(['python', 'webcam_barcode_scanner.py']).decode('utf-8')
            barcode = barcode.rstrip()

            aws_access_key_id = config('aws_access_key_id')
            aws_secret_access_key = config('aws_secret_access_key')
            aws_storage_bucket_name = config('aws_storage_bucket_name')
            aws_s3_region_name = 'us-west-2'

            #s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key= aws_secret_access_key)
            today = date.today()
            fname = str(barcode) + '_' + str(today.strftime("%m%d%y")) + '.txt'
            print(fname)
            flink = 'https://covidtest2.s3-us-west-2.amazonaws.com/' + fname

            s3 = boto3.resource('s3')
            bucket = s3.Bucket(aws_storage_bucket_name)
            bucket.upload_fileobj(request.FILES['Browse'], fname)

            csv_file = request.FILES["Browse"]
            file_data = csv_file.read().decode("utf-8")

            lines = file_data.split("\n")
            s = lines[0].split(',')
            for i in (0, len(s)):
                if s[i] == 'well':
                    well_col = i
                elif s[i] == 'cQ':
                    ct_col = i
                else:
                    continue

            # loop over the lines and save them in db. If error , store as string and then display
            for line in lines[1:]:
                s = line.split(",")
                t = test_results.objects.filter(plate_id=barcode, sampling_plate_well=s[well_col]).update(ct_value=s[ct_col])


            #s3_client.upload_file(request.FILES['pcr_results_csv'], aws_storage_bucket_name, fname)

            print(test_results.objects.filter(plate_id=barcode).count())
            # t = test_results.objects.filter(plate_id=barcode).update(pcr_results_csv=request.FILES['pcr_results_csv'])
            t = test_results.objects.filter(plate_id=barcode).update(pcr_results_csv=flink)
            #t.save()
            return render(request, 'qpcr_records/index.html')
        else:
            return render(request, 'qpcr_records/index.html')
    else:
        return render(request, 'qpcr_records/index.html')


@login_required
def new_record_form(request):
    """
    Pass new record form to the django template.
    :param request: signal call that this function has been called
    :return f: form to display
    """
    f = SamplingForm()
    return render(request, 'qpcr_records/new_record_form.html', {'form': f})


@login_required
def create_record(request):
    """
    We no longer use this function since this is for manual creation of records.

    This function will update the database based on the form filled by user. Function will check if the request method
    is POST, only then the database will be updated. Uploaded files are passed through the request.FILES variable
    :param request: html request that contains user entries
    :return:
    """
    if request.method == 'POST':
        f = SamplingForm(request.POST, request.FILES)

        # Check if the form is valid : is the form complete ? are the datatypes correct ? etc..
        if f.is_valid():
            # create new record
            new_entry = f.save()
            return render(request, 'qpcr_records/success.html', {'status': 'works'})
        else:
            # something is wrong with the entries
            print(f.errors)
            return render(request, 'qpcr_records/success.html', {'status': 'form not valid'})
    else:
        f = SamplingForm()
        return render(request, 'qpcr_records/new_record.html', {'form': f})


@login_required
def search_record_form(request):
    """
    Pass the search form to the django template. User has to fill at least one field for a successful search
    :param request:
    :param request: signal call that this function has been called
    :return f: form to display to search forms
    """
    f = SearchRecords()
    return render(request, 'qpcr_records/search_record_form.html', {'form': f})


@login_required
def check_information(request):
    """
    Redirect to this view when user wants to start a new platemap. Before the user starts loading a fresh plate, some
    information such as collection site, protocol version, technician name, lab, etc; will need to be reviewed by the
    user. If the default values for the fields are correct, the user has the option to process with loading the samples
    into the plate. If not, the user can edit the field values and then proceed to loading samples in the plate.
    :param request: signal call that this function has been called
    :return barcode: captured barcode
    :return next_well: Since the plate barcode has been recorded here, the next well will always be A1
    """
    f = SamplingForm(initial={'technician': request.user.get_full_name()})
    return render(request, 'qpcr_records/check_information.html', {'form': f})


@login_required
def start_platemap(request):
    """
    Redirect to this view after the user has confirmed the defaults in the submission form. The first step is to scan a
    barcode for the plate. Execute the webcam_barcode_scanner script to to capture barcode from the label using a webcam
    Once the barcode is saved to a session variable, redirect to sample barcode scan view.
    Records the plate barcode in a session variable "plate"
    Records the lastest scanned plate or well in session variable "last_scan". This variable is useful in keeping track of
    how much of the well has been loaded and which well to prompt the user with
    :param request: signal call that this function has been called
    :return barcode: captured barcode
    :return next_well: Since the plate barcode has been recorded here, the next well will always be A1
    """
    if request.method == 'GET':
        for k in request.GET.keys():
            request.session[k] = request.GET[k]
        barcode = subprocess.check_output(['python', 'webcam_barcode_scanner.py']).decode('utf-8')
        barcode = barcode.rstrip()
        request.session['plate'] = barcode
        request.session['last_scan'] = 'plate'

        f = SamplingForm_v2(initial={'plate_id': barcode, 'sampling_plate_well': 'A1'})
        return render(request, 'qpcr_records/start_platemap.html', {'barcode': barcode, 'form': f,
                                                                    'plate': request.session['plate']})


@login_required
def barcode_capture(request):
    """
    Redirected here after the plate barcode has been scanned. User will be prompted to scan a barcode until the second
    to last well is scanned. After scanning the last well, database records for each barcode will be created and the
    user will be routed to a success page.
    :param request: signal call that this function has been called
    :return f: captured barcode
    """
    d1 = {'A': 'C', 'C': 'E', 'E': 'G', 'G': 'I', 'I': 'K', 'K': 'M', 'M': 'O'}
    d2 = {'A': 'B', 'C': 'D', 'E': 'F', 'G': 'H', 'I': 'J', 'K': 'L', 'M': 'N', 'O': 'P'}

    for k in request.GET.keys():
        request.session[k] = request.GET[k]

    try:
        print(request.session['n1_well'])
    except KeyError:
        print('Not Set Yet')

    barcode = subprocess.check_output(['python', 'webcam_barcode_scanner.py']).decode('utf-8')
    barcode = barcode.rstrip()

    # Checks if the last scanned barcode was for a plate. In that case, the current scan is for the first well 'A1'.
    if request.session['last_scan'] == 'plate':
        request.session['A1'] = barcode
        request.session['last_scan'] = 'A1'
        request.session['n1_well'] = 'A1'

        obj = test_results.objects.create(barcode=barcode, sample_box_number=request.session['sample_box_number'],
                                          sample_box_x_position=request.session['sample_box_x_position'],
                                          sample_box_y_position=request.session['sample_box_y_position'],
                                          plate_id=request.session['plate'], sampling_plate_well='A1',
                                          sampling_date=request.session['sampling_date'],
                                          rna_extraction_protocol=request.session['rna_extraction_protocol'],
                                          qpcr_n1_well='A1', qpcr_n2_well='A2', qpcr_rp_well='B2',
                                          qpcr_instrument=request.session['qpcr_instrument'],
                                          technician=request.session['technician'], lab=request.session['lab'],
                                          institute=request.session['institute'])

        f = SamplingForm_v2(initial={'plate_id': request.session['plate'], 'sampling_plate_well': 'A2'})
        return render(request, 'qpcr_records/barcode_capture.html', {'barcode': barcode, 'previous_well': 'A1',
                                                                     'form': f, 'plate': request.session['plate']})
    # Checks if the last scanned barcode was for well A5 (which is the second to last well in the plate). In that case,
    # the current scan is for the last well 'B5'.
    elif request.session['last_scan'] == 'A5':
        request.session['B5'] = barcode
        request.session['last_scan'] = 'B5'

        obj = test_results.objects.create(barcode=barcode, sample_box_number=request.session['sample_box_number'],
                                          sample_box_x_position=request.session['sample_box_x_position'],
                                          sample_box_y_position=request.session['sample_box_y_position'],
                                          plate_id=request.session['plate'], sampling_plate_well='A5',
                                          sampling_date=request.session['sampling_date'],
                                          rna_extraction_protocol=request.session['rna_extraction_protocol'],
                                          qpcr_n1_well='A9', qpcr_n2_well='A10', qpcr_rp_well='B9',
                                          qpcr_instrument=request.session['qpcr_instrument'],
                                          technician=request.session['technician'], lab=request.session['lab'],
                                          institute=request.session['institute'])

        f = SamplingForm_v2(initial={'plate_id': request.session['plate'], 'sampling_plate_well': 'B5'})
        return render(request, 'qpcr_records/platemap.html', {'barcode': barcode, 'previous_well': 'A5',
                                                              'form': f, 'plate': request.session['plate']})
    # If none of the above conditions qualify, the user has scanned a barcode for a well that is not the first or last.
    # Proceed normally
    else:
        well = request.session['last_scan']
        row = well[0]
        col = int(well[1:])
        if row == 'A':
            row = 'B'
        else:
            row = 'A'
            col = col + 1

        next_well = row + str(col)
        request.session[well] = barcode
        request.session['last_scan'] = next_well

        n1_col = int(request.session['n1_well'][1:])
        n1_row = request.session['n1_well'][0]
        if n1_col == 9:
            n1_row = d1[n1_row]
            rp_row = d2[n1_row]
            n1_col = 1
            n2_col = 2
        else:
            n1_row = request.session['n1_well'][0]
            n1_col = n1_col + 2
            n2_col = n1_col + 1
            rp_row = d2[n1_row]

        request.session['n1_well'] = n1_row + str(n1_col)
        n2_well = n1_row + str(n2_col)
        rp_well = rp_row + str(n1_col)

        obj = test_results.objects.create(barcode=barcode, sample_box_number=request.session['sample_box_number'],
                                          sample_box_x_position=request.session['sample_box_x_position'],
                                          sample_box_y_position=request.session['sample_box_y_position'],
                                          plate_id=request.session['plate'],
                                          sampling_plate_well=request.session['last_scan'],
                                          sampling_date=request.session['sampling_date'],
                                          rna_extraction_protocol=request.session['rna_extraction_protocol'],
                                          qpcr_n1_well=request.session['n1_well'], qpcr_n2_well=n2_well,
                                          qpcr_rp_well=rp_well,
                                          qpcr_instrument=request.session['qpcr_instrument'],
                                          technician=request.session['technician'], lab=request.session['lab'],
                                          institute=request.session['institute'])

        f = SamplingForm_v2(initial={'plate_id': request.session['plate'], 'sampling_plate_well': next_well})
        return render(request, 'qpcr_records/barcode_capture.html', {'barcode': barcode,
                                                                     'previous_well': request.session['last_scan'],
                                                                     'form': f, 'plate': request.session['plate']})


@login_required
def platemap(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    barcode = subprocess.check_output(['python', 'webcam_barcode_scanner.py']).decode('utf-8')
    barcode = barcode.rstrip()
    obj = test_results.objects.create(barcode=barcode, collection_site=request.session['collection_site'],
                                      collection_protocol=request.session['collection_protocol'],
                                      processing_protocol=request.session['processing_protocol'],
                                      collection_date=request.session['collection_date'],
                                      processing_date=request.session['processing_date'],
                                      machine_model=request.session['machine_model'],
                                      reagents=request.session['reagents'],
                                      plate_id=request.session['plate'], well='B5')
    # obj.save()

    x = range(0, 6)
    y = range(0, 3)
    text = list()
    for i in ['A1', 'B1', 'A2', 'B2', 'A3', 'B3', 'A4', 'B4', 'A5', 'B5']:
        text.append(request.session[i])
    source = ColumnDataSource(dict(x=x, y=y, text=text))
    plot = Plot(title=None, plot_width=300, plot_height=300, min_border=0, toolbar_location=None)
    glyph = Text(x="x", y="y", text="text", text_color="firebrick")
    plot.add_glyph(source, glyph)
    xaxis = LinearAxis()
    plot.add_layout(xaxis, 'below')

    yaxis = LinearAxis()
    plot.add_layout(yaxis, 'left')

    plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
    plot.add_layout(Grid(dimension=1, ticker=yaxis.ticker))

    script, div = components(plot)

    return render(request, 'qpcr_records/platemap.html', {'script': script, 'div': div})


@login_required
def record_search(request):
    """
    Function to search records based on the fields. User has to enter at least one field to complete a successful search
    :param request: GET request with search parameters
    :return table: Returns a django-tables2 object to be displayed on the webpage
    """
    if request.method == 'GET':
        # ['csrfmiddlewaretoken', 'barcode', 'technician', 'lab', 'collection_date', 'processing_date']
        q = ''
        for k in ['barcode', 'technician', 'lab', 'sampling_date', 'plate_id']:
            if request.GET[k] != '' and k == 'barcode':
                if q == '':
                    q = test_results.objects.filter(barcode=request.GET[k])
                else:
                    q = q.filter(barcode=request.GET[k])
            elif request.GET[k] != '' and k == 'technician':
                if q == '':
                    q = test_results.objects.filter(technician=request.GET[k])
                else:
                    q = q.filter(technician=request.GET[k])
            elif request.GET[k] != '' and k == 'lab':
                if q == '':
                    q = test_results.objects.filter(lab=request.GET[k])
                else:
                    q = q.filter(lab=request.GET[k])
            elif request.GET[k] != '' and k == 'sampling_date':
                if q == '':
                    q = test_results.objects.filter(sampling_date=request.GET[k])
                else:
                    q = q.filter(sampling_date=request.GET[k])
            elif request.GET[k] != '' and k == 'plate_id':
                if q == '':
                    q = test_results.objects.filter(plate_id=request.GET[k])
                else:
                    q = q.filter(plate_id=request.GET[k])
            else:
                continue

        if q == '':
            return render(request, 'qpcr_records/search_record_form_error.html')
        else:
            print(q.count())
            table = test_resultsTable(q)
            RequestConfig(request).configure(table)

            export_format = request.GET.get('_export', None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response('table.{}'.format(export_format))

            table.columns.hide('id')
            return render(request, 'qpcr_records/record_search.html', {'table': table})


@login_required
def upload_qpcr_results(request):
    f = qpcrResultUploadForm()
    return render(request, 'qpcr_records/upload_qpcr_results.html', {'form': f})
