from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from django.conf import settings
from django.views.decorators.http import require_POST
import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Registrace fontu podporujícího diakritiku
font_path = os.path.join(settings.BASE_DIR, 'logistika', 'static', 'fonts', 'DejaVuSans.ttf')
font_path_bold = os.path.join(settings.BASE_DIR, 'logistika', 'static', 'fonts', 'DejaVuSans-Bold.ttf')
pdfmetrics.registerFont(TTFont('DejaVu', font_path))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', font_path_bold))
from django.db.models import Count, Sum, F, ExpressionWrapper, DecimalField, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Preprava, Partner, Dokument, Holiday
from .forms import PrepravaForm, PartnerForm, DopravceAssignForm, StavChangeForm, DokumentForm, PrepravaFilterForm

@login_required
def dashboard(request):
    # Původní statistiky stavů
    nove = Preprava.objects.filter(stav='nova').count()
    planovane = Preprava.objects.filter(stav='planovana').count()
    probihajici = Preprava.objects.filter(stav='probiha').count()
    k_fakturaci = Preprava.objects.filter(stav='fakturace').count()

    # Poslední realizované přepravy (od plánovaných dál)
    realizovane_stavy = ['planovana', 'probiha', 'dokoncena', 'fakturace', 'uzavrena']
    posledni_realizovane = Preprava.objects.filter(stav__in=realizovane_stavy).order_by('-datum_vytvoreni')[:10]

    # Výpočty marží
    now = timezone.now()
    today = now.date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    def calculate_marze(queryset):
        # Vytvoříme anotaci pro marži, ale pouze tam, kde jsou měny stejné
        marze_query = queryset.filter(mena_zakaznik=F('mena_dopravce')).annotate(
            hmotnost_t=ExpressionWrapper(
                Coalesce(F('finalni_hmotnost_kg'), F('odhadovana_hmotnost_kg')) / 1000.0,
                output_field=DecimalField()
            )
        ).annotate(
            celkova_cena=F('hmotnost_t') * F('cena_za_tunu_zakaznik'),
            celkovy_naklad=F('hmotnost_t') * F('naklad_za_tunu_dopravce')
        ).annotate(
            marze=F('celkova_cena') - F('celkovy_naklad')
        )
        # Sečteme marže pro CZK a EUR odděleně
        marze_czk = marze_query.filter(mena_zakaznik='CZK').aggregate(total=Coalesce(Sum('marze'), Decimal('0.00')))['total']
        marze_eur = marze_query.filter(mena_zakaznik='EUR').aggregate(total=Coalesce(Sum('marze'), Decimal('0.00')))['total']
        return marze_czk, marze_eur

    marze_den_czk, marze_den_eur = calculate_marze(Preprava.objects.filter(datum_vytvoreni__date=today, stav__in=realizovane_stavy))
    marze_tyden_czk, marze_tyden_eur = calculate_marze(Preprava.objects.filter(datum_vytvoreni__date__gte=start_of_week, stav__in=realizovane_stavy))
    marze_mesic_czk, marze_mesic_eur = calculate_marze(Preprava.objects.filter(datum_vytvoreni__date__gte=start_of_month, stav__in=realizovane_stavy))

    # Nejlepší zákazníci a dopravci
    nejlepsi_zakaznici = Partner.objects.filter(prepravy_zakaznik__isnull=False).annotate(
        pocet_preprav=Count('prepravy_zakaznik')
    ).order_by('-pocet_preprav')[:5]

    nejlepsi_dopravci = Partner.objects.filter(prepravy_dopravce__isnull=False, prepravy_dopravce__stav__in=realizovane_stavy).annotate(
        pocet_preprav=Count('prepravy_dopravce')
    ).order_by('-pocet_preprav')[:5]

    context = {
        'nove': nove,
        'planovane': planovane,
        'probihajici': probihajici,
        'k_fakturaci': k_fakturaci,
        'posledni_realizovane': posledni_realizovane,
        'marze_den_czk': marze_den_czk,
        'marze_den_eur': marze_den_eur,
        'marze_tyden_czk': marze_tyden_czk,
        'marze_tyden_eur': marze_tyden_eur,
        'marze_mesic_czk': marze_mesic_czk,
        'marze_mesic_eur': marze_mesic_eur,
        'nejlepsi_zakaznici': nejlepsi_zakaznici,
        'nejlepsi_dopravci': nejlepsi_dopravci,
    }
    return render(request, 'logistika/dashboard.html', context)

