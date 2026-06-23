# Lingkungan Deploy — Satu Data Banten

| Lingkungan | SSH alias | IP | User | Domain publik | `.env` di server |
|------------|-----------|-----|------|---------------|------------------|
| **Development** | `ssh-banten-dev` atau `vm-banten` | `10.255.100.246` | `statistik` | https://satudata.bantendev.id | `CKAN_SITE_URL` → dev |
| **Production** | `ssh-banten-prod` | `10.249.100.25` | `statistik` | https://data.bantenprov.go.id | `CKAN_SITE_URL` → prod |

Repo path di kedua VM (default): `~/satudata`

---

## SSH (Mac / laptop developer)

Tambahkan ke `~/.ssh/config` (lihat juga `deploy/ssh-config.snippet`):

```sshconfig
Host vm-banten ssh-banten-dev
    HostName 10.255.100.246
    User statistik
    IdentityFile ~/.ssh/vm_access
    IdentitiesOnly yes
    ServerAliveInterval 30

Host ssh-banten-prod
    HostName 10.249.100.25
    User statistik
    IdentityFile ~/.ssh/vm_access
    IdentitiesOnly yes
    ServerAliveInterval 30
```

**Login:**

```bash
ssh ssh-banten-dev    # development
ssh ssh-banten-prod   # production
```

**Autentikasi:** gunakan SSH key (`~/.ssh/vm_access`). Jika server baru masih password-only, login sekali dengan password lalu pasang key:

```bash
ssh-copy-id -i ~/.ssh/vm_access.pub ssh-banten-prod
```

> Jangan simpan password di git. Kredensial hanya di password manager / vault tim.

---

## Deploy cepat dari laptop

```bash
# Sync source ke development
./deploy/sync.sh dev

# Sync source ke production
./deploy/sync.sh prod

# Setelah sync, di VM:
ssh ssh-banten-prod 'cd ~/satudata && bash deploy/update.sh'
```

---

## Perbedaan konfigurasi penting

| Item | Development | Production |
|------|-------------|------------|
| `CKAN_SITE_URL` | `https://satudata.bantendev.id` | `https://data.bantenprov.go.id` |
| Data persisten | `/var/lib/satudata-data/` (VM dev) | `/var/lib/satudata-data/` (VM prod) |
| API publik konsumen | (sesuai kebijakan) | `api.bantenprov.go.id` → upstream prod |

Setiap VM punya file **`.env` sendiri** — jangan copy `.env` dev ke prod tanpa menyesuaikan URL, secret, dan SMTP.

---

## Metrix (Metabase signed embed)

- CKAN route `/metrix` membangun JWT di server (`metabase_embed.py`).
- iframe memakai path same-origin: `/metrix-dashboard/embed/dashboard/{token}`.
- Env di `.env` VM: `METABASE_EMBED_SECRET`, `METABASE_DASHBOARD_ID`, `METABASE_EMBED_SITE_URL`.
- Nginx VM: gunakan `deploy/nginx-ckan-vm.conf` (`Host $host`, bukan IP Metabase).

## Verifikasi setelah deploy

```bash
# Development
curl -fsS https://satudata.bantendev.id/api/3/action/status_show

# Production
curl -fsS https://data.bantenprov.go.id/api/3/action/status_show
```
