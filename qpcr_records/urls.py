from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('barcode_list_upload/', views.barcode_list_upload, name='barcode_list_upload'),
    path('unknown_barcode/', views.unknown_barcode, name='unknown_barcode'),
    path('scan_plate_1_2_barcode/', views.scan_plate_1_2_barcode, name='scan_plate_1_2_barcode'),
    path('search_record_form/', views.search_record_form, name='search_record_form'),
    path('record_search/', views.record_search, name='record_search'),
    path('perform_safety_check/', views.perform_safety_check, name='perform_safety_check'),
    path('barcode_capture/', views.barcode_capture, name='barcode_capture'),
    path('update_existing_records/', views.update_existing_records, name='update_existing_records'),
    path('scan_plate_2_3_barcode/', views.scan_plate_2_3_barcode, name='scan_plate_2_3_barcode'),
    path('scan_plate_arrayed_plate_barcode/', views.scan_plate_arrayed_plate_barcode, name='scan_plate_arrayed_plate_barcode'),
    path('scan_plate_5_6_barcode/', views.scan_plate_5_6_barcode, name='scan_plate_5_6_barcode'),
    path('track_samples_form/', views.track_samples_form, name='track_samples_form'),
    path('track_samples/', views.track_samples, name='track_samples'),
    path('check_information/', views.check_information, name='check_information'),
    path('upload_qpcr_results/', views.upload_qpcr_results, name='upload_qpcr_results'),
    path('review_results/', views.review_results, name='review_results'),
    path('qpcr_plate_id_to_review/', views.qpcr_plate_id_to_review, name='qpcr_plate_id_to_review'),
    path('search_record_form_error/', views.search_record_form_error, name='search_record_form_error'),
]
