from django import forms
from .models import Preprava, Partner, Dokument

class PrepravaForm(forms.ModelForm):
    class Meta:
        model = Preprava
        fields = [
            'zakaznik', 'misto_nakladky', 'datum_cas_nakladky',
            'misto_vykladky', 'datum_cas_vykladky', 'odesilatel_cmr', 'prijemce_cmr', 'typ_vozidla', 'popis_zbozi',
            'odhadovana_hmotnost_kg', 'poznamka_odhad_hmotnost', 'finalni_hmotnost_kg', 'poznamka_final_hmotnost',
            'cena_za_tunu_zakaznik', 'mena_zakaznik', 'naklad_za_tunu_dopravce', 'mena_dopravce'
        ]
        widgets = {
            'zakaznik': forms.Select(attrs={'class': 'form-select'}),
            'misto_nakladky': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'datum_cas_nakladky': forms.TextInput(attrs={'class': 'form-control'}),
            'misto_vykladky': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'datum_cas_vykladky': forms.TextInput(attrs={'class': 'form-control'}),
            'odesilatel_cmr': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prijemce_cmr': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'typ_vozidla': forms.Select(attrs={'class': 'form-select'}),
            'popis_zbozi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'odhadovana_hmotnost_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'poznamka_odhad_hmotnost': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Poznámka k odhad. hmotnosti'}),
            'finalni_hmotnost_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'poznamka_final_hmotnost': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Poznámka k finální hmotnosti'}),
            'cena_za_tunu_zakaznik': forms.NumberInput(attrs={'class': 'form-control'}),
            'mena_zakaznik': forms.Select(attrs={'class': 'form-select'}),
            'naklad_za_tunu_dopravce': forms.NumberInput(attrs={'class': 'form-control'}),
            'mena_dopravce': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['zakaznik'].queryset = Partner.objects.filter(typ_partnera__in=['zakaznik', 'zakaznik_dopravce']).order_by('nazev')
        self.fields['finalni_hmotnost_kg'].required = False
        self.fields['naklad_za_tunu_dopravce'].required = False
        self.fields['cena_za_tunu_zakaznik'].required = False

class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = [
            'nazev', 'ic', 'dic', 'adresa', 'typ_partnera',
            'kontaktni_osoba', 'email', 'telefon', 'dalsi_kontakty',
            'certifikace', 'typy_vozidel', 'fakturacni_udaje', 'splatnost_faktur_dny'
        ]
        widgets = {
            'nazev': forms.TextInput(attrs={'class': 'form-control'}),
            'ic': forms.TextInput(attrs={'class': 'form-control'}),
            'dic': forms.TextInput(attrs={'class': 'form-control'}),
            'adresa': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'typ_partnera': forms.Select(attrs={'class': 'form-select'}),
            'kontaktni_osoba': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control'}),
            'dalsi_kontakty': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'certifikace': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'typy_vozidel': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fakturacni_udaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'splatnost_faktur_dny': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ic'].required = False
        self.fields['dic'].required = False

class DopravceAssignForm(forms.ModelForm):
    class Meta:
        model = Preprava
        fields = ['dopravce']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dopravce'].queryset = Partner.objects.filter(typ_partnera__in=['dopravce', 'zakaznik_dopravce']).order_by('nazev')
        self.fields['dopravce'].label = "Přiřadit dopravce"

class StavChangeForm(forms.ModelForm):
    class Meta:
        model = Preprava
        fields = ['stav']
        widgets = {
            'stav': forms.Select(attrs={'class': 'form-select'})
        }

class DokumentForm(forms.ModelForm):
    class Meta:
        model = Dokument
        fields = ['nazev', 'soubor']

class PrepravaFilterForm(forms.Form):
    referencni_cislo = forms.CharField(label='Referenční číslo', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    zakaznik = forms.ModelChoiceField(
        queryset=Partner.objects.filter(typ_partnera__in=['zakaznik', 'zakaznik_dopravce']),
        required=False,
        label='Zákazník',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    stav = forms.ChoiceField(
        choices=[('', '---------')] + Preprava.STAV_CHOICES,
        required=False,
        label='Stav',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
