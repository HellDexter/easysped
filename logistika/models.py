from django.db import models
from django.utils import timezone
from decimal import Decimal

class Partner(models.Model):
    TYP_PARTNERA_CHOICES = [
        ('zakaznik', 'Zákazník'),
        ('dopravce', 'Dopravce'),
        ('zakaznik_dopravce', 'Zákazník i dopravce'),
    ]

    nazev = models.CharField(max_length=200)
    ic = models.CharField(max_length=20, unique=True, blank=True, null=True)
    dic = models.CharField(max_length=20, blank=True)
    adresa = models.TextField()
    kontaktni_osoba = models.CharField(max_length=100, blank=True, verbose_name="Kontaktní osoba")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    telefon = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    dalsi_kontakty = models.TextField(blank=True, verbose_name="Další kontakty (jméno, e-mail, tel.)")
    certifikace = models.TextField(blank=True, verbose_name="Certifikace")
    typy_vozidel = models.TextField(blank=True, verbose_name="Typy vozidel")
    fakturacni_udaje = models.TextField(blank=True, verbose_name="Fakturační údaje")
    splatnost_faktur_dny = models.IntegerField(null=True, blank=True, verbose_name="Splatnost faktur (dní)")
    typ_partnera = models.CharField(max_length=20, choices=TYP_PARTNERA_CHOICES, verbose_name="Typ partnera")

    class Meta:
        verbose_name = 'Partner'
        verbose_name_plural = 'Partneři'

    def __str__(self):
        return self.nazev

class Dokument(models.Model):
    preprava = models.ForeignKey('Preprava', related_name='dokumenty', on_delete=models.CASCADE)
    nazev = models.CharField(max_length=200)
    soubor = models.FileField(upload_to='dokumenty/%Y/%m/%d/')
    datum_nahrani = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dokument'
        verbose_name_plural = 'Dokumenty'

    def __str__(self):
        return self.nazev

class Preprava(models.Model):
    TYP_VOZIDLA_CHOICES = [
        ('SKL', 'Sklápěč'),
        ('WF', 'Walking Floor'),
        ('SKL_WF', 'Sklápěč/Walking Floor'),
    ]

    MENA_CHOICES = [
        ('CZK', 'Kč'),
        ('EUR', '€'),
    ]

    STAV_CHOICES = [
        ('nova', 'Nová'),
        ('planovana', 'Plánovaná'),
        ('probiha', 'Probíhá'),
        ('dokoncena', 'Dokončená'),
        ('fakturace', 'K fakturaci'),
        ('uzavrena', 'Uzavřená'),
        ('neprodano', 'Neprodáno'),
    ]

    referencni_cislo = models.CharField(max_length=50, unique=True, blank=True)
    zakaznik = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name='prepravy_zakaznik', limit_choices_to={'typ_partnera__in': ['zakaznik', 'zakaznik_dopravce']})
    dopravce = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name='prepravy_dopravce', null=True, blank=True, limit_choices_to={'typ_partnera__in': ['dopravce', 'zakaznik_dopravce']})
    misto_nakladky = models.TextField()
    datum_cas_nakladky = models.CharField(max_length=50, verbose_name="Datum a čas nakládky")
    misto_vykladky = models.TextField()
    datum_cas_vykladky = models.CharField(max_length=50, verbose_name="Datum a čas vykládky")
    odesilatel_cmr = models.TextField(blank=True, verbose_name="Odesílatel CMR")
    prijemce_cmr = models.TextField(blank=True, verbose_name="Příjemce CMR")
    popis_zbozi = models.TextField()
    typ_vozidla = models.CharField(max_length=10, choices=TYP_VOZIDLA_CHOICES, default='SKL', verbose_name="Typ vozidla")
    odhadovana_hmotnost_kg = models.IntegerField(default=25000, verbose_name="Odhadovaná hmotnost (kg)")
    poznamka_odhad_hmotnost = models.CharField(max_length=255, blank=True, verbose_name="Poznámka k odhad. hmotnosti")
    finalni_hmotnost_kg = models.IntegerField(null=True, blank=True, verbose_name="Finální hmotnost (kg)")
    poznamka_final_hmotnost = models.CharField(max_length=255, blank=True, verbose_name="Poznámka k finální hmotnosti")
    cena_za_tunu_zakaznik = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Cena za tunu pro zákazníka")
    mena_zakaznik = models.CharField(max_length=3, choices=MENA_CHOICES, default='CZK', verbose_name="Měna (zákazník)")
    naklad_za_tunu_dopravce = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Náklad za tunu pro dopravce")
    mena_dopravce = models.CharField(max_length=3, choices=MENA_CHOICES, default='CZK', verbose_name="Měna (dopravce)")
    stav = models.CharField(max_length=20, choices=STAV_CHOICES, default='nova')
    datum_vytvoreni = models.DateTimeField(auto_now_add=True)
    @property
    def celkova_cena_zakaznik(self):
        hmotnost_t = (self.finalni_hmotnost_kg or self.odhadovana_hmotnost_kg) / 1000
        if self.cena_za_tunu_zakaznik and hmotnost_t > 0:
            return self.cena_za_tunu_zakaznik * Decimal(hmotnost_t)
        return Decimal('0.00')

    @property
    def celkovy_naklad_dopravce(self):
        hmotnost_t = (self.finalni_hmotnost_kg or self.odhadovana_hmotnost_kg) / 1000
        if self.naklad_za_tunu_dopravce and hmotnost_t > 0:
            return self.naklad_za_tunu_dopravce * Decimal(hmotnost_t)
        return Decimal('0.00')


    @property
    def marze(self):
        if self.celkova_cena_zakaznik and self.celkovy_naklad_dopravce:
            return self.celkova_cena_zakaznik - self.celkovy_naklad_dopravce
        return Decimal('0.00')

    def save(self, *args, **kwargs):
        if not self.referencni_cislo:
            rok = timezone.now().year
            posledni_preprava = Preprava.objects.filter(referencni_cislo__startswith=f'JAFA-{rok}').order_by('referencni_cislo').last()
            if posledni_preprava:
                posledni_cislo = int(posledni_preprava.referencni_cislo.split('-')[-1])
                nove_cislo = posledni_cislo + 1
            else:
                nove_cislo = 1
            self.referencni_cislo = f'JAFA-{rok}-{nove_cislo:04d}'
        super().save(*args, **kwargs)

    def get_stav_badge_class(self):
        if self.stav == 'nova':
            return 'bg-primary'
        elif self.stav == 'planovana':
            return 'bg-warning'
        elif self.stav == 'probiha':
            return 'bg-success text-dark'
        elif self.stav == 'dokoncena':
            return 'bg-success'
        elif self.stav == 'fakturace':
            return 'bg-info'
        elif self.stav == 'uzavrena':
            return 'bg-secondary'
        elif self.stav == 'neprodano':
            return 'bg-danger'
        return 'bg-light'

    class Meta:
        verbose_name = 'Přeprava'
        verbose_name_plural = 'Přepravy'

    def __str__(self):
        return self.referencni_cislo


class Holiday(models.Model):
    date = models.DateField()
    name = models.CharField(max_length=150)
    country_code = models.CharField(max_length=2)
    regions = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Svatek"
        verbose_name_plural = "Svátky"
        ordering = ["date", "country_code", "name"]
        unique_together = ("date", "country_code", "name")

    def __str__(self):
        return f"{self.date} - {self.name} ({self.country_code})"
