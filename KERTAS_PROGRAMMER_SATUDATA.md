# Kertas Kerja Tenaga Ahli Programmer

**Project:** Portal Satu Data Provinsi Banten (CKAN 2.11 + tema kustom + Docker)

*Dokumen ini mengisi template Kertas Programmer agar sesuai implementasi repositori `satudata`. Sesuaikan field bertanda [ISI] dengan data administrasi Anda.*

---

## Profile Pekerjaan

| Field | Isi |
|--------|-----|
| **Nama Pekerjaan** | Pengembangan dan pemeliharaan portal data terbuka Satu Data Provinsi Banten berbasis CKAN |
| **OPD** | [ISI: mis. Diskominfo Provinsi Banten] |
| **Kategori** | Pengembangan & pembangunan (custom theme, integrasi, deployment) |
| **Goals** | Portal data terbuka yang stabil, cepat diakses, tampilan sesuai identitas pemerintah daerah, siap operasional di lingkungan produksi (VM + Docker) |
| **Klasifikasi** | Internal (infrastruktur pemerintah) / eksternal (akses publik read-only ke dataset & API) |
| **Dasar surat** | [ISI: nomor & tanggal surat perintah / SK / lampiran kerja] |

---

## 1. Bahasa Pemrograman yang Digunakan

- **Python** — inti CKAN 2.11, plugin `ckanext-banten-theme`, helper, blueprint (Metrik, Dokumentasi).
- **HTML / Jinja2** — override template (`header`, `footer`, `home`, `about`, `user`, `organization`, `group`, `package`, `metrix`, snippet helper).
- **CSS** — tema `banten.css`, webassets untuk cache-busting.
- **Shell** — skrip deploy/backup/update (`deploy/update.sh`, rsync, docker compose).

**Standar coding**

- PEP 8 untuk kode Python pada extension.
- Struktur CKAN: plugin `IBlueprint`, `ITemplateHelpers`, entry point `ckan.plugins`.
- Penamaan mengikuti konvensi CKAN/extension yang ada.

---

## 2. Basis Data

- **Engine:** PostgreSQL (database CKAN + Datastore).
- **Pencarian:** Apache Solr (indeks dataset/resource).
- **Cache / antrian:** Redis (stack CKAN Docker).
- **Desain:** Skema mengikuti CKAN core; migrasi dari instance CKAN lama ke instance baru (dump/restore).

**Entitas utama (konsep CKAN)**

| No | Entitas | Peran |
|----|---------|--------|
| 1 | `package` (dataset) | Dataset milik organisasi, berisi resource & metadata |
| 2 | `organization` | OPD / produsen data |
| 3 | `group` | Topik / klasifikasi tematik |
| 4 | `user` | Autentikasi, peran, sysadmin |
| 5 | `resource` | File/format unduhan terikat dataset |

**Operasional:** backup dump sebelum update; volume/bind mount agar data persisten saat rebuild image.

---

## 3. Layer Teknologi

| Layer | Teknologi | Alasan |
|--------|------------|--------|
| Aplikasi | CKAN 2.11 (Flask, Jinja2, uWSGI) | Standar portal open data |
| Kontainer | Docker & Docker Compose | Reproduksi dev/prod, isolasi dependensi |
| Reverse proxy | Nginx (host VM) | SSL, proxy ke CKAN & embed Metabase |
| Penyimpanan file | Volume `ckan_storage` | Resource & upload persisten |

---

## 4. Proses Pengembangan / Pembangunan Aplikasi

**Metodologi:** iteratif (penyesuaian bertahap berdasarkan UAT/feedback), deployment bertahap dev → prod.

**Tools**

- Lokal: `docker-compose.dev.yml`, port mapping (mis. 5001).
- Produksi: `docker-compose.prod.yml`, VM Ubuntu, SSH, `deploy/update.sh`.
- Version control: Git + GitHub (private); alternatif rsync bila kredensial Git di VM belum tersedia.

**Tahapan (isi durasi riil di kolom Waktu)**

| No | Tahapan | Waktu | Aktivitas |
|----|---------|--------|-----------|
| 1 | Setup CKAN (Docker) | [ISI] | Compose, PostgreSQL, Solr, Redis, path extension |
| 2 | Theme & branding | [ISI] | Logo, warna, header/footer, favicon, homepage |
| 3 | Fitur kustom | [ISI] | Metrik (embed Metabase), Dokumentasi, About |
| 4 | Migrasi data | [ISI] | Dump/restore PostgreSQL, verifikasi login & indeks |
| 5 | Deploy produksi | [ISI] | Backup VM, build image, cutover, Nginx, SMTP |
| 6 | Lokal bahasa / UI | [ISI] | Bahasa Indonesia, form pencarian, login/reset, label menu |

---

## 5. Versioning

- **Version control:** Git (GitHub).
- **Branching (contoh):** branch utama produksi; branch fitur untuk pengembangan tema & template.
- **Versi aplikasi:** CKAN 2.11; extension `ckanext-banten-theme` sesuai versi paket di `pyproject.toml`.

---

## 6. Integrasi

**Internal**

- CKAN ↔ PostgreSQL, Solr, Redis, DataPusher (sesuai konfigurasi aktif).
- Tema ↔ aset statis (`public/banten/…`), webassets.

**Eksternal**

- **SMTP** — pengiriman email (relay internal; penyesuaian sertifikat CA jika diperlukan di VM).
- **Metabase** — dashboard di menu Metrik via iframe + reverse proxy Nginx.
- **Action API CKAN** — konsumsi publik; halaman Dokumentasi berisi contoh `curl`.

