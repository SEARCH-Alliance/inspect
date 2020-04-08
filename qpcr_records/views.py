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
from django.contrib import messages


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
        if 'ssp_id' in request.GET.keys():
            l = list()
            for i in ['A', 'B', 'C']:
                for j in range(1, 4):
                    l.append(test_results(barcode=request.session[i + str(j)], ssp_id=request.GET['ssp_id'],
                                          ssp_well=i + str(j), sep_id=request.GET['sep_id'],
                                          sep_well=i + str(j),
                                          sampling_date=datetime.date.today().strftime('%Y-%m-%d')))
            test_results.objects.bulk_create(l)
        elif 'sep_id' in request.GET.keys() and 'rep_id' in request.GET.keys():
            objs = test_results.objects.filter(sep_id=request.GET['sep_id']).update(rep_id=request.GET['rep_id'])
            objs = test_results.objects.filter(sep_id=request.GET['sep_id']).update(rsp_id=request.GET['rsp_id'])
        elif 'barcode4' in request.GET.keys():
            objs = test_results.objects.filter(
                rep_id__in=[request.GET['barcode1'], request.GET['barcode2'], request.GET['barcode3'],
                            request.GET['barcode4']]).update(rwp_id=request.GET['rwp_id'])
        elif 'rwp_id' in request.GET.keys() and 'qrp_id' in request.GET.keys():
            objs = test_results.objects.filter(rwp_id=request.GET['rwp_id']).update(qrp_id=request.GET['qrp_id'])

    if request.method == 'POST':
        if 'Browse' in request.FILES.keys():
            file = request.FILES['Browse']
            objs = test_results.objects.filter(qrp_id=file.name.split('_')[0]).update(file_transfer_status='Complete')
            print("The file name is : %s" % file.name)
            s3 = boto3.resource('s3')
            s3.Bucket('covidtest2').put_object(Key=file.name, Body=file)
            return render(request, 'qpcr_records/index.html')
        elif 'Select Barcode List File' in request.FILES.keys():
            barcodes = request.FILES['Select Barcode List File'].read().decode("utf-8").splitlines()
            l = list()
            for b in barcodes:
                l.append(test_results(barcode=b, sampling_date=datetime.date.today().strftime('%Y-%m-%d')))
            test_results.objects.bulk_create(l)
            return render(request, 'qpcr_records/index.html')
        else:
            return render(request, 'qpcr_records/index.html')
    else:
        return render(request, 'qpcr_records/index.html')


@login_required
def barcode_list_upload(request):
    return render(request, 'qpcr_records/barcode_list_upload.html')


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

        request.session['expected_barcodes'] = list(
            test_results.objects.filter(sampling_date=date.today().strftime('%Y-%m-%d'),
                                        sep_well='').values_list('barcode', flat=True))
        f = SampleStorageAndExtractionWellForm(initial={'ssp_well': 'A1', 'sep_well': 'A1'})
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

    if 'ssp_well' in request.session.keys():
        if request.session['ssp_well'] == 'A1':
            request.session[request.session['ssp_well']] = request.session['barcode']
            request.session['last_scan'] = 'A1'
            f = SampleStorageAndExtractionWellForm(initial={'ssp_well': 'B1', 'sep_well': 'B1'})
            return render(request, 'qpcr_records/barcode_capture.html', {'form': f})
        elif request.session['ssp_well'] == 'C3':
            request.session[request.session['ssp_well']] = request.session['barcode']
            request.session['last_scan'] = 'C3'
            f = SampleStorageAndExtractionPlateForm()
            return render(request, 'qpcr_records/scan_plate_1_2_barcode.html', {'form': f})
        else:
            request.session[request.session['ssp_well']] = request.session['barcode']
            request.session['last_scan'] = request.session['ssp_well']
            row = request.session['ssp_well'][0]
            col = int(request.session['ssp_well'][1])
            if row == 'C':
                row = d1[row]
                col = col + 1
            else:
                row = d1[row]

            f = SampleStorageAndExtractionWellForm(initial={'ssp_well': row + str(col), 'sep_well': row + str(col)})
            return render(request, 'qpcr_records/barcode_capture.html', {'form': f})


