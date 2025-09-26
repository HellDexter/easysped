from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('prepravy/', views.seznam_preprav, name='seznam_preprav'),
    path('prepravy/nova/', views.preprava_create, name='preprava_create'),
    path('prepravy/<int:pk>/', views.preprava_detail, name='preprava_detail'),
    path('prepravy/<int:pk>/podklady-pdf/', views.generovat_podklady_pdf, name='podklady_pdf'),
    path('prepravy/<int:pk>/upravit/', views.preprava_update, name='preprava_update'),
    path('partneri/novy/', views.partner_create, name='partner_create'),
    path('partneri/<int:pk>/upravit/', views.partner_update, name='partner_update'),
    path('zakaznici/', views.seznam_zakazniku, name='seznam_zakazniku'),
    path('dopravci/', views.seznam_dopravcu, name='seznam_dopravcu'),
    path('prepravy/export/', views.export_aktivnich_preprav, name='export_preprav'),
    path('dokument/<int:pk>/smazat/', views.dokument_delete, name='dokument_delete'),
    path('preprava/<int:pk>/smazat/', views.preprava_delete, name='preprava_delete'),
    path('svatky/', views.seznam_svatku, name='seznam_svatku'),
]
