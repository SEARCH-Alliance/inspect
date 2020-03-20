from django.contrib import admin
from .models import test_results


class test_overlapAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'collection_site', 'collection_protocol', 'processing_protocol', 'technician', 'lab',
                    'institute', 'collection_date', 'processing_date', 'machine_model', 'reagents', 'pcr_results_csv',
                    'pcr_platemap_csv')

    search_fields = ('barcode', 'collection_site', 'technician', 'lab')


admin.site.register(test_results, test_overlapAdmin)
