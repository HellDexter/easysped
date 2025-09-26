# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Preprava, Partner, Dokument, Holiday

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('nazev', 'ic', 'typ_partnera')
    search_fields = ('nazev', 'ic')

@admin.register(Preprava)
class PrepravaAdmin(admin.ModelAdmin):
    list_display = ('referencni_cislo', 'zakaznik', 'dopravce', 'stav', 'datum_cas_nakladky')
    search_fields = ('referencni_cislo', 'zakaznik__nazev', 'dopravce__nazev')
    list_filter = ('stav', 'typ_vozidla')
    autocomplete_fields = ['zakaznik', 'dopravce']


@admin.register(Dokument)
class DokumentAdmin(admin.ModelAdmin):
    list_display = ('nazev', 'get_preprava_info', 'datum_nahrani')
    search_fields = ('nazev', 'preprava__referencni_cislo', 'preprava__zakaznik__nazev')
    list_filter = ('preprava',)
    autocomplete_fields = ['preprava']

    @admin.display(description='Přeprava', ordering='preprava')
    def get_preprava_info(self, obj):
        if obj.preprava:
            return f"{obj.preprava.referencni_cislo} ({obj.preprava.zakaznik.nazev})"
        return "N/A"


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'name', 'country_code', 'regions')
    list_filter = ('country_code',)
    search_fields = ('name', 'country_code', 'regions')
    ordering = ('date',)
