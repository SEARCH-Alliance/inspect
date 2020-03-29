import subprocess
from django.shortcuts import render
from test_results.models import *
from test_results.forms import SearchRecords
from django.contrib.auth.decorators import login_required
from bokeh.models import ColumnDataSource, Grid, LinearAxis, Plot, Text
from bokeh.embed import components


# @login_required implements a check by django for login credentials. Add this tag to every function to enforce checks
# for user logins. If the check returns False, user will be automatically redirected to the login page

@login_required
def index(request):
    """
    Login page redirects here
    """
    return render(request, 'test_results/index.html')


@login_required
def new_record_form(request):
    """
    Pass new record form to the django template.
    :param request: signal call that this function has been called
    :return f: form to display
    """
    f = ResultsForm()
    return render(request, 'test_results/new_record_form.html', {'form': f})


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
        f = ResultsForm(request.POST, request.FILES)

        # Check if the form is valid : is the form complete ? are the datatypes correct ? etc..
        if f.is_valid():
            # create new record
            new_entry = f.save()
            return render(request, 'test_results/success.html', {'status': 'works'})
        else:
            # something is wrong with the entries
            print(f.errors)
            return render(request, 'test_results/success.html', {'status': 'form not valid'})
    else:
        f = ResultsForm()
        return render(request, 'test_results/new_record.html', {'form': f})


@login_required
def search_record_form(request):
    """
    Pass the search form to the django template. User has to fill at least one field for a successful search
    :param request:
    :param request: signal call that this function has been called
    :return f: form to display to search forms
    """
    f = SearchRecords()
    return render(request, 'test_results/search_record_form.html', {'form': f})


@login_required
def start_platemap(request):
    """
    Redirect to this view when user wants to start a new platemap. The first step is to scan a barcode for the plate.
    Execute the webcam_barcode_scanner script to to capture barcode from the label using a webcam
    Once the barcode is saved to a session variable, redirect to sample barcode scan view
    Records the plate barcode in a session variable "plate"
    Records the last scanned plate or well in session variable "last_scan". This variable is useful in keeping track of
    how much of the well has been loaded and which well to prompt the user with
    :param request: signal call that this function has been called
    :return barcode: captured barcode
    :return next_well: Since the plate barcode has been recorded here, the next well will always be A1
    """
    barcode = subprocess.check_output(['python', 'webcam_barcode_scanner.py']).decode('utf-8')
    request.session['plate'] = barcode
    request.session['last_scan'] = 'plate'
    return render(request, 'test_results/start_platemap.html', {'barcode': barcode, 'next_well': 'A1'})


@login_required
def barcode_capture(request):
    """
    Redirected here after the plate barcode has been scanned. User will be prompted to scan a barcode until the second
    to last well is scanned. After scanning the last well, database records for each barcode will be created and the
    user will be routed to a success page.
    :param request: signal call that this function has been called
    :return f: captured barcode
    """
    print(request.session.keys())
    print(request.session['last_scan'])
    barcode = subprocess.check_output(['python', 'webcam_barcode_scanner.py']).decode('utf-8')

    # Checks if the last scanned barcode was for a plate. In that case, the current scan is for the first well 'A1'.
    if request.session['last_scan'] == 'plate':
        request.session['A1'] = barcode
        request.session['last_scan'] = 'A1'
        return render(request, 'test_results/barcode_capture.html', {'barcode': barcode, 'current_well': 'A1',
                                                                     'next_well': 'A2'})
    # Checks if the last scanned barcode was for well A5 (which is the second to last well in the plate). In that case,
    # the current scan is for the last well 'B5'.
    elif request.session['last_scan'] == 'A5':
        request.session['B5'] = barcode
        request.session['last_scan'] = 'B5'
        return render(request, 'test_results/platemap.html', {'barcode': barcode})
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
        return render(request, 'test_results/barcode_capture.html', {'barcode': barcode, 'current_well': well,
                                                                     'next_well': next_well})


@login_required
def platemap(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
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

    print(script)

    return render(request, 'test_results/platemap.html', {'script': script, 'div': div})


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
        for k in ['barcode', 'technician', 'lab', 'collection_date', 'processing_date']:
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
            elif request.GET[k] != '' and k == 'collection_date':
                if q == '':
                    q = test_results.objects.filter(collection_date=request.GET[k])
                else:
                    q = q.filter(collection_date=request.GET[k])
            elif request.GET[k] != '' and k == 'processing_date':
                if q == '':
                    q = test_results.objects.filter(processing_date=request.GET[k])
                else:
                    q = q.filter(processing_date=request.GET[k])
            else:
                continue

        if q == '':
            return render(request, 'test_results/search_record_form_error.html')
        else:
            table = test_resultsTable(q)
            return render(request, 'test_results/record_search.html', {'table': table})
