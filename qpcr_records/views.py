from django.shortcuts import render
from qpcr_records.models import *
from qpcr_records.forms import SearchRecords, ArrayingForm, TrackSamplesForm
from qpcr_records.data_processing.results import Results
from django.contrib.auth.decorators import login_required
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from decouple import config
from datetime import date, datetime, timedelta
import boto3
from django.contrib import messages
from django.db.models import Q



# @login_required implements a check by django for login credentials. Add this tag to every function to enforce checks
# for user logins. If the check returns False, user will be automatically redirected to the login page

# barcode = subprocess.check_output(['python', 'webcam_barcode_scanner.py']).decode('utf-8')
# barcode = barcode.rstrip()

def sample_counter_display():
    """
    Performs queries to determine the number of unprocessed samples, sample extraction plates,
    RNA extraction plates, RNA working plates, running qPCR plates, qPCR plates with results,
    processed qPCR plates, and cleared results. Returns a dictionary with these values.
    """

    # We are calculating the plates from each stage backwards by
    # subtracting the number of plates in the current stage being evaluated
    # timestamp threshold
    time_thresh = datetime.now() - timedelta(days=2)
    dub_count = 0  # tracks plates in previous stages

    # Cleared plate counter
    data_cleared = test_results.objects.filter(~Q(final_results='Undetermined'),sampling_date__gte=time_thresh).count() - dub_count
    dub_count += data_cleared

    # qPCR plate counters
    q_processed = test_results.objects.filter(~Q(decision_tree_results='Undetermined'),sampling_date__gte=time_thresh).count() - dub_count
    dub_count += q_processed

    q_recorded = test_results.objects.filter(~Q(pcr_results_csv=''),sampling_date__gte=time_thresh).count() - dub_count
    dub_count += q_recorded

    q_running = test_results.objects.filter(~Q(qrp_id=''),sampling_date__gte=time_thresh).count() - dub_count
    qrp_id = test_results.objects.filter(~Q(sep_id=''),sampling_date__gte=time_thresh).values_list('qrp_id')
    dub_count += q_running

    # RNA plate counters
    rwp_count = test_results.objects.filter(~Q(rwp_id=''),sampling_date__gte=time_thresh).count() - dub_count  # rna working plate
    rwp_id = test_results.objects.filter(~Q(sep_id=''),sampling_date__gte=time_thresh).values_list('rwp_id')
    dub_count += rwp_count

    rep_count = test_results.objects.filter(~Q(rep_id=''),sampling_date__gte=time_thresh).count() - dub_count  # rna extraction plate
    rep_id = test_results.objects.filter(~Q(sep_id=''),sampling_date__gte=time_thresh).values_list('rep_id')
    dub_count += rep_count

    # Sample extraction plate counter
    sep_count = test_results.objects.filter(~Q(sep_id=''),sampling_date__gte=time_thresh).count() - dub_count
    sep_id = test_results.objects.filter(~Q(sep_id=''),sampling_date__gte=time_thresh).values_list('sep_id')
    dub_count += sep_count

    # Unprocessed sample counter
    unproc_samples = test_results.objects.filter(~Q(barcode=''),sampling_date__gte=time_thresh).count() - dub_count

    # Compile all of the results into a dictionary to return to webpages via Django
    counter_information = {
        'data_cleared': data_cleared,
        'q_processed': q_processed, 'q_recorded': q_recorded, 'q_running': q_running,
        'rwp_count': rwp_count, 'rep_count': rep_count,
        'sep_count': sep_count,
        'unproc_samples': unproc_samples
    }
    return counter_information