---

## 7. Modul-Modul

| No | Modul | Deskripsi | Teknologi | Prioritas |
|----|--------|-----------|-----------|-----------|
| 1 | `ckanext-banten-theme` | Tampilan portal, override template, CSS, favicon | Python, Jinja2, CSS | Tinggi |
| 2 | Homepage | Hero, statistik, dataset terbaru, pratinjau Metrik, CTA | Jinja2, helper | Tinggi |
| 3 | About | Profil portal, prinsip data, kontak, CTA | Jinja2 | Sedang |
| 4 | Metrik | Route blueprint + iframe Metabase | Flask blueprint, HTML | Sedang |
| 5 | Dokumentasi | Halaman statis API & panduan | Jinja2 | Sedang |
| 6 | Deploy & operasi | `update.sh`, backup DB, rebuild image | Bash, Docker | Tinggi |
| 7 | Lokal bahasa / UI | Form pencarian, helper org/group, login/reset | Jinja2 | Sedang |

**Entrypoint Docker (contoh):** `ckan/docker-entrypoint.d/01_setup_datapusher.sh`, `02_set_locale.sh` (locale default Indonesia, penyesuaian startup).

---

## 8. Dokumentasi Source Code dan API

- **Source:** `README.md` repositori, struktur `src/ckanext-banten-theme`, `plugin.py`, blueprint.
- **API:** CKAN Action API v3; halaman `/dokumentasi` dengan contoh permintaan; tautan ke dokumentasi resmi CKAN bila perlu.
- **Lokasi:** `README.md`, halaman Dokumentasi di portal, catatan di folder `deploy/`.

---

## 9. Pengujian (Testing)

- **Manual:** UAT login, pencarian dataset, organisasi/grup, About/Metrik/Dokumentasi, email reset.
- **Smoke:** `status_show` via API, health container setelah deploy.
- **Regresi visual:** header logo, responsif mobile.

*(Unit test otomatis untuk extension dapat ditambahkan sebagai peningkatan.)*

---

## Referensi path di repositori

| Area | Path |
|------|------|
| Tema | `src/ckanext-banten-theme/ckanext/banten_theme/` |
| Compose dev/prod | `docker-compose.dev.yml`, `docker-compose.prod.yml` |
| Entrypoint CKAN | `ckan/docker-entrypoint.d/` |
| Contoh environment | `.env.example`, `.env.production.example` |

---

## 10. Log Aktivitas / Pekerjaan

| No | Tanggal Mulai | Tanggal Selesai | Pekerjaan | Deskripsi singkat | Status |
|----|---------------|-----------------|-----------|-------------------|--------|
| 1 | 2026-05-05 | 2026-05-05 | Improve Hero Banner Homepage | Mengganti background hero homepage dari gradient polos menjadi banner foto resmi (Gubernur, Wagub, landmark Menara Banten). Tuning overlay & text-shadow agar gambar tampil jelas tetapi heading "Satu Data Provinsi Banten" tetap kontras. Deploy: rsync ke VM, rebuild image (`DOCKER_BUILDKIT=0`), recreate container CKAN, smoke test publik (`https://satudata.bantendev.id/`) → 200 OK. | Done |
| 2 | 2026-05-18 | 2026-05-18 | Pentest Quick-Wins (HIGH-1, MED-1, MED-2, LOW-1) | Tambah entrypoint `ckan/docker-entrypoint.d/03_security_hardening.sh` yang otomatis set `ckan.auth.public_user_details=false` & `public_activity_stream_detail=false` (HIGH-1 + MED-1), cookie session/remember `Secure+HttpOnly+SameSite=Lax` saat HTTPS (MED-2), dan default API token expiry 90 hari (LOW-1). Deploy ke VM + rebuild + recreate. Verifikasi: `user_list`/`user_show` anon → 403, cookie `Secure; HttpOnly; SameSite=Lax`, package_search & status_show tetap OK. | Done |
| 3 | 2026-05-18 | 2026-05-18 | HIGH-2 — Rate Limiting Login | Implementasi `rate_limiter.py` (Redis counter + Flask `before/after_app_request`): 5/IP/15min → 429, 10/user/jam → lockout 30 min, reset counters on success (302). Verifikasi: attempt 1–5 → 200, attempt 6+ → 429. Fail-open saat Redis down. Detail di `tasks/2026-05-18-pentest-high2-rate-limiting.md`. | Done |
| 4 | 2026-05-18 | 2026-05-18 | HIGH-3 — SSRF Validator `resource_create` | `validators.py` + IValidators + IResourceController. Scheme whitelist (http/https), reject IPv4/IPv6 private/loopback/link-local/cloud-metadata. Verifikasi: file://, 169.254.169.254, 127.0.0.1, 10/8 semua → 400 ValidationError; example.com tetap accepted. Detail di `tasks/2026-05-18-pentest-high3-ssrf-validator.md`. | Done |
| 5 | _TBD_ | _TBD_ | Hardening Nginx | HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, CSP, Permissions-Policy + HTTP→HTTPS redirect + server_tokens off. Perlu sudo VM + koordinasi tim infra upstream openresty. Detail di `tasks/2026-05-18-pentest-nginx-hardening.md`. | Open |

*(Tambahkan baris baru pada tabel di atas setiap kali ada pekerjaan/improvement berikutnya. Detail teknis per task dapat disimpan di folder `tasks/` agar tabel ini tetap ringkas.)*

---

*Tanggal dokumen: [ISI]. Penanggung jawab / nama programmer: [ISI].*
