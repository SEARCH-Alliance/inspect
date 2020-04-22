from django.shortcuts import render, redirect
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
from django.contrib import messages
from django.utils.safestring import mark_safe


# @login_required implements a check by django for login credentials. Add this tag to every function to enforce checks
# for user logins. If the check returns False, user will be automatically redirected to the login page

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

    q_recorded = test_results.objects.filter(
        ~Q(qpcr_results_file=''), sampling_date__gte=time_thresh).count() - dub_count
    dub_count += q_recorded

    q_running = test_results.objects.filter(
        ~Q(qrp_id=''), sampling_date__gte=time_thresh).count() - dub_count
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
    sep_count = test_results.objects.filter(
        ~Q(sep_id=''), sampling_date__gte=time_thresh).count() - dub_count
    s = list(set(
        test_results.objects.filter(~Q(sep_id=''), sampling_date__gte=time_thresh).values_list('sep_id', flat=True)))
    sep_id = ', '.join(s)
    dub_count += sep_count

    # Unprocessed sample counter
    unproc_samples = test_results.objects.filter(
        ~Q(barcode=''), sampling_date__gte=time_thresh).count() - dub_count

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

    # RESET ALL SESSION DATA EXCEPT FOR USER LOGIN
    reset_session(request)
    return render(request, 'qpcr_records/index.html', counter_information)


@login_required
def barcode_list_upload(request):
    # Show initial form
    if request.method == 'GET':
        f = BarcodesUploadForm()
        return render(request, 'qpcr_records/barcode_list_upload.html', {'form': f})
    # Upon form submission, redirect to index if valid
    else:
        f = BarcodesUploadForm(request.POST, request.FILES)

        if f.is_valid():
            barcodes = request.FILES['barcodes_file'].read().decode("utf-8").splitlines()

            # Write barcodes to db
            objs = list()
            for b in barcodes:
                objs.append(test_results(barcode=b, sampling_date=date.today().strftime('%Y-%m-%d')))
            test_results.objects.bulk_create(objs)

            messages.success(request, mark_safe('Barcodes list uploaded successfully.'))
            return redirect('index')
        else: # Show form again with user data and errors
            return render(request, 'qpcr_records/barcode_list_upload.html', {'form': f})


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
    # Show initial form
    if request.method == 'GET':
        f = LysisReagentLotForm(initial={'lrl_id': 'M6246109105'})
        return render(request, 'qpcr_records/perform_safety_check.html', {'form': f})
    # Upon form submission, redirect to barcode_capture if valid
    else:
        f = LysisReagentLotForm(request.POST)

        if f.is_valid():
            request.session['lrl_id'] = f.cleaned_data['lrl_id']
            request.session['personnel2_andersen_lab'] = f.cleaned_data['personnel2_andersen_lab']
            return redirect('barcode_capture')
        else:
            return render(request, 'qpcr_records/perform_safety_check.html', {'form': f})



@login_required
def barcode_capture(request):
    """
    Redirected here after the plate barcode has been scanned. User will be prompted to scan a barcode until the second
    to last well is scanned. After scanning the last well, database records for each barcode will be created and the
    user will be routed to a success page.
    :param request: signal call that this function has been called
    :return f: captured barcode
    """
    d1 = {'A': 'B', 'B': 'C', 'C': 'D', 'D': 'E',
          'E': 'F', 'F': 'G', 'G': 'H', 'H': 'A'}

    for k in request.GET.keys():
        request.session[k] = request.GET[k]

    # Initial visit via redirect
    if request.method == 'GET':
        start_well = 'A1'
        request.session['barcodes'] = dict()
        f = SampleStorageAndExtractionWellForm(initial={'ssp_well': start_well, 'sep_well': start_well})
        return render(request, 'qpcr_records/barcode_capture.html', {'form': f, 'barcodes': request.session['barcodes']})
    # Progressing through wells
    else:
        f = SampleStorageAndExtractionWellForm(request.POST)

        # Proceed to next well accordingly
        if f.is_valid():
            # Save well barcodes to session
            active_well = f.cleaned_data['sep_well']
            request.session[active_well] = f.cleaned_data['barcode']
            request.session['barcodes'][active_well] = f.cleaned_data['barcode']
            barcodes = request.session['barcodes']

            # Last well reached; redirect to plate form
            if active_well == 'C1':
                # Save barcode to
                return redirect('sample_plate_capture')
            # Next well
            else:
                row = active_well[0]
                col = int(active_well[1:])
                if row == 'H':
                    row = d1[row]
                    col = col + 1
                else:
                    row = d1[row]

                well = row + str(col)
                f = SampleStorageAndExtractionWellForm(initial={'sep_well': well, 'ssp_well': well})
                return render(request, 'qpcr_records/barcode_capture.html', {'form': f, 'barcodes': barcodes})
        else:  # Initial submission of control wells
            # Initialize variables
            first_sample_well = 'B1'
            f = SampleStorageAndExtractionWellForm(initial={'sep_well': first_sample_well, 'ssp_well': first_sample_well})
            return render(request, 'qpcr_records/barcode_capture.html', {'form': f, 'barcodes': request.session['barcodes']})