@login_required
def index(request):
    """
    Login page redirects here
    """

    # Sample Counter Display - Will appear every time the home page is loaded
    counter_information = sample_counter_display()

    if request.method == 'GET':
        print(request.GET)
        # DATA UPDATE IN ANDERSSON LAB
        if 'ssp_id' in request.GET.keys():
            print(list(request.session.keys()))
            l = list()
            for i in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                for j in range(1, 13):
                    well = i + str(j)
                    if well in ['A1', 'H1']:
                        continue
                    elif well not in request.session.keys():
                        continue
                    else:
                        l.append(test_results(barcode=request.session[well],
                                              ssp_id=request.GET['ssp_id'],
                                              ssp_well=well,
                                              sep_id=request.GET['sep_id'],
                                              sep_well=well,
                                              sampling_date=date.today().strftime('%Y-%m-%d'),
                                              lrl_id=request.session['lrl_id'],
                                              sample_bag_id=request.GET['sample_bag_id']))
            test_results.objects.bulk_create(l)
        # DATA UPDATE IN KNIGHT LAB
        elif 'sep_id' in request.GET.keys() and 'rep_id' in request.GET.keys():
            objs = test_results.objects.filter(sep_id=request.GET['sep_id'])\
                .update(rep_id=request.GET['rep_id'], re_date=date.today().strftime('%Y-%m-%d'),)
        elif 'barcode4' in request.GET.keys():
            print(request.GET)
            objs = test_results.objects.filter(
                rep_id__in=[request.GET['barcode1'], request.GET['barcode2'], request.GET['barcode3'],
                            request.GET['barcode4']]).update(rwp_id=request.GET['rwp_id'], rsp_id=request.GET['rsp_id'],)

            # CONVERT 4X96-WELL PLATE LAYOUT TO 1X384-WELL PLATE LAYOUT
            d = dict()
            rows_384 = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
            cols_384 = range(1, 25)
            col_index = 0
            row_index = 0
            for z in range(0, 4):
                for col1, col2 in zip([1, 3, 5, 7, 9, 11], [2, 4, 6, 8, 10, 12]):
                    for row in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                        d[str(z) + row + str(col1)] = rows_384[row_index] + str(cols_384[col_index])
                        row_index = row_index + 1
                        d[str(z) + row + str(col2)] = rows_384[row_index] + str(cols_384[col_index])
                        row_index = row_index + 1

                    col_index = col_index + 1
                    row_index = 0

            barcode_list = list()
            i = 0
            for b in [request.GET['barcode1'], request.GET['barcode2'], request.GET['barcode3'],
                      request.GET['barcode4']]:
                print(type(b))
                print(b)
                if b in barcode_list:
                    continue
                else:
                    for z in test_results.objects.filter(rep_id=b).values_list('sep_well', flat=True):
                        test_results.objects.filter(rep_id=b, sep_well=z).update(rwp_well=d[str(i)+z], rsp_well=d[str(i)+z])
                    i = i+1

                barcode_list.append(b)
        # DATA UPDATE IN LAURENT LAB
        elif 'rwp_id' in request.GET.keys() and 'qrp_id' in request.GET.keys():
            objs = test_results.objects.filter(rwp_id=request.GET['rwp_id'])\
                .update(qrp_id=request.GET['qrp_id'], qpcr_date=date.today().strftime('%Y-%m-%d'),)

    if request.method == 'POST':  # User is uploading file. Can be the qPCR results or the Barcodes list
        if 'Browse' in request.FILES.keys():  # qPCR Results file
            # Parse file for Ct values and determine decision tree resuls
            file = request.FILES['Browse']
            qreaction_plate = file.name.split('.')[0]

            # Upload excel file to s3
            objs = test_results.objects.filter(qrp_id=qreaction_plate).update(file_transfer_status='Complete')
            s3 = boto3.resource('s3', region_name=config('AWS_S3_REGION_NAME'),
                                aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                                aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'))
            s3.Bucket(config('AWS_STORAGE_BUCKET_NAME')).put_object(Key=file.name, Body=file)

            objs = test_results.objects.filter(qrp_id=qreaction_plate) \
                .update(pcr_results_csv='https://covidtest2.s3-us-west-2.amazonaws.com/' + file.name)

            r = Results()
            data_ = r.get_results(file)
            r.read_fake_names()
            # update the database with values

            for well,vals in data_.items():
                if well != 'instrument':
                    objs = test_results.objects.filter(qrp_id=qreaction_plate,rwp_well=well).update(ms2_ct_value=vals['MS2'])
                    objs = test_results.objects.filter(qrp_id=qreaction_plate,rwp_well=well).update(n_ct_value=vals['N gene'])
                    objs = test_results.objects.filter(qrp_id=qreaction_plate,rwp_well=well).update(orf1ab_ct_value=vals['ORF1ab'])
                    objs = test_results.objects.filter(qrp_id=qreaction_plate,rwp_well=well).update(s_ct_value=vals['S gene'])
                    objs = test_results.objects.filter(qrp_id=qreaction_plate,rwp_well=well).update(decision_tree_results=vals['diagnosis'])
                    barc = test_results.objects.filter(qrp_id=qreaction_plate,rwp_well=well).values_list('barcode',flat=True)[0]
                    objs = test_results.objects.filter(qrp_id=qreaction_plate,rwp_well=well).update(fake_name=r.get_fake_name(barc))
                elif well == 'instrument':
                    objs = test_results.objects.filter(qrp_id=qreaction_plate).update(qs5_id=vals)

            print("Finished database update")

            return render(request, 'qpcr_records/index.html', counter_information)

        elif 'Select Barcode List File' in request.FILES.keys():  # Barcodes list
            barcodes = request.FILES['Select Barcode List File'].read().decode("utf-8").splitlines()
            l = list()
            for b in barcodes:
                l.append(test_results(barcode=b, sampling_date=date.today().strftime('%Y-%m-%d')))
            test_results.objects.bulk_create(l)
            return render(request, 'qpcr_records/index.html', counter_information)
        else:
            return render(request, 'qpcr_records/index.html', counter_information)
    else:
        return render(request, 'qpcr_records/index.html', counter_information)


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
def perform_safety_check(request):
    """
    Present list of safety checks to user before starting plating.
    :param request: signal call that this function has been called
    """
    for k in list(request.session.keys()):
        if k not in ['_auth_user_id', '_auth_user_backend', '_auth_user_hash']:
            del request.session[k]

    if request.method == 'GET':
        for k in request.GET.keys():
            request.session[k] = request.GET[k]

        request.session['ssp_well'] = 'X'
        request.session['current_barcodes'] = dict()
        f = LysisReagentLotForm()
        request.session['expected_barcodes'] = list(
            test_results.objects.filter(sampling_date=date.today().strftime('%Y-%m-%d'),
                                        sep_well='').values_list('barcode', flat=True))
        return render(request, 'qpcr_records/perform_safety_check.html', {'form': f, 'well': 'A1'})


@login_required
def barcode_capture(request):
    """
    Redirected here after the plate barcode has been scanned. User will be prompted to scan a barcode until the second
    to last well is scanned. After scanning the last well, database records for each barcode will be created and the
    user will be routed to a success page.
    :param request: signal call that this function has been called
    :return f: captured barcode
    """
    d1 = {'A': 'B', 'B': 'C', 'C': 'D', 'D': 'E', 'E': 'F', 'F': 'G', 'G': 'H', 'H': 'A'}

    for k in request.GET.keys():
        request.session[k] = request.GET[k]

    # Checks if the last scanned barcode was for a plate. In that case, the current scan is for the first well 'A1'.

    # Add well barcodes
    if 'barcode' in request.GET.keys():

        # Add barcode if not control well
        if 'barcode' in request.session.keys():
            well = request.session['ssp_well']
            request.session['current_barcodes'][well] = request.session['barcode']
            request.session[well] = request.session['barcode']

        barcodes = request.session['current_barcodes']
        # Skip second control well
        if request.session['ssp_well'] == 'G1':
            request.session['last_scan'] = request.session['ssp_well']
            f = SampleStorageAndExtractionWellForm(initial={'ssp_well': 'A2', 'sep_well': 'A2'})
            return render(request, 'qpcr_records/barcode_capture.html', {'form': f, 'barcodes': barcodes, 'well': 'A2'})
        elif request.session['ssp_well'] == 'H12':  # END
            request.session['last_scan'] = 'H12'
            f = SampleStorageAndExtractionPlateForm()
            return render(request, 'qpcr_records/scan_plate_1_2_barcode.html', {'form': f})
        else:
            request.session['last_scan'] = request.session['ssp_well']
            row = request.session['ssp_well'][0]
            col = int(request.session['ssp_well'][1:])
            print(request.session['ssp_well'])
            print(row)
            print(col)
            if row == 'H':
                row = d1[row]
                col = col + 1
            else:
                row = d1[row]

            f = SampleStorageAndExtractionWellForm(initial={'ssp_well': row + str(col), 'sep_well': row + str(col)})
            return render(request, 'qpcr_records/barcode_capture.html', {'form': f, 'barcodes': barcodes,
                                                                         'well': row + str(col)})
    else:
        barcodes = request.session['current_barcodes']
        request.session['last_scan'] = request.session['ssp_well']
        if request.session['ssp_well'] == 'A1': # Redirect from start
            f = SampleStorageAndExtractionWellForm(initial={'ssp_well': 'H1', 'sep_well': 'H1', 'well': 'H1'})
            return render(request, 'qpcr_records/barcode_capture.html', {'form': f, 'barcodes': barcodes, 'well': 'H1'})
        if request.session['ssp_well'] == 'H1': # Redirect from start
            f = SampleStorageAndExtractionWellForm(initial={'ssp_well': 'B1', 'sep_well': 'B1'})
            return render(request, 'qpcr_records/barcode_capture.html', {'form': f, 'barcodes': barcodes, 'well': 'B1'})
        else:
            if 'lrl_id' in request.GET.keys():
                print('Works')
            request.session['lrl_id'] = request.GET['lrl_id']
            print(request.session['lrl_id'])
            request.session['last_scan'] = request.session['ssp_well']
            f = SampleStorageAndExtractionWellForm(initial={'ssp_well': 'A1', 'sep_well': 'A1'})
            return render(request, 'qpcr_records/barcode_capture.html', {'form': f, 'barcodes': barcodes, 'well': 'A1'})


@login_required
def unknown_barcode(request):
    return render(request, 'qpcr_records/unknown_barcode.html')


@login_required
def update_existing_records(request):
    # Sample Counter Display - Will appear every time the home page is loaded
    counter_information = sample_counter_display()
    return render(request, 'qpcr_records/update_existing_records.html', counter_information)


@login_required
def plate_termination(request):
    print(request.GET.keys())
    print(request.session.keys())
    if 'barcode' in request.session.keys():
        request.session[request.session['ssp_well']] = request.session['barcode']
    f = SampleStorageAndExtractionPlateForm()
    return render(request, 'qpcr_records/scan_plate_1_2_barcode.html', {'form': f})


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
    f2 = RNAExtractionPlateForm()

    recent_plate_query = test_results.objects.filter(sampling_date__gte=datetime.now() - timedelta(days=2)).values("sep_id")
    plates = list(recent_plate_query.values())
    return render(request, 'qpcr_records/scan_plate_2_3_barcode.html', {'form1': f1, 'form2': f2, 'plates': plates})


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
    f2 = RNAStorageAndWorkingPlateForm()
    return render(request, 'qpcr_records/scan_plate_arrayed_plate_barcode.html', {'form1': f1, 'form2': f2})


@login_required
def scan_plate_5_6_barcode(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    f1 = RNAStorageAndWorkingPlateForm()
    f2 = QPCRStorageAndReactionPlateForm()
    return render(request, 'qpcr_records/scan_plate_5_6_barcode.html', {'form1': f1, 'form2': f2})


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
        for k in ['barcode', 'sampling_date', 'plate_id', 'technician', 'result']:
            if request.GET[k] != '' and k == 'barcode':
                if q == '':
                    q = test_results.objects.filter(barcode__iexact=request.GET[k])
                else:
                    q = q.filter(barcode__iexact=request.GET[k])
            elif request.GET[k] != '' and k == 'sampling_date':
                if q == '':
                    q = test_results.objects.filter(sampling_date__iexact=request.GET[k])
                else:
                    q = q.filter(sampling_date__iexact=request.GET[k])
            elif request.GET[k] != '' and k == 'plate_id':
                if q == '':
                    q = test_results.objects.filter(Q(ssp_id__icontains=request.GET[k]) |
                                                    Q(sep_id__icontains=request.GET[k]) |
                                                    Q(rep_id__icontains=request.GET[k]) |
                                                    Q(rwp_id__icontains=request.GET[k]) |
                                                    Q(rsp_id__icontains=request.GET[k]) |
                                                    Q(qrp_id__icontains=request.GET[k]))
                else:
                    q = q.filter(Q(ssp_id__icontains=request.GET[k]) | Q(sep_id__icontains=request.GET[k]) |
                                 Q(rep_id__icontains=request.GET[k]) | Q(rwp_id__icontains=request.GET[k]) |
                                 Q(rsp_id__icontains=request.GET[k]) | Q(qrp_id__icontains=request.GET[k]))
            elif request.GET[k] != '' and k == 'technician':
                if q == '':
                    q = test_results.objects.filter(Q(personnel1_andersen_lab__iexact=request.GET[k]) |
                                                    Q(personnel2_andersen_lab__iexact=request.GET[k]) |
                                                    Q(personnel_knight_lab__iexact=request.GET[k]) |
                                                    Q(personnel_laurent_lab__iexact=request.GET[k]))
                else:
                    q = q.filter(Q(personnel1_andersen_lab__iexact=request.GET[k]) |
                                 Q(personnel2_andersen_lab__iexact=request.GET[k]) |
                                 Q(personnel_knight_lab__iexact=request.GET[k]) |
                                 Q(personnel_laurent_lab__iexact=request.GET[k]))
            elif request.GET[k] != '' and k == 'result':
                if q == '':
                    q = test_results.objects.filter(final_results__iexact=request.GET[k])
                else:
                    q = q.filter(final_results__iexact=request.GET[k])
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
            print(k)
            l2.append(k)
        else:
            continue

    q = ''
    for k in l2:
        if k == 'Sample_Plated':
            if q == '':
                q = test_results.objects.filter(~Q(ssp_id=''))
            else:
                q = q.filter(~Q(ssp_id=''))
        elif k == 'Sample_Stored':
            if q == '':
                q = test_results.objects.filter(~Q(sep_id=''))
            else:
                q = q.filter(~Q(sep_id=''))
        elif k == 'RNA_Extraction':
            if q == '':
                q = test_results.objects.filter(~Q(rep_id=''))
            else:
                q = q.filter(~Q(rep_id=''))
        elif k == 'Sample_Arrayed':
            if q == '':
                q = test_results.objects.filter(~Q(rsp_id=''))
            else:
                q = q.filter(~Q(rsp_id=''))
        elif k == 'qPCR_BackUp':
            if q == '':
                q = test_results.objects.filter(~Q(rwp_id=''))
            else:
                q = q.filter(~Q(rwp_id=''))
        else:
            q = test_results.objects.all()
            break

    table = test_resultsTable(q)
    RequestConfig(request).configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    return render(request, 'qpcr_records/track_samples.html', {'table': table})
