from django.shortcuts import render
from test_results.models import *
from test_results.forms import SearchRecords
from django.contrib.auth.decorators import login_required
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport


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
    Pass the search form to the django template
    :param request:
    :param request: signal call that this function has been called
    :return f: form to display to search forms
    """
    f = SearchRecords()
    return render(request, 'test_results/search_record_form.html', {'form': f})


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