@login_required
def seznam_preprav(request):
    base_query = Preprava.objects.select_related('zakaznik').all()
    form = PrepravaFilterForm(request.GET)

    if form.is_valid():
        if form.cleaned_data['referencni_cislo']:
            base_query = base_query.filter(referencni_cislo__icontains=form.cleaned_data['referencni_cislo'])
        if form.cleaned_data['zakaznik']:
            base_query = base_query.filter(zakaznik=form.cleaned_data['zakaznik'])
        if form.cleaned_data['stav']:
            base_query = base_query.filter(stav=form.cleaned_data['stav'])

    aktivni_stavy = ['nova', 'planovana', 'probiha']
    archivni_stavy = ['dokoncena', 'fakturace', 'uzavrena', 'neprodano']

    aktivni_prepravy = base_query.filter(stav__in=aktivni_stavy).order_by('-datum_vytvoreni')
    archivni_prepravy = base_query.filter(stav__in=archivni_stavy).order_by('-datum_vytvoreni')

    context = {
        'form': form,
        'aktivni_prepravy': aktivni_prepravy,
        'archivni_prepravy': archivni_prepravy
    }
    return render(request, 'logistika/seznam_preprav.html', context)

@login_required
def seznam_zakazniku(request):
    query = request.GET.get('q')
    zakaznici = Partner.objects.filter(typ_partnera__in=['zakaznik', 'zakaznik_dopravce'])

    if query:
        zakaznici = zakaznici.filter(
            Q(nazev__icontains=query) |
            Q(ic__icontains=query) |
            Q(dic__icontains=query) |
            Q(kontaktni_osoba__icontains=query) |
            Q(email__icontains=query) |
            Q(telefon__icontains=query)
        ).distinct()

    zakaznici = zakaznici.order_by('nazev')
    return render(request, 'logistika/seznam_partneru.html', {'partneri': zakaznici, 'typ': 'Zákazníci', 'search_query': query})

@login_required
def seznam_dopravcu(request):
    query = request.GET.get('q')
    dopravci = Partner.objects.filter(typ_partnera__in=['dopravce', 'zakaznik_dopravce'])

    if query:
        dopravci = dopravci.filter(
            Q(nazev__icontains=query) |
            Q(ic__icontains=query) |
            Q(dic__icontains=query) |
            Q(kontaktni_osoba__icontains=query) |
            Q(email__icontains=query) |
            Q(telefon__icontains=query)
        ).distinct()

    dopravci = dopravci.order_by('nazev')
    return render(request, 'logistika/seznam_partneru.html', {'partneri': dopravci, 'typ': 'Dopravci', 'search_query': query})

@login_required
def preprava_detail(request, pk):
    preprava = get_object_or_404(Preprava, pk=pk)

    if 'assign_dopravce' in request.POST:
        dopravce_form = DopravceAssignForm(request.POST, instance=preprava)
        if dopravce_form.is_valid():
            dopravce_form.save()
            messages.success(request, 'Dopravce byl úspěšně přiřazen.')
            return redirect('preprava_detail', pk=pk)
    else:
        dopravce_form = DopravceAssignForm(instance=preprava)

    if 'change_stav' in request.POST:
        stav_form = StavChangeForm(request.POST, instance=preprava)
        if stav_form.is_valid():
            stav_form.save()
            messages.success(request, 'Stav přepravy byl změněn.')
            return redirect('preprava_detail', pk=pk)
    else:
        stav_form = StavChangeForm(instance=preprava)

    if 'upload_dokument' in request.POST:
        dokument_form = DokumentForm(request.POST, request.FILES)
        if dokument_form.is_valid():
            dokument = dokument_form.save(commit=False)
            dokument.preprava = preprava
            dokument.save()
            messages.success(request, f'Dokument "{dokument.nazev}" byl úspěšně nahrán.')
            return redirect('preprava_detail', pk=pk)
    else:
        dokument_form = DokumentForm()

    context = {
        'preprava': preprava,
        'dopravce_form': dopravce_form,
        'stav_form': stav_form,
        'dokument_form': dokument_form,
    }
    return render(request, 'logistika/preprava_detail.html', context)

