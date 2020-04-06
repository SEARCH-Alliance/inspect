from django.contrib import admin
from .models import test_results


class test_overlapAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'fake_name', 'plate_1_id', 'sampling_date', 'plate_2_id', 'plate_2_well',
                    'rna_extraction_protocol', 'plate_3_id', 'plate_3_well', 'plate_4_id', 'plate_4_well', 'plate_5_id',
                    'plate_5_well', 'plate_6_id', 'plate_6_well', 'ms2_ct_value', 'ms2_ct_mean_value',
                    'ms2_ct_sd_value', 'n_ct_value', 'n_ct_mean_value', 'n_ct_sd_value', 'orf1ab_ct_value',
                    'orf1ab_ct_mean_value', 'orf1ab_ct_sd_value', 's_ct_value', 's_ct_mean_value', 's_ct_sd_value',
                    'technician', 'lab', 'institute', 'pcr_results_csv', 'search_fields')


admin.site.register(test_results, test_overlapAdmin)