@login_required
def unknown_barcode(request):
    return render(request, 'qpcr_records/unknown_barcode.html')


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
    f1 = SampleStorageAndExtractionPlateForm()
    f2 = RNAExtractionAndStoragePlateForm()
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
    f2 = RNAWorkingPlateForm()
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
    f1 = RNAWorkingPlateForm()
    f2 = QPCRReactionPlateForm()
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
        for k in ['barcode', 'sampling_date', 'ssp_id', 'sep_id', 'rep_id', 'rsp_id', 'rwp_id', 'qrp_id',
                  'sampling_extraction_technician', 'rna_extraction_technician', 'qpcr_technician']:
            if request.GET[k] != '' and k == 'barcode':
                if q == '':
                    q = test_results.objects.filter(barcode=request.GET[k])
                else:
                    q = q.filter(barcode=request.GET[k])
            elif request.GET[k] != '' and k == 'sampling_date':
                if q == '':
                    q = test_results.objects.filter(sampling_date=request.GET[k])
                else:
                    q = q.filter(sampling_date=request.GET[k])
            elif request.GET[k] != '' and k == 'ssp_id':
                if q == '':
                    q = test_results.objects.filter(ssp_id=request.GET[k])
                else:
                    q = q.filter(ssp_id=request.GET[k])
            elif request.GET[k] != '' and k == 'sep_id':
                if q == '':
                    q = test_results.objects.filter(sep_id=request.GET[k])
                else:
                    q = q.filter(sep_id=request.GET[k])
            elif request.GET[k] != '' and k == 'rep_id':
                if q == '':
                    q = test_results.objects.filter(rep_id=request.GET[k])
                else:
                    q = q.filter(rep_id=request.GET[k])
            elif request.GET[k] != '' and k == 'rsp_id':
                if q == '':
                    q = test_results.objects.filter(rsp_id=request.GET[k])
                else:
                    q = q.filter(rsp_id=request.GET[k])
            elif request.GET[k] != '' and k == 'rwp_id':
                if q == '':
                    q = test_results.objects.filter(rwp_id=request.GET[k])
                else:
                    q = q.filter(rwp_id=request.GET[k])
            elif request.GET[k] != '' and k == 'qrp_id':
                if q == '':
                    q = test_results.objects.filter(qrp_id=request.GET[k])
                else:
                    q = q.filter(qrp_id=request.GET[k])
            elif request.GET[k] != '' and k == 'sampling_extraction_technician':
                if q == '':
                    q = test_results.objects.filter(sample_extraction_technician1=request.GET[k])
                    q = test_results.objects.filter(sample_extraction_technician2=request.GET[k])
                else:
                    q = q.filter(sample_extraction_technician1=request.GET[k])
                    q = q.filter(sample_extraction_technician2=request.GET[k])
            elif request.GET[k] != '' and k == 'rna_extraction_technician':
                if q == '':
                    q = test_results.objects.filter(rna_extraction_technician=request.GET[k])
                else:
                    q = q.filter(rna_extraction_technician=request.GET[k])
            elif request.GET[k] != '' and k == 'qpcr_technician':
                if q == '':
                    q = test_results.objects.filter(qpcr_technician=request.GET[k])
                else:
                    q = q.filter(qpcr_technician=request.GET[k])
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

            # table.columns.hide('id')
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
            l2.append(k)
        else:
            continue

    q = ''
    for k in l2:
        if k == 'Sample_Plated':
            if q == '':
                q = test_results.objects.filter(ssp_id='X')
            else:
                q = q.filter(ssp_id='X')
        elif k == 'Sample_Stored':
            if q == '':
                q = test_results.objects.filter(sep_id='X')
            else:
                q = q.filter(sep_id='X')
        elif k == 'RNA_Extraction':
            if q == '':
                q = test_results.objects.filter(rep_id='X')
            else:
                q = q.filter(rep_id='X')
        elif k == 'Sample_Arrayed':
            if q == '':
                q = test_results.objects.filter(rsp_id='X')
            else:
                q = q.filter(rsp_id='X')
        elif k == 'qPCR_BackUp':
            if q == '':
                q = test_results.objects.filter(rwp_id='X')
            else:
                q = q.filter(rwp_id='X')
        else:
            q = test_results.objects.all()
            break

    table = test_resultsTable(q)
    RequestConfig(request).configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    #table.columns.hide('id')
    return render(request, 'qpcr_records/track_samples.html', {'table': table})
