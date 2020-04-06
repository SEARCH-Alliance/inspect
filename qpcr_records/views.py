import subprocess
from django.shortcuts import render
from qpcr_records.models import *
from qpcr_records.forms import SearchRecords, ArrayingForm, TrackSamplesForm
from django.contrib.auth.decorators import login_required
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from decouple import config
from datetime import date
import boto3
import pandas
from io import StringIO
import datetime
from django.db.models import Q


# @login_required implements a check by django for login credentials. Add this tag to every function to enforce checks
# for user logins. If the check returns False, user will be automatically redirected to the login page

# barcode = subprocess.check_output(['python', 'webcam_barcode_scanner.py']).decode('utf-8')
# barcode = barcode.rstrip()

@login_required
def index(request):
    """
    Login page redirects here
    """
    if request.method == 'GET':
        print(request.GET)
        if 'plate_1_id' in request.GET.keys():
            l = list()
            for i in ['A', 'B', 'C']:
                for j in range(1, 4):
                    l.append(test_results(barcode=request.session[i + str(j)], plate_1_id=request.GET['plate_1_id'],
                                          plate_1_well=i + str(j), plate_2_id=request.GET['plate_2_id'],
                                          plate_2_well=i + str(j),
                                          sampling_date=datetime.date.today().strftime('%Y-%m-%d')))
            test_results.objects.bulk_create(l)
        elif 'plate_2_id' in request.GET.keys() and 'plate_3_id' in request.GET.keys():
            objs = test_results.objects.filter(plate_2_id=request.GET['plate_2_id']).update(plate_3_id=request.GET['plate_3_id'])
        elif 'barcode4' in request.GET.keys():
            objs = test_results.objects.filter(
                plate_3_id__in=[request.GET['barcode1'], request.GET['barcode2'], request.GET['barcode3'],
                                request.GET['barcode4']]).update(plate_4_id=request.GET['plate_4_id'])
        elif 'plate_4_id' in request.GET.keys() and 'plate_5_id' in request.GET.keys():
            objs = test_results.objects.filter(plate_4_id=request.GET['plate_4_id']).update(plate_5_id=request.GET['plate_5_id'])
        elif 'plate_5_id' in request.GET.keys() and 'plate_6_id' in request.GET.keys():
            objs = test_results.objects.filter(plate_5_id=request.GET['plate_5_id']).update(plate_6_id=request.GET['plate_6_id'])

    if request.method == 'POST':
        if 'Browse' in request.FILES.keys():
            # f = request.FILES['pcr_results_csv']
            barcode = subprocess.check_output(['python', 'webcam_barcode_scanner.py']).decode('utf-8')
            barcode = barcode.rstrip()

            csv_file = pandas.read_csv(request.FILES['Browse'])
            for i, j in zip(csv_file['Well'], csv_file['Cq']):
                if i[1:] in ['01', '02', '03', '04', '05', '06', '07', '08', '09']:
                    i = i[0] + str(i[2])

                if test_results.objects.filter(plate_id=barcode, qpcr_n1_well=i).count() > 0:
                    print('HERE 1')
                    print(i)
                    t = test_results.objects.filter(plate_id=barcode, qpcr_n1_well=i).update(n1_ct_value=j)
                elif test_results.objects.filter(plate_id=barcode, qpcr_n2_well=i).count() > 0:
                    print('HERE 2')
                    print(i)
                    t = test_results.objects.filter(plate_id=barcode, qpcr_n2_well=i).update(n2_ct_value=j)
                else:
                    print('HERE 3')
                    print(i)
                    t = test_results.objects.filter(plate_id=barcode, qpcr_rp_well=i).update(rp_ct_value=j)

            aws_access_key_id = config('aws_access_key_id')
            aws_secret_access_key = config('aws_secret_access_key')
            aws_storage_bucket_name = config('aws_storage_bucket_name')
            aws_s3_region_name = 'us-west-2'

            today = date.today()
            fname = str(barcode) + '_' + str(today.strftime("%m%d%y")) + '.txt'
            flink = 'https://covidtest2.s3-us-west-2.amazonaws.com/' + fname
            t = test_results.objects.filter(plate_id=barcode).update(pcr_results_csv=flink)

            csv_buffer = StringIO()
            csv_file.to_csv(csv_buffer, sep=",", index=False)
            s3_resource = boto3.resource("s3")
            s3_resource.Object(aws_storage_bucket_name, fname).put(Body=csv_buffer.getvalue())

            # s3 = boto3.client('s3')
            # s3.put_object(Bucket=aws_storage_bucket_name, Body=csv_file, Key=fname)

            # s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key= aws_secret_access_key)

            # s3 = boto3.resource('s3')
            # bucket = s3.Bucket(aws_storage_bucket_name)
            # bucket.upload_fileobj(request.FILES['Browse'], fname)

            # s3_client.upload_file(request.FILES['pcr_results_csv'], aws_storage_bucket_name, fname)

            # t = test_results.objects.filter(plate_id=barcode).update(pcr_results_csv=request.FILES['pcr_results_csv'])
            # t.save()
            return render(request, 'qpcr_records/index.html')
        else:
            return render(request, 'qpcr_records/index.html')
    else:
        return render(request, 'qpcr_records/index.html')


