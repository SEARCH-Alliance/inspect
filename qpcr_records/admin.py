from django.contrib import admin
from .models import test_results, personnel_list


class test_overlapAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'fake_name', 'ssp_id', 'ssp_well', 'sampling_date', 'sep_id', 'sep_well',
                    'andersson_lab_frz_id', 'personnel1_andersen_lab', 'personnel2_andersen_lab', 'sample_bag_id',
                    'ms2_lot_id', 'epm_id', 'rna_extract_kit_id', 'megabeads_id', 'carrier_rna_id', 'kfr_id', 'rep_id',
                    'rep_well', 'rsp_id', 'rsp_well', 'knight_lab_frz_id', 'rwp_id', 'rwp_well', 'personnel_knight_lab',
                    're_date', 'qrp_id', 'qrp_well', 'probe_mix_id', 'enzyme_mix_id', 'mhv_id', 'qs5_id',
                    'laurent_lab_frz_id', 'personnel_laurent_lab', 'qpcr_date', 'ms2_ct_value', 'n_ct_value',
                    'orf1ab_ct_value', 's_ct_value', 'decision_tree_results', 'final_results', 'is_reviewed',
                    'qpcr_results_file', 'eds_results_csv', 'file_transfer_status', 'sample_release')


class personnel_listAdmin(admin.ModelAdmin):
    list_display = ('technician_name', 'technician_lab', 'technician_institute')


admin.site.register(test_results, test_overlapAdmin)
admin.site.register(personnel_list, personnel_listAdmin)