@login_required
def update_existing_records(request):
    # Sample Counter Display - Will appear every time the home page is loaded
    counter_information = sample_counter_display()
    return render(request, 'qpcr_records/update_existing_records.html', counter_information)


@login_required
def sample_plate_capture(request):

    # Render initial form
    if request.method == 'GET':
        f = SampleStorageAndExtractionPlateForm()
        return render(request, 'qpcr_records/sample_plate_capture.html',
                      {'form': f, 'barcodes': request.session['barcodes']})
    else:  # Upon form submission, redirect according to validation
        f = SampleStorageAndExtractionPlateForm(request.POST)
        # Save barcodes to db
        if f.is_valid():
            l = list()
            for i in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                for j in range(1, 13):
                    well = i + str(j)
                    if well in ['A1', 'H1']:
                        continue
                    elif well not in request.session.keys():
                        continue
                    else:
                        entry = test_results(barcode=request.session[well].strip(),
                                             ssp_id=f.cleaned_data['ssp_id'],
                                             ssp_well=well,
                                             sep_id=f.cleaned_data['sep_id'],
                                             sep_well=well,
                                             rep_well=well,
                                             rsp_well=well,
                                             sampling_date=date.today().strftime('%Y-%m-%d'),
                                             lrl_id=request.session['lrl_id'].strip(),
                                             personnel1_andersen_lab=request.user.get_full_name(),
                                             personnel2_andersen_lab=request.session['personnel2_andersen_lab'].strip(),
                                             sample_bag_id=f.cleaned_data['sample_bag_id'])
                        l.append(entry)

            test_results.objects.bulk_create(l)
            messages.success(request, mark_safe(f'{len(l)} samples added successfully.'))
            return redirect('index')
        # Invalid form
        else:
            return render(request, 'qpcr_records/sample_plate_capture.html',
                          {'form': f, 'barcodes': request.session['barcodes']})


