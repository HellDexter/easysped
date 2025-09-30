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
- **Uživatelská média (media/)**: Produkční prostředí je nakonfigurováno pro ukládání souborů do Amazon S3 bucketu pro zajištění trvalého úložiště.

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
- `AWS_STORAGE_BUCKET_NAME` – Název vašeho S3 bucketu.
- `AWS_S3_REGION_NAME` – Region vašeho S3 bucketu (např. `eu-north-1`).
- `AWS_ACCESS_KEY_ID` – Přístupový klíč pro IAM uživatele.
- `AWS_SECRET_ACCESS_KEY` – Tajný klíč pro IAM uživatele.
- `DJANGO_DEBUG` – Nastaveno na `False` v produkci.

---

## Nastavení Amazon S3 pro ukládání souborů

Aplikace je nakonfigurována pro ukládání uživatelských souborů (média) na Amazon S3. Pro zprovoznění je nutné provést následující kroky v AWS a na Renderu.

### 1. Vytvoření S3 Bucketu
1. V AWS konzoli jděte do služby **S3**.
2. Vytvořte nový bucket (např. `easysped-media-12345`).
3. **Region**: Vyberte region, který je vám nejblíže (např. `eu-north-1` pro Stockholm).
4. V sekci **Block Public Access settings for this bucket** odškrtněte **"Block all public access"** a potvrďte.

### 2. Vytvoření IAM uživatele a politiky
Pro bezpečný přístup k S3 je doporučeno vytvořit specializovaného uživatele.

1. **Vytvoření politiky oprávnění:**
   - V AWS jděte do **IAM -> Policies -> Create policy**.
   - Přepněte na záložku **JSON** a vložte následující kód (nahraďte `NAZEV-VASEHO-BUCKETU` skutečným názvem):
     ```json
     {
         "Version": "2012-10-17",
         "Statement": [
             {
                 "Sid": "AllowS3Management",
                 "Effect": "Allow",
                 "Action": [
                     "s3:GetObject",
                     "s3:PutObject",
                     "s3:PutObjectAcl",
                     "s3:DeleteObject",
                     "s3:ListBucket",
                     "s3:GetBucketLocation"
                 ],
                 "Resource": [
                     "arn:aws:s3:::NAZEV-VASEHO-BUCKETU/*",
                     "arn:aws:s3:::NAZEV-VASEHO-BUCKETU"
                 ]
             }
         ]
     }
     ```
   - Pojmenujte politiku (např. `EasySpedS3AccessPolicy`) a vytvořte ji.

2. **Vytvoření uživatele:**
   - V **IAM -> Users -> Create user**.
   - Zadejte jméno (např. `easysped-app-user`) a pokračujte.
   - Zvolte **"Attach policies directly"** a vyberte politiku `EasySpedS3AccessPolicy`, kterou jste právě vytvořili.
   - Dokončete vytvoření uživatele.

3. **Generování přístupových klíčů:**
   - Po vytvoření uživatele přejděte do jeho detailu, na záložku **"Security credentials"**.
   - V sekci **"Access keys"** klikněte na **"Create access key"**.
   - Jako "Use case" vyberte **"Application running on an AWS compute service"**.
   - Zkopírujte si zobrazený **Access key ID** a **Secret access key**.

### 3. Nastavení Bucket Policy a CORS
1. **Bucket Policy:**
   - Vraťte se do S3, vyberte váš bucket -> **Permissions -> Bucket policy -> Edit**.
   - Vložte následující JSON (opět nahraďte `NAZEV-VASEHO-BUCKETU` a `VASE-AWS-ACCOUNT-ID`):
     ```json
     {
         "Version": "2012-10-17",
         "Statement": [
             {
                 "Sid": "PublicReadGetObject",
                 "Effect": "Allow",
                 "Principal": "*",
                 "Action": "s3:GetObject",
                 "Resource": "arn:aws:s3:::NAZEV-VASEHO-BUCKETU/*"
             },
             {
                 "Sid": "AllowWriteForApp",
                 "Effect": "Allow",
                 "Principal": {
                     "AWS": "arn:aws:iam::VASE-AWS-ACCOUNT-ID:user/easysped-app-user"
                 },
                 "Action": [
                     "s3:PutObject",
                     "s3:PutObjectAcl",
                     "s3:DeleteObject"
                 ],
                 "Resource": "arn:aws:s3:::NAZEV-VASEHO-BUCKETU/*"
             }
         ]
     }
     ```

2. **CORS Configuration:**
   - Ve stejné sekci sjeďte níže k **"Cross-origin resource sharing (CORS)" -> Edit**.
   - Vložte následující JSON (nahraďte `https://vas-render-hostname.onrender.com` vaší skutečnou URL):
     ```json
     [
         {
             "AllowedHeaders": [
                 "*"
             ],
             "AllowedMethods": [
                 "GET",
                 "PUT",
                 "POST",
                 "DELETE"
             ],
             "AllowedOrigins": [
                 "https://vas-render-hostname.onrender.com"
             ],
             "ExposeHeaders": []
         }
     ]
     ```

### 4. Nastavení proměnných na Renderu
- V "Environment" vaší služby na Renderu přidejte/aktualizujte následující proměnné:
  - `AWS_STORAGE_BUCKET_NAME`: Název vašeho S3 bucketu.
  - `AWS_S3_REGION_NAME`: Region vašeho S3 bucketu.
  - `AWS_ACCESS_KEY_ID`: Nově vygenerovaný Access key.
  - `AWS_SECRET_ACCESS_KEY`: Nově vygenerovaný Secret key.

Po uložení proměnných se aplikace restartuje a měla by být schopna ukládat soubory na S3.

---

## Licence
Uveďte licenci dle potřeby (např. MIT) nebo ponechte interní/proprietární.

---

## Podpora
Pro problémy s nasazením si projděte logy na Renderu (Build & Runtime). Pokud chyba souvisí se šablonami nebo migracemi, zkontrolujte:
- `requirements.txt` obsahuje všechny balíčky (vč. `django-crispy-forms`, `crispy-bootstrap5`).
- Migrace proběhly: `python manage.py migrate`.
- Šablona přihlášení existuje: `logistika/templates/registration/login.html`.
