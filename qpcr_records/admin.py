from django.contrib import admin
from .models import test_results


class test_overlapAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'fake_name', 'ssp_id', 'ssp_well', 'sampling_date', 'sep_id', 'sep_well',
                    'andersson_lab_frz_id', 'sample_extraction_technician1', 'sample_extraction_technician1_lab',
                    'sample_extraction_technician1_institute', 'sample_extraction_technician2',
                    'sample_extraction_technician2_lab', 'sample_extraction_technician2_institute', 'ms2_lot_id',
                    'epm_id', 'rna_extract_reagent_ids', 'kfr_id', 'rep_id', 'rep_well', 'rsp_id', 'rsp_well',
                    'knight_lab_frz_id', 'rwp_id', 'rwp_well', 'rna_extraction_technician',
                    'rna_extraction_technician_lab', 'rna_extraction_technician_institute', 'qrp_id', 'qrp_well',
                    'probe_mix_id', 'enzyme_mix_id', 'mhv_id', 'qs5_id', 'laurent_lab_frz_id', 'qpcr_technician',
                    'qpcr_technician_lab', 'qpcr_technician_institute', 'ms2_ct_value', 'n_ct_value', 'orf1ab_ct_value',
                    's_ct_value', 'decision_tree_results', 'final_results', 'pcr_results_csv', 'eds_results_csv',
                    'file_transfer_status')


admin.site.register(test_results, test_overlapAdmin)
