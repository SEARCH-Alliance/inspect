from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('new_record_form/', views.new_record_form, name='new_record_form'),
    path('success/', views.create_record, name='success'),
    path('failure/', views.create_record, name='failure'),
    path('search_record_form/', views.search_record_form, name='search_record_form'),
    path('record_search/', views.record_search, name='record_search'),
]