@login_required
def preprava_create(request):
    if request.method == 'POST':
        form = PrepravaForm(request.POST)
        if form.is_valid():
            preprava = form.save()
            messages.success(request, f'Přeprava {preprava.referencni_cislo} byla úspěšně vytvořena.')
            return redirect('seznam_preprav')
    else:
        form = PrepravaForm()
    return render(request, 'logistika/preprava_form.html', {'form': form, 'title': 'Vytvořit novou přepravu'})

@login_required
def preprava_update(request, pk):
    preprava = get_object_or_404(Preprava, pk=pk)
    if request.method == 'POST':
        form = PrepravaForm(request.POST, instance=preprava)
        if form.is_valid():
            form.save()
            messages.success(request, f'Přeprava {preprava.referencni_cislo} byla úspěšně upravena.')
            return redirect('preprava_detail', pk=preprava.pk)
    else:
        form = PrepravaForm(instance=preprava)
    return render(request, 'logistika/preprava_form.html', {'form': form, 'title': f'Upravit přepravu {preprava.referencni_cislo}'})

@login_required
def generovat_podklady_pdf(request, pk):
    preprava = get_object_or_404(Preprava.objects.select_related('zakaznik', 'dopravce'), pk=pk)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont('DejaVu', 10)

    # Výška stránky
    height = letter[1]

    # --- Helper funkce pro kreslení --- #
    def draw_section(title, data, y_start):
        c.setFont("DejaVu-Bold", 16)
        c.drawString(inch, y_start, title)
        c.line(inch, y_start - 5, letter[0] - inch, y_start - 5)
        y = y_start - 30
        c.setFont("DejaVu", 10)
        line_height = 15
        for key, value in data.items():
            c.drawString(inch, y, f"{key}:")
            
            # Zpracování víceřádkového textu
            lines = str(value).splitlines()
            if not lines:
                lines = ['-'] # Zobrazí pomlčku, pokud je hodnota prázdná

            # Vykreslení prvního řádku na stejné úrovni jako klíč
            c.drawString(inch * 3, y, lines[0])
            
            # Vykreslení dalších řádků pod sebou
            for i, line in enumerate(lines[1:]):
                y -= line_height
                c.drawString(inch * 3, y, line)

            y -= line_height
        return y + line_height # Vrátí pozici pro další sekci

    # --- Titulek --- #
    c.setFont("DejaVu-Bold", 18)
    c.drawCentredString(letter[0] / 2, 1 * inch, f"Podklady pro přepravu {preprava.referencni_cislo}")

    y_position = height - 1.5 * inch

    # --- Detaily přepravy (společné) --- #
    preprava_data = {
        "Místo nakládky": preprava.misto_nakladky,
        "Datum a čas nakládky": preprava.datum_cas_nakladky,
        "Místo vykládky": preprava.misto_vykladky,
        "Datum a čas vykládky": preprava.datum_cas_vykladky,
        "Zboží": preprava.popis_zbozi,
        "Typ vozidla": preprava.get_typ_vozidla_display(),
        "Odhadovaná hmotnost": f"{preprava.odhadovana_hmotnost_kg} kg",
        "Finální hmotnost": f"{preprava.finalni_hmotnost_kg} kg" if preprava.finalni_hmotnost_kg else "-",
    }
    y_position = draw_section("Informace o přepravě", preprava_data, y_position)

    # --- Podklady pro objednávku dopravci --- #
    dopravce_data = {
        "Dopravce": preprava.dopravce.nazev if preprava.dopravce else "NEPŘIŘAZEN",
        "Kontaktní osoba": preprava.dopravce.kontaktni_osoba if preprava.dopravce else "-",
        "Telefon": preprava.dopravce.telefon if preprava.dopravce else "-",
        "E-mail": preprava.dopravce.email if preprava.dopravce else "-",
        "Náklad za tunu": f"{preprava.naklad_za_tunu_dopravce} {preprava.get_mena_dopravce_display()}" if preprava.naklad_za_tunu_dopravce else "-",
        "Celkový náklad": f"{preprava.celkovy_naklad_dopravce} {preprava.get_mena_dopravce_display()}" if preprava.celkovy_naklad_dopravce else "-",
    }
    y_position = draw_section("Podklady pro objednávku dopravci", dopravce_data, y_position - 0.5 * inch)

    # --- Podklady pro fakturaci zákazníkovi --- #
    zakaznik_data = {
        "Zákazník": preprava.zakaznik.nazev,
        "IČ": preprava.zakaznik.ic,
        "DIČ": preprava.zakaznik.dic,
        "Fakturační údaje": preprava.zakaznik.fakturacni_udaje or preprava.zakaznik.adresa,
        "Splatnost faktur (dní)": preprava.zakaznik.splatnost_faktur_dny or "-",
        "Cena za tunu": f"{preprava.cena_za_tunu_zakaznik} {preprava.get_mena_zakaznik_display()}",
        "Celková cena": f"{preprava.celkova_cena_zakaznik} {preprava.get_mena_zakaznik_display()}",
    }
    draw_section("Podklady pro fakturaci zákazníkovi", zakaznik_data, y_position - 0.5 * inch)

    c.showPage()
    c.save()
    buf.seek(0)

    return FileResponse(buf, as_attachment=True, filename=f'podklady_{preprava.referencni_cislo}.pdf')

