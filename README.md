# EasySped

Moderní interní webová aplikace pro malou/spediční firmu. Umožňuje evidovat přepravy, zákazníky, dopravce a pracovat s přehledným dashboardem. Aplikace je postavena na Django 4.2, připravena pro lokální vývoj i nasazení na Render.com.

---

## Vlastnosti
- **Přihlášení a ochrana obsahu**: všechna zobrazení chráněna, přístup pouze přihlášeným uživatelům (`/accounts/login/`).
- **Přepravy / Zákazníci / Dopravci**: CRUD obrazovky, export pro dopravce.
- **Dashboard**: rychlý přehled a navigace.
- **Svátky**: boční panel se seznamem nadcházejících svátků.
- **UX**: Bootstrap 5, vlastní sidebar, kalkulačka a notifikace.

> Pozn.: Aplikace je navržena jako „single‑tenant“ – všichni uživatelé sdílí stejná data v jedné databázi.

---

## Tech stack
- Python 3.13+
- Django 4.2
- gunicorn (produkce)
- WhiteNoise (statická aktiva v produkci)
- PostgreSQL (Render)

---

## Struktura projektu (zkráceně)
```
.
├─ logistika/                  # Hlavní aplikace
│  ├─ templates/
│  ├─ static/
│  └─ management/commands/     # create_superuser_on_deploy
├─ spedice_project/            # Django project
│  ├─ settings.py
│  └─ wsgi.py
├─ render.yaml                 # Blueprint pro Render.com
├─ requirements.txt
└─ manage.py
```

---

## Lokální vývoj

1) Vytvoření a aktivace virtuálního prostředí
```bash
python -m venv .venv
# Windows PowerShell
. .venv\Scripts\Activate.ps1
```

2) Instalace závislostí
```bash
pip install -r requirements.txt
```

3) Migrace databáze a superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

4) Spuštění serveru
```bash
python manage.py runserver
```
Aplikace poběží na http://127.0.0.1:8000/

---

## Nasazení na Render.com

Repozitář obsahuje `render.yaml`, který definuje:
- webovou službu (Python, gunicorn, collectstatic, migrate, vytvoření superusera),
- PostgreSQL databázi v plánu `free`.

Kroky:
1) Nahrajte repozitář na GitHub (bez `db.sqlite3` a `media/`, viz `.gitignore`).
2) Na Render.com zvolte **New → Blueprint** a vyberte repo.
3) V sekci Environment přidejte proměnné:
   - `SECRET_KEY` (generované v render.yaml),
   - `DJANGO_SUPERUSER_USERNAME` (např. `admin`),
   - `DJANGO_SUPERUSER_PASSWORD`,
   - Render automaticky propojí `DATABASE_URL` na vaši PostgreSQL.
4) Spusťte deploy. Po nasazení otevřete přidělenou URL.

> Render vyžaduje platební kartu i pro free služby (ověření identity). Pokud v `render.yaml` zůstává `plan: free`, nic se neúčtuje.

---

## Statická a uživatelská data v produkci
- **Statická aktiva**: obsluhuje WhiteNoise; spouští se `collectstatic` do `staticfiles/`.
- **Uživatelská média (media/)**: Render má dočasné FS – nahrané soubory se při redeploy/resetu smažou. Pro trvalé ukládání doporučujeme S3/Cloud Storage (TODO).

---

## Import / Export dat

### Export (lokálně)
Vygeneruje dump všech aplikačních dat bez interních Django tabulek:
```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > datadump.json
```

### Import (na serveru Render)
V Shellu služby:
```bash
# stáhněte datadump.json (přímý link)
curl -o datadump.json "https://<direct-download-link>"

# ověřte, že nezačíná HTML
head datadump.json

# import do PostgreSQL
python manage.py loaddata datadump.json
```

---

## Důležité URL
- Přihlášení: `/accounts/login/`
- Odhlášení: `/accounts/logout/`
- Admin: `/admin/`
- Hlavní dashboard: `/`

---

## Proměnné prostředí
- `SECRET_KEY` – tajný klíč Django (produkce povinné).
- `DATABASE_URL` – připojení k PostgreSQL (Render doplní automaticky).
- `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL` (volitelně) – pro automatické vytvoření superusera při deployi.
- `RENDER_EXTERNAL_HOSTNAME` – Render přidá, používá se do `ALLOWED_HOSTS`.

---

## Licence
Uveďte licenci dle potřeby (např. MIT) nebo ponechte interní/proprietární.

---

## Podpora
Pro problémy s nasazením si projděte logy na Renderu (Build & Runtime). Pokud chyba souvisí se šablonami nebo migracemi, zkontrolujte:
- `requirements.txt` obsahuje všechny balíčky (vč. `django-crispy-forms`, `crispy-bootstrap5`).
- Migrace proběhly: `python manage.py migrate`.
- Šablona přihlášení existuje: `logistika/templates/registration/login.html`.
