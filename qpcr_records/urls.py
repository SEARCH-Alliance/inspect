from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('barcode_list_upload/', views.barcode_list_upload, name='barcode_list_upload'),
    path('sample_plate_capture/', views.sample_plate_capture, name='sample_plate_capture'),
    path('search/', views.search, name='search'),
    path('search_results/', views.search_results, name='search_results'),
    path('perform_safety_check/', views.perform_safety_check, name='perform_safety_check'),
    path('barcode_capture/', views.barcode_capture, name='barcode_capture'),
    path('update_existing_records/', views.update_existing_records, name='update_existing_records'),
    path('rna_plate_capture/', views.rna_plate_capture, name='rna_plate_capture'),
    path('rwp_plate_capture/', views.rwp_plate_capture, name='rwp_plate_capture'),
    path('qpcr_plate_capture/', views.qpcr_plate_capture, name='qpcr_plate_capture'),
    path('upload_qpcr_results/', views.upload_qpcr_results, name='upload_qpcr_results'),
    path('review_results/', views.review_results, name='review_results'),
    path('qpcr_plate_id_to_review/', views.qpcr_plate_id_to_review, name='qpcr_plate_id_to_review'),
    path('sample_release/', views.sample_release, name='sample_release'),
    path('discard_storage_bag/', views.discard_storage_bag, name='discard_storage_bag')
]