@login_required
def rna_plate_capture(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    # Render initial form
    if request.method == 'GET':
        f = RNAExtractionPlateForm(initial={'ms2_lot_id': '2003001'})
        return render(request, 'qpcr_records/rna_plate_capture.html', {'form': f})
    else:  # Upon form submission, redirect according to validation
        f = RNAExtractionPlateForm(request.POST)

        if f.is_valid():
            objs = test_results.objects.filter(sep_id=f.cleaned_data['sep_id']).update(
                rep_id=f.cleaned_data['rep_id'].strip(),
                re_date=date.today().strftime('%Y-%m-%d'),
                rsp_id=f.cleaned_data['rep_id'].strip(),
                ms2_lot_id=f.cleaned_data['ms2_lot_id'].strip(),
                personnel_knight_lab=request.user.get_full_name(),
                kfr_id=f.cleaned_data['kfr_id'].strip(),
                rna_extract_kit_id=f.cleaned_data['rna_extract_kit_id'],
                megabeads_id=f.cleaned_data['megabeads_id'],
                carrier_rna_id=f.cleaned_data['carrier_rna_id'])

            # Redirect to homepage
            messages.success(request, mark_safe('RNA plates added successfully.'))
            return redirect('index')
        # Invalid form
        else:
            return render(request, 'qpcr_records/rna_plate_capture.html', {'form': f})


@login_required
def rwp_plate_capture(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    # TODO
    if request.method == 'GET':
        f = ArrayingForm()
        return render(request, 'qpcr_records/rwp_plate_capture.html', {'form': f})
    else:  # Upon form submission, redirect according to validation
        f = ArrayingForm(request.POST)

        # Array form
        if f.is_valid():
            objs = test_results.objects.filter(rep_id__in=[f.cleaned_data['barcode1'], f.cleaned_data['barcode2'],
                                                           f.cleaned_data['barcode3'], f.cleaned_data['barcode4']]).update(
                rwp_id=f.cleaned_data['rwp_id'],
                epm_id=f.cleaned_data['epm_id'])

            # CONVERT 4X96-WELL PLATE LAYOUT TO 1X384-WELL PLATE LAYOUT
            d = dict()
            rows_384 = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
            cols_384 = range(1, 25)
            col_index = 0
            row_index = 0
            for z in range(0, 4):
                for col1, col2 in zip([1, 3, 5, 7, 9, 11], [2, 4, 6, 8, 10, 12]):
                    for row in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                        d[str(z) + row + str(col1)] = rows_384[row_index] + \
                            str(cols_384[col_index])
                        row_index = row_index + 1
                        d[str(z) + row + str(col2)] = rows_384[row_index] + \
                            str(cols_384[col_index])
                        row_index = row_index + 1

                    col_index = col_index + 1
                    row_index = 0

            barcode_list = list()
            i = 0
            for b in [f.cleaned_data['barcode1'], f.cleaned_data['barcode2'],
                      f.cleaned_data['barcode3'], f.cleaned_data['barcode4']]:
                if b in barcode_list:
                    continue
                else:
                    for z in test_results.objects.filter(rep_id=b).values_list('sep_well', flat=True):
                        test_results.objects.filter(rep_id=b, sep_well=z).update(rwp_well=d[str(i) + z],
                                                                                 rsp_well=d[str(i) + z],
                                                                                 qrp_well=d[str(i) + z])
                    i = i + 1

                barcode_list.append(b)
            messages.success(request, mark_safe('RNA working plate added successfully.'))
            return redirect('index')
        else:  # Invalid form
            return render(request, 'qpcr_records/rwp_plate_capture.html', {'form': f})


@login_required
def qpcr_plate_capture(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    if request.method == 'GET':
        f = QPCRStorageAndReactionPlateForm()
        return render(request, 'qpcr_records/qpcr_plate_capture.html', {'form': f})
    else:
        f = QPCRStorageAndReactionPlateForm(request.POST)

        if f.is_valid():
            objs = test_results.objects.filter(rwp_id=f.cleaned_data['rwp_id']).update(
                qrp_id=f.cleaned_data['qrp_id'],
                qpcr_date=date.today().strftime('%Y-%m-%d'),
                personnel_laurent_lab=request.user.get_full_name())

            messages.success(request, mark_safe('qRT-PCR plate added successfully.'))
            return redirect('index')
        else:
            return render(request, 'qpcr_records/qpcr_plate_capture.html', {'form': f})


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
                    q = test_results.objects.filter(
                        barcode__iexact=request.GET[k])
                else:
                    q = q.filter(barcode__iexact=request.GET[k])
            elif request.GET[k] != '' and k == 'sampling_date':
                if q == '':
                    q = test_results.objects.filter(
                        sampling_date__iexact=request.GET[k])
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
                    q = test_results.objects.filter(
                        final_results__iexact=request.GET[k].strip())
                else:
                    q = q.filter(final_results__iexact=request.GET[k].strip())
            elif request.GET[k] != '' and k == 'bag_id':
                if q == '':
                    q = test_results.objects.filter(
                        sample_bag_id__iexact=request.GET[k])
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
    if request.method == 'GET':
        f = QPCRResultsUploadForm()
        return render(request, 'qpcr_records/upload_qpcr_results.html', {'form': f})
    else:
        f = QPCRResultsUploadForm(request.POST, request.FILES)

        if f.is_valid():
            # Parse file for Ct values and determine decision tree resuls
            file = request.FILES['qpcr_results_file']
            qrp_id = file.name.split('.')[0]
            exists = test_results.objects.filter(qrp_id=qrp_id)
            # Upload excel file to s3
            s3 = boto3.resource('s3', region_name=config('AWS_S3_REGION_NAME'),
                                        aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                                        aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'))
            s3.Bucket(config('AWS_STORAGE_BUCKET_NAME')).put_object(Key=file.name, Body=file)

            s3_filepath = 'https://covidtest2.s3-us-west-2.amazonaws.com/' + file.name
            objs = test_results.objects.filter(qrp_id=qrp_id).update(file_transfer_status='Complete')
            objs = test_results.objects.filter(qrp_id=qrp_id).update(qpcr_results_file=s3_filepath)


            # update the database with values
            r = Results()
            data_ = r.get_results(file)
            r.read_fake_names() # * Is this still needed?
            for well, vals in data_.items():
                if well != 'instrument':
                    objs = test_results.objects.filter(qrp_id=qrp_id, rwp_well=well).update(
                                                       ms2_ct_value=vals['MS2'],
                                                       n_ct_value=vals['N gene'],
                                                       orf1ab_ct_value=vals['ORF1ab'],
                                                       s_ct_value=vals['S gene'],
                                                       decision_tree_results=vals['diagnosis'],
                                                       final_results=vals['diagnosis'])

                    if test_results.objects.filter(qrp_id=qrp_id, rwp_well=well).count() > 0:
                        barcodes = test_results.objects.filter(qrp_id=qrp_id, rwp_well=well).values_list('barcode', flat=True)[0]
                        objs = test_results.objects.filter(qrp_id=qrp_id, rwp_well=well).update(fake_name=r.get_fake_name(barcodes))
                elif well == 'instrument':
                    objs = test_results.objects.filter(qrp_id=qrp_id).update(qs5_id=vals)

            messages.success(request, mark_safe('qRT-PCR data uploaded successfully.'))
            return redirect('index')
        else:
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
    l = ['Sample_Plated', 'Sample_Stored', 'RNA_Extraction',
         'Sample_Arrayed', 'qPCR_BackUp', 'qPCR_Reaction']
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
