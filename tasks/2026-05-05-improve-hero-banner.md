# Task: Improve Hero Banner Homepage Satu Data Banten

| Field        | Isi |
|--------------|-----|
| **Title**    | Improve Hero Banner Homepage Satu Data Banten |
| **Start Date** | 2026-05-05 |
| **End Date**   | 2026-05-05 |
| **Status**     | Done (deployed ke produksi) |
| **Modul**      | `ckanext-banten-theme` (homepage hero) |
| **Lingkungan** | Local (`http://localhost:5001/`) → Production (`https://satudata.bantendev.id/`) |

## Description

Mengganti background hero section homepage Satu Data Provinsi Banten dari gradient navy polos menjadi banner foto resmi (Gubernur, Wakil Gubernur, dan landmark Menara Banten) sesuai referensi desain yang diminta. Sebelumnya overlay biru terlalu dominan sehingga gambar tidak terlihat; setelah penyesuaian, gambar tampil jelas dengan teks heading tetap terbaca.

### Perubahan teknis
- Tambah asset baru: `src/ckanext-banten-theme/ckanext/banten_theme/public/banten/images/banner-home.png`.
- `templates/home/index.html`: pasang `--hero-bg-image` via `h.url_for_static(...)` agar URL benar di lingkungan CKAN apa pun.
- `assets/css/banten.css`:
  - hilangkan overlay biru full-screen di `.banten-hero`,
  - background pakai image (`background-size: cover`, `background-position: center center`),
  - tinggalkan vignette radial halus di belakang heading + `text-shadow` agar teks tetap kontras,
  - ubah `.banten-hero h1 .accent` (kata "Provinsi Banten") jadi putih solid agar konsisten dengan "Satu Data".

### Deployment
- rsync 3 file (CSS, template, image) ke `vm-banten:/home/statistik/satudata/...`.
- `DOCKER_BUILDKIT=0 docker compose -f docker-compose.prod.yml build ckan` → `satudata-ckan:latest` ter-rebuild.
- `docker compose -f docker-compose.prod.yml up -d --no-deps ckan datapusher` → container CKAN sehat.
- Smoke test:
  - `GET /api/action/status_show` → `success: true`.
  - `GET /banten/images/banner-home.png` → `200 OK`, 1,413,937 bytes (sama dengan sumber).
  - `GET https://satudata.bantendev.id/` via Nginx (openresty) → `200 OK`.

## Acceptance Criteria
- Homepage menampilkan banner foto Gubernur & Wagub + landmark sebagai background hero.
- Heading "Satu Data Provinsi Banten" tetap terbaca jelas (kontras cukup).
- Tidak ada perubahan data (DB, Solr, file storage tidak disentuh).
- Public URL `https://satudata.bantendev.id/` mengembalikan HTTP 200.