@login_required
def partner_update(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == 'POST':
        form = PartnerForm(request.POST, instance=partner)
        if form.is_valid():
            form.save()
            messages.success(request, f'Partner "{partner.nazev}" byl úspěšně upraven.')
            if partner.typ_partnera == 'zakaznik':
                return redirect('seznam_zakazniku')
            else:
                return redirect('seznam_dopravcu')
    else:
        form = PartnerForm(instance=partner)
    return render(request, 'logistika/partner_form.html', {'form': form, 'title': f'Upravit partnera {partner.nazev}'})

@login_required
def export_aktivnich_preprav(request):
    volne_prepravy = Preprava.objects.filter(stav='nova').order_by('datum_cas_nakladky')
    context = {
        'prepravy': volne_prepravy
    }
    return render(request, 'logistika/export_preprav.html', context)

@login_required
@require_POST
def dokument_delete(request, pk):
    dokument = get_object_or_404(Dokument, pk=pk)
    preprava_pk = dokument.preprava.pk
    dokument.soubor.delete(save=False) # Smaže soubor
    dokument.delete() # Smaže záznam z DB
    messages.success(request, f'Dokument "{dokument.nazev}" byl úspěšně smazán.')
    return redirect('preprava_detail', pk=preprava_pk)

@login_required
@require_POST
def preprava_delete(request, pk):
    preprava = get_object_or_404(Preprava, pk=pk)
    preprava.delete()
    messages.success(request, f'Přeprava {preprava.referencni_cislo} byla úspěšně smazána.')
    return redirect('seznam_preprav')

@login_required
def partner_create(request):
    if request.method == 'POST':
        form = PartnerForm(request.POST)
        if form.is_valid():
            partner = form.save()
            messages.success(request, f'Partner "{partner.nazev}" byl úspěšně vytvořen.')
            if partner.typ_partnera == 'zakaznik':
                return redirect('seznam_zakazniku')
            else:
                return redirect('seznam_dopravcu')
    else:
        form = PartnerForm()
    return render(request, 'logistika/partner_form.html', {'form': form, 'title': 'Vytvořit nového partnera'})


@login_required
def seznam_svatku(request):
    holidays = Holiday.objects.order_by('date', 'country_code')
    context = {
        'holidays': holidays,
    }
    return render(request, 'logistika/holidays_list.html', context)
