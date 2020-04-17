from django.shortcuts import render
from qpcr_records.models import *
from qpcr_records.forms import *
from qpcr_records.data_processing.results import Results
from django.contrib.auth.decorators import login_required
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from decouple import config
from datetime import date, datetime, timedelta
import boto3
from django.db.models import Q


# @login_required implements a check by django for login credentials. Add this tag to every function to enforce checks
# for user logins. If the check returns False, user will be automatically redirected to the login page

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
    time_thresh = date.today() - timedelta(days=2)
    dub_count = 0  # tracks plates in previous stages

    # Cleared plate counter
    data_cleared = test_results.objects.filter(~Q(final_results=''),
                                               sampling_date__gte=time_thresh).count() - dub_count
    dub_count += data_cleared

    # qPCR plate counters
    q_processed = test_results.objects.filter(~Q(decision_tree_results='Undetermined'),
                                              sampling_date__gte=time_thresh).count() - dub_count
    dub_count += q_processed

    q_recorded = test_results.objects.filter(~Q(pcr_results_csv=''), sampling_date__gte=time_thresh).count() - dub_count
    dub_count += q_recorded

    q_running = test_results.objects.filter(~Q(qrp_id=''), sampling_date__gte=time_thresh).count() - dub_count
    s = list(set(test_results.objects.filter(~Q(sep_id=''), sampling_date__gte=time_thresh).values_list(
        'qrp_id', flat=True).order_by('qrp_id')))
    qrp_id = ', '.join(s)
    dub_count += q_running

    # RNA plate counters
    rwp_count = test_results.objects.filter(~Q(rwp_id=''),
                                            sampling_date__gte=time_thresh).count() - dub_count  # rna working plate
    s = list(set(
        test_results.objects.filter(~Q(sep_id=''), sampling_date__gte=time_thresh).values_list('rwp_id', flat=True)))
    rwp_id = ', '.join(s)
    dub_count += rwp_count

    rep_count = test_results.objects.filter(~Q(rep_id=''),
                                            sampling_date__gte=time_thresh).count() - dub_count  # rna extraction plate
    s = list(set(
        test_results.objects.filter(~Q(sep_id=''), sampling_date__gte=time_thresh).values_list('rep_id', flat=True)))
    rep_id = ', '.join(s)
    dub_count += rep_count

    # Sample extraction plate counter
    sep_count = test_results.objects.filter(~Q(sep_id=''), sampling_date__gte=time_thresh).count() - dub_count
    s = list(set(
        test_results.objects.filter(~Q(sep_id=''), sampling_date__gte=time_thresh).values_list('sep_id', flat=True)))
    sep_id = ', '.join(s)
    dub_count += sep_count

    # Unprocessed sample counter
    unproc_samples = test_results.objects.filter(~Q(barcode=''), sampling_date__gte=time_thresh).count() - dub_count

    # Compile all of the results into a dictionary to return to webpages via Django
    counter_information = {
        'data_cleared': data_cleared,
        'q_processed': q_processed, 'q_recorded': q_recorded, 'q_running': q_running,
        'q_running_ids': qrp_id,
        'qrp_ids': qrp_id,
        'rwp_count': rwp_count, 'rep_count': rep_count,
        'rwp_ids': rwp_id, 'rep_ids': rep_id,
        'sep_count': sep_count,
        'sep_ids': sep_id,
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
        # DATA UPDATE IN ANDERSSON LAB
        if 'ssp_id' in request.GET.keys():
            # IF SSP_ID IS PRESENT, WE ARE CREATING NEW RECORDS. LOOP OVER WELLS FROM A1 THROUGH H12 AND EXTRACT THE
            # BARCODE FROM THE CORRESPONDING WELL. WELLS A1 AND H1 HAVE NO BARCODES SINCE THESE ARE CONTROL WELLS.
            # WELLS A1 AND H1 WILL NOT BE RECORDED IN THE DATABASE
            l = list()
            for i in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                for j in range(1, 13):
                    well = i + str(j)
                    if well in ['A1', 'H1']:
                        continue
                    elif well not in request.session.keys():
                        continue
                    else:
                        l.append(test_results(barcode=request.session[well].strip(),
                                              ssp_id=request.GET['ssp_id'].strip(),
                                              ssp_well=well.strip(),
                                              sep_id=request.GET['sep_id'].strip(),
                                              sep_well=well.strip(),
                                              rep_well=well.strip(),
                                              rsp_well=well.strip(),
                                              sampling_date=date.today().strftime('%Y-%m-%d'),
                                              lrl_id=request.session['lrl_id'].strip(),
                                              personnel1_andersen_lab=request.user.get_full_name(),
                                              personnel2_andersen_lab=request.session['personnel2_andersen_lab'].strip(),
                                              sample_bag_id=request.GET['sample_bag_id'].strip()))
            test_results.objects.bulk_create(l)

        # DATA UPDATE IN KNIGHT LAB
        # IF WE HAVE REP_ID, WE ARE AT THE RNA ELUTION STEP. UPDATE THE DATABASE RECORDS USING THE SEP_ID THAT WAS SCANNED
        elif 'sep_id' in request.GET.keys() and 'rep_id' in request.GET.keys():
            objs = test_results.objects.filter(sep_id=request.GET['sep_id']) \
                .update(rep_id=request.GET['rep_id'].strip(), re_date=date.today().strftime('%Y-%m-%d'),
                        rsp_id=request.GET['rep_id'].strip(), ms2_lot_id=request.GET['ms2_lot_id'].strip(),
                        personnel_knight_lab=request.user.get_full_name(), kfr_id=request.GET['kfr_id'].strip())
        # IF THERE IS A BARCODE4 PASSED, WE ARE AT THE ARRAYING STEP
        elif 'barcode4' in request.GET.keys():
            objs = test_results.objects.filter(
                rep_id__in=[request.GET['barcode1'], request.GET['barcode2'], request.GET['barcode3'],
                            request.GET['barcode4']]).update(rwp_id=request.GET['rwp_id'].strip(),
                                                             epm_id=request.GET['epm_id'].strip())

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
                if b in barcode_list:
                    continue
                else:
                    for z in test_results.objects.filter(rep_id=b).values_list('sep_well', flat=True):
                        test_results.objects.filter(rep_id=b, sep_well=z).update(rwp_well=d[str(i) + z],
                                                                                 rsp_well=d[str(i) + z],
                                                                                 qrp_well=d[str(i) + z])
                    i = i + 1

                barcode_list.append(b)

        # DATA UPDATE IN LAURENT LAB
        # IF BOTH RWP_ID AND QRP_ID WERE PASSED WE ARE AT THE QPCR STEP, WHERE THE LAURENT LAB WILL SCAN THE QPCR REACTION PLATE
        elif 'rwp_id' in request.GET.keys() and 'qrp_id' in request.GET.keys():
            objs = test_results.objects.filter(rwp_id=request.GET['rwp_id']) \
                .update(qrp_id=request.GET['qrp_id'].strip(), qpcr_date=date.today().strftime('%Y-%m-%d'),
                        personnel_laurent_lab=request.user.get_full_name())
        # IF ONLY A QPR_ID WAS PASSED, THE LAURENT LAB WANTS TO REVIEW THE RESULTS FROM THIS QRP_ID
        elif 'qrp_id' in request.session.keys():
            for k in request.GET.keys():
                print("%s : %s\n" %(k, request.GET[k]))
            for i, j in zip(test_results.objects.filter(qrp_id__iexact=request.session['qrp_id']).values_list(
                    'rwp_well', flat=True), list(request.GET.values())):
                test_results.objects.filter(rwp_well=i, qrp_id__iexact=request.session['qrp_id']).update(
                    final_results=j.strip(), is_reviewed=True)
            qs = ''

        # RESET ALL SESSION DATA EXCEPT FOR USER LOGIN
        reset_session(request)

    # FOR ANY POST METHOD, ASSUME THAT THE USER IS UPLOADING A FILE
    if request.method == 'POST':  # User is uploading file. Can be the qPCR results or the Barcodes list
        if 'Browse' in request.FILES.keys():  # qPCR Results file
            # Parse file for Ct values and determine decision tree resuls
            file = request.FILES['Browse']
            qreaction_plate = file.name.split('.')[0]
            exists = test_results.objects.filter(qrp_id=qreaction_plate)
            # First see if plate ID exists
            if not exists:
                return render(request, 'qpcr_records/unknown_qpcr_plate.html')
            else:
                # Double check that this sample doesn't already have data
                history = test_results.objects.filter(~Q(decision_tree_results='Undetermined'), qrp_id=qreaction_plate)
                if not history:
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

                    for well, vals in data_.items():
                        if well != 'instrument':
                            objs = test_results.objects.filter(qrp_id=qreaction_plate, rwp_well=well).update(
                                ms2_ct_value=vals['MS2'])
                            objs = test_results.objects.filter(qrp_id=qreaction_plate, rwp_well=well).update(
                                n_ct_value=vals['N gene'])
                            objs = test_results.objects.filter(qrp_id=qreaction_plate, rwp_well=well).update(
                                orf1ab_ct_value=vals['ORF1ab'])
                            objs = test_results.objects.filter(qrp_id=qreaction_plate, rwp_well=well).update(
                                s_ct_value=vals['S gene'])
                            objs = test_results.objects.filter(qrp_id=qreaction_plate, rwp_well=well).update(
                                decision_tree_results=vals['diagnosis'])
                            objs = test_results.objects.filter(qrp_id=qreaction_plate, rwp_well=well).update(
                                final_results=vals['diagnosis'])

                            if test_results.objects.filter(qrp_id=qreaction_plate, rwp_well=well).count() > 0:
                                barc = test_results.objects.filter(qrp_id=qreaction_plate, rwp_well=well).values_list(
                                    'barcode', flat=True)[0]
                                objs = test_results.objects.filter(qrp_id=qreaction_plate, rwp_well=well).update(
                                    fake_name=r.get_fake_name(barc))
                        elif well == 'instrument':
                            objs = test_results.objects.filter(qrp_id=qreaction_plate).update(qs5_id=vals)

                    return render(request, 'qpcr_records/index.html', counter_information)
                else:
                    return render(request, 'qpcr_records/qpcr_overwrite_warning.html')

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

    if request.method == 'GET':
        for k in request.GET.keys():
            request.session[k] = request.GET[k]

        request.session['ssp_well'] = 'X'
        request.session['current_barcodes'] = dict()
        f1 = LysisReagentLotForm(initial={'lrl_id': 'M6246109105'})
        f2 = PersonnelForm()
        # request.session['expected_barcodes'] = list(
        #    test_results.objects.filter(sampling_date=date.today().strftime('%Y-%m-%d'),
        #                                sep_well='').values_list('barcode', flat=True))
        return render(request, 'qpcr_records/perform_safety_check.html', {'form1': f1, 'form2': f2, 'well': 'A1'})


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
            return render(request, 'qpcr_records/scan_plate_1_2_barcode.html', {'form': f, 'barcodes': barcodes})
        else:
            request.session['last_scan'] = request.session['ssp_well']
            row = request.session['ssp_well'][0]
            col = int(request.session['ssp_well'][1:])
            if row == 'H':
                row = d1[row]
                col = col + 1
            else:
                row = d1[row]

            f = SampleStorageAndExtractionWellForm(initial={'ssp_well': row + str(col), 'sep_well': row + str(col)})
            return render(request, 'qpcr_records/barcode_capture.html', {'form': f, 'barcodes': barcodes,
                                                                         'well': row + str(col)})
    else: # Handle first visit to page passing lrl_id
        barcodes = request.session['current_barcodes']
        request.session['lrl_id'] = request.GET['lrl_id']
        request.session['last_scan'] = request.session['ssp_well']
        f = SampleStorageAndExtractionWellForm(initial={'ssp_well': 'B1', 'sep_well': 'B1', 'well': 'B1'})
        return render(request, 'qpcr_records/barcode_capture.html', {'form': f, 'barcodes': barcodes, 'well': 'B1'})


@login_required
def unknown_barcode(request):
    return render(request, 'qpcr_records/unknown_barcode.html')


@login_required
def update_existing_records(request):
    # Sample Counter Display - Will appear every time the home page is loaded
    counter_information = sample_counter_display()
    return render(request, 'qpcr_records/update_existing_records.html', counter_information)


@login_required
def scan_plate_1_2_barcode(request):
    if 'barcode' in request.session.keys():
        request.session[request.session['ssp_well']] = request.session['barcode']

    barcodes = request.session['current_barcodes']

    f = SampleStorageAndExtractionPlateForm()
    recent_plate_query = test_results.objects.filter(
        sampling_date__gte=datetime.today() - timedelta(days=2)).values_list("sep_id", flat=True)
    plates = list(recent_plate_query)
    return render(request, 'qpcr_records/scan_plate_1_2_barcode.html',
                  {'form': f, 'barcodes': barcodes, 'plates': plates})


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
    f2 = RNAExtractionPlateForm(initial={'ms2_lot_id': '2003001'})
    f3 = MS2LotForm()

    recent_plate_query = test_results.objects.filter(
        sampling_date__gte=datetime.today() - timedelta(days=2)).values_list("sep_id", flat=True)
    plates = list(recent_plate_query)
    return render(request, 'qpcr_records/scan_plate_2_3_barcode.html', {'form1': f1, 'form2': f2, 'form3': f3, 'plates': plates})


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

    recent_plate_query = test_results.objects.filter(sampling_date__gte=datetime.today() - timedelta(days=2)) \
        .values_list("rep_id", flat=True)
    plates = list(recent_plate_query)
    return render(request, 'qpcr_records/scan_plate_arrayed_plate_barcode.html',
                  {'form1': f1, 'form2': f2, 'plates': plates})


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

    recent_plate_query = test_results.objects.filter(sampling_date__gte=datetime.today() - timedelta(days=2)) \
        .values_list("rwp_id", flat=True)
    plates = list(recent_plate_query)
    return render(request, 'qpcr_records/scan_plate_5_6_barcode.html', {'form1': f1, 'form2': f2, 'plates': plates})


@login_required
def record_search(request):
    """
    Function to search records based on the fields. User has to enter at least one field to complete a successful search
    :param request: GET request with search parameters
    :return table: Returns a django-tables2 object to be displayed on the webpage
    """
    if request.method == 'GET':
        # ['csrfmiddlewaretoken', 'barcode', 'sampling_date', 'plate_id', 'technician', 'result', 'sample_bag_id']
        q = ''
        for k in request.GET.keys():
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
                    q = test_results.objects.filter(Q(ssp_id__iexact=request.GET[k].strip()) |
                                                    Q(sep_id__iexact=request.GET[k].strip()) |
                                                    Q(rep_id__iexact=request.GET[k].strip()) |
                                                    Q(rwp_id__iexact=request.GET[k].strip()) |
                                                    Q(rsp_id__iexact=request.GET[k].strip()) |
                                                    Q(qrp_id__iexact=request.GET[k].strip()))
                else:
                    q = q.filter(Q(ssp_id__iexact=request.GET[k].strip()) | Q(sep_id__iexact=request.GET[k].strip()) |
                                 Q(rep_id__iexact=request.GET[k].strip()) | Q(rwp_id__iexact=request.GET[k].strip()) |
                                 Q(rsp_id__iexact=request.GET[k].strip()) | Q(qrp_id__iexact=request.GET[k].strip()))
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
                    q = test_results.objects.filter(final_results__iexact=request.GET[k].strip())
                else:
                    q = q.filter(final_results__iexact=request.GET[k].strip())
            elif request.GET[k] != '' and k == 'bag_id':
                if q == '':
                    q = test_results.objects.filter(sample_bag_id__iexact=request.GET[k])
                else:
                    q = q.filter(sample_bag_id__iexact=request.GET[k])
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
def search_record_form_error(request):
    return render(request, 'qpcr_records/search_record_form_error.html')


@login_required
def upload_qpcr_results(request):
    f = qpcrResultUploadForm()
    return render(request, 'qpcr_records/upload_qpcr_results.html', {'form': f})


@login_required()
def qpcr_plate_id_to_review(request):
    return render(request, 'qpcr_records/qpcr_plate_id_to_review.html', {'form': QPCRStorageAndReactionPlateForm})


@login_required
def review_results(request):
    request.session['qrp_id'] = request.GET['qrp_id']
    q = test_results.objects.filter(qrp_id__iexact=request.GET['qrp_id'])
    table = review_resultsTable(q)
    RequestConfig(request, paginate=False).configure(table)
    return render(request, 'qpcr_records/review_results.html', {'table': table, "choices": sample_result_choices})


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


def reset_session(request):
    for k in list(request.session.keys()):
        if k not in ['_auth_user_id', '_auth_user_backend', '_auth_user_hash']:
            del request.session[k]
