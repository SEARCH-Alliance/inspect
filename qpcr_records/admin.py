from django.contrib import admin
from .models import test_results


class test_overlapAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'sample_box_number', 'sample_box_x_position', 'sample_box_y_position', 'plate_id',
                    'sampling_plate_well', 'sampling_date', 'rna_extraction_protocol', 'qpcr_n1_well', 'qpcr_n2_well',
                    'qpcr_rp_well', 'qpcr_instrument', 'technician', 'lab', 'institute', 'pcr_results_csv',
                    'pcr_platemap_csv')
    search_fields = ('barcode', 'technician', 'samplIng_date', 'plate_id')


admin.site.register(test_results, test_overlapAdmin)