@login_required
def new_record_form(request):
    """
    THIS FUNCTION IS NO LONGER USED
    Pass new record form to the django template.
    :param request: signal call that this function has been called
    :return f: form to display
    """
    f = ArrayingForm()
    return render(request, 'qpcr_records/new_record_form.html', {'form': f})


@login_required
def create_record(request):
    """
    THIS FUNCTION IS NO LONGER USED.

    This function will update the database based on the form filled by user. Function will check if the request method
    is POST, only then the database will be updated. Uploaded files are passed through the request.FILES variable
    :param request: html request that contains user entries
    :return:
    """
    if request.method == 'POST':
        f = ArrayingForm(request.POST, request.FILES)

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
        f = ArrayingForm()
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
    THIS FUNCTION IS NO LONGER USED
    
    Redirect to this view when user wants to start a new platemap. Before the user starts loading a fresh plate, some
    information such as collection site, protocol version, technician name, lab, etc; will need to be reviewed by the
    user. If the default values for the fields are correct, the user has the option to process with loading the samples
    into the plate. If not, the user can edit the field values and then proceed to loading samples in the plate.
    :param request: signal call that this function has been called
    :return barcode: captured barcode
    :return next_well: Since the plate barcode has been recorded here, the next well will always be A1
    """
    f = ArrayingForm()
    return render(request, 'qpcr_records/check_information.html', {'form': f})


@login_required
def start_sampling_plate(request):
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

        f = Sampling_Form(initial={'plate_1_well': 'A1', 'plate_2_well': 'A1'})
        request.session['plate_well'] = 'A1'
        return render(request, 'qpcr_records/start_sampling_plate.html', {'form': f})


@login_required
def barcode_capture(request):
    """
    Redirected here after the plate barcode has been scanned. User will be prompted to scan a barcode until the second
    to last well is scanned. After scanning the last well, database records for each barcode will be created and the
    user will be routed to a success page.
    :param request: signal call that this function has been called
    :return f: captured barcode
    """
    d1 = {'A': 'B', 'B': 'C', 'C': 'A'}

    for k in request.GET.keys():
        request.session[k] = request.GET[k]

    # Checks if the last scanned barcode was for a plate. In that case, the current scan is for the first well 'A1'.
    if 'plate_1_well' in request.session.keys():
        if request.session['plate_1_well'] == 'A1':
            request.session[request.session['plate_1_well']] = request.session['barcode']
            request.session['last_scan'] = 'A1'
            f = Sampling_Form(initial={'plate_1_well': 'B1', 'plate_2_well': 'B1'})
            return render(request, 'qpcr_records/barcode_capture.html', {'form': f})
        elif request.session['plate_1_well'] == 'C3':
            request.session[request.session['plate_1_well']] = request.session['barcode']
            request.session['last_scan'] = 'C3'
            f = Plate_1_2_Form()
            return render(request, 'qpcr_records/scan_plate_1_2_barcode.html', {'form': f})
        else:
            request.session[request.session['plate_1_well']] = request.session['barcode']
            request.session['last_scan'] = request.session['plate_1_well']
            row = request.session['plate_1_well'][0]
            col = int(request.session['plate_1_well'][1])
            if row == 'C':
                row = d1[row]
                col = col + 1
            else:
                row = d1[row]

            f = Sampling_Form(initial={'plate_1_well': row + str(col), 'plate_2_well': row + str(col)})
            return render(request, 'qpcr_records/barcode_capture.html', {'form': f})


@login_required
def update_existing_records(request):
    return render(request, 'qpcr_records/update_existing_records.html')


@login_required
def scan_plate_1_2_barcode(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    return render(request, 'qpcr_records/index.html')


@login_required
def scan_plate_2_3_barcode(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    f1 = Plate_1_2_Form()
    f2 = Plate_3_Form()
    return render(request, 'qpcr_records/scan_plate_2_3_barcode.html', {'form1': f1, 'form2': f2})


@login_required
def scan_plate_2_3_barcode(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    f1 = Plate_1_2_Form()
    f2 = Plate_3_Form()
    return render(request, 'qpcr_records/scan_plate_2_3_barcode.html', {'form1': f1, 'form2': f2})


@login_required
def scan_plate_arrayed_plate_barcode(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    f1 = ArrayingForm()
    f2 = Plate_4_Form()
    return render(request, 'qpcr_records/scan_plate_arrayed_plate_barcode.html', {'form1': f1, 'form2': f2})


@login_required
def scan_plate_4_5_barcode(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    f1 = Plate_4_Form()
    f2 = Plate_5_Form()
    return render(request, 'qpcr_records/scan_plate_4_5_barcode.html', {'form1': f1, 'form2': f2})


@login_required
def scan_plate_5_6_barcode(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    f1 = Plate_5_Form()
    f2 = Plate_6_Form()
    return render(request, 'qpcr_records/scan_plate_5_6_barcode.html', {'form1': f1, 'form2': f2})


@login_required
def record_search(request):
    """
    Function to search records based on the fields. User has to enter at least one field to complete a successful search
    :param request: GET request with search parameters
    :return table: Returns a django-tables2 object to be displayed on the webpage
    """
    if request.method == 'GET':
        print(request.GET.keys())
        # ['csrfmiddlewaretoken', 'barcode', 'technician', 'lab', 'collection_date', 'processing_date']
        q = ''
        for k in ['barcode', 'fake_name', 'technician', 'lab', 'sampling_date', 'plate_1_id', 'plate_2_id', 'plate_3_id', 'plate_4_id', 'plate_5_id', 'plate_6_id']:
            if request.GET[k] != '' and k == 'barcode':
                if q == '':
                    q = test_results.objects.filter(barcode=request.GET[k])
                else:
                    q = q.filter(barcode=request.GET[k])
            elif request.GET[k] != '' and k == 'fake_name':
                if q == '':
                    q = test_results.objects.filter(fake_name=request.GET[k])
                else:
                    q = q.filter(fake_name=request.GET[k])
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
            elif request.GET[k] != '' and k == 'plate_1_id':
                if q == '':
                    q = test_results.objects.filter(plate_1_id=request.GET[k])
                else:
                    q = q.filter(plate_1_id=request.GET[k])
            elif request.GET[k] != '' and k == 'plate_2_id':
                if q == '':
                    q = test_results.objects.filter(plate_2_id=request.GET[k])
                else:
                    q = q.filter(plate_2_id=request.GET[k])
            elif request.GET[k] != '' and k == 'plate_3_id':
                if q == '':
                    q = test_results.objects.filter(plate_3_id=request.GET[k])
                else:
                    q = q.filter(plate_3_id=request.GET[k])
            elif request.GET[k] != '' and k == 'plate_4_id':
                if q == '':
                    q = test_results.objects.filter(plate_4_id=request.GET[k])
                else:
                    q = q.filter(plate_4_id=request.GET[k])
            elif request.GET[k] != '' and k == 'plate_4_id':
                if q == '':
                    q = test_results.objects.filter(plate_5_id=request.GET[k])
                else:
                    q = q.filter(plate_5_id=request.GET[k])
            elif request.GET[k] != '' and k == 'plate_6_id':
                if q == '':
                    q = test_results.objects.filter(plate_6_id=request.GET[k])
                else:
                    q = q.filter(plate_6_id=request.GET[k])
            else:
                continue

        if q == '':
            return render(request, 'qpcr_records/search_record_form_error.html')
        else:
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


@login_required
def track_samples_form(request):
    f = TrackSamplesForm()
    return render(request, 'qpcr_records/track_samples_form.html', {'form': f})


@login_required
def track_samples(request):
    l = ['Sample_Plated', 'Sample_Stored', 'RNA_Extraction', 'Sample_Arrayed', 'qPCR_BackUp', 'qPCR_Reaction']
    l2 = list()
    for k in l:
        if k in request.GET['track_samples']:
            continue
        else:
            l2.append(k)

    q = ''
    for k in l2:
        if k == 'Sample_Plated':
            if q == '':
                q = test_results.objects.filter(plate_1_id='X')
            else:
                q = q.filter(plate_1_id='X')
        elif k == 'Sample_Stored':
            if q == '':
                q = test_results.objects.filter(plate_2_id='X')
            else:
                q = q.filter(plate_2_id='X')
        elif k == 'RNA_Extraction':
            if q == '':
                q = test_results.objects.filter(plate_3_id='X')
            else:
                q = q.filter(plate_3_id='X')
        elif k == 'Sample_Arrayed':
            if q == '':
                q = test_results.objects.filter(plate_4_id='X')
            else:
                q = q.filter(plate_4_id='X')
        elif k == 'qPCR_BackUp':
            if q == '':
                q = test_results.objects.filter(plate_5_id='X')
            else:
                q = q.filter(plate_5_id='X')
        else:
            q = test_results.objects.all()
            break

    table = test_resultsTable(q)
    RequestConfig(request).configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    table.columns.hide('id')
    return render(request, 'qpcr_records/track_samples.html', {'table': table})
