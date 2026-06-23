# Satudata Deployment Guide

Panduan deploy portal Satu Data Banten (CKAN 2.11 + Docker).

## Lingkungan (Development vs Production)

| | Development | Production |
|---|-------------|------------|
| **SSH** | `ssh ssh-banten-dev` (alias `vm-banten`) | `ssh ssh-banten-prod` |
| **IP** | `10.255.100.246` | `10.249.100.25` |
| **Domain** | https://satudata.bantendev.id | https://data.bantenprov.go.id |

Detail SSH, rsync, dan perbedaan `.env`: **[deploy/environments.md](environments.md)**  
Snippet `~/.ssh/config`: **[deploy/ssh-config.snippet](ssh-config.snippet)**  
Sync dari laptop: `./deploy/sync.sh dev` atau `./deploy/sync.sh prod`

---

## Arsitektur

```
Internet
   │
   ▼
┌──────────────────────────────────────────┐
│ VM (host)                                │
│                                          │
│ nginx:443 (host) ──► 127.0.0.1:8080      │
│   (SSL + reverse proxy)         │        │
│                                 ▼        │
│             ┌─────────────────────────┐  │
│             │ Docker network          │  │
│             │  ckan ─┬─ db (postgres) │  │
│             │        ├─ solr          │  │
│             │        ├─ redis         │  │
│             │        └─ datapusher    │  │
│             └─────────────────────────┘  │
│                                          │
│ /var/lib/satudata-data/  (persistent)    │
│   ├── postgres/                          │
│   ├── solr/                              │
│   ├── ckan_storage/                      │
│   └── redis/                             │
│                                          │
│ /home/$USER/satudata/  (git clone)       │
│   ├── docker-compose.prod.yml            │
│   ├── .env  (gitignored)                 │
│   └── ...                                │
└──────────────────────────────────────────┘
```

**Key principle:** Source code (di repo) terpisah total dari data (di `/var/lib/satudata-data/`). 
Update source code = `git pull` + rebuild, **data tidak terganggu**.

---

## Initial Deploy (sekali saja, di VM)

### Prerequisites di VM

```bash
# Install Docker (kalau belum)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

### Step 1 — Stop service lama (CKAN native)

```bash
# Stop CKAN uwsgi & datapusher native (ada di VM lama)
sudo systemctl stop ckan datapusher 2>/dev/null || true
sudo systemctl stop apache2 2>/dev/null || true   # kalau pakai Apache

# Stop docker container lama
docker stop sdi-banten ckan-solr 2>/dev/null || true

# Verify port 8080 bebas
sudo ss -tlnp | grep ':8080 '
```

### Step 2 — Clone repo

```bash
cd ~
git clone https://github.com/herihandoko/satudata.git
cd satudata
```

### Step 3 — Setup `.env`

```bash
cp .env.production.example .env
# Edit dan ganti SEMUA placeholder CHANGE_ME
nano .env

# Generate secrets dengan:
openssl rand -base64 48   # untuk BEAKER_SESSION_SECRET
openssl rand -base64 48   # untuk JWT_ENCODE_SECRET (sama untuk DECODE)
openssl rand -base64 24   # untuk passwords
```

### Step 4 — Run initial setup

```bash
bash deploy/initial-setup.sh
```

Script akan:
1. Cek prerequisite
2. Buat data directories di `/var/lib/satudata-data/`
3. Build Docker images
4. Start semua container
5. Tunggu services healthy

### Step 5 — Restore data dari VM lama

```bash
# Asumsi backup sudah ada di /home/statistik/vm-backups/<timestamp>/
BACKUP=/home/statistik/vm-backups/20260426_145727

# Stop CKAN dulu (biar tidak ada query yang masuk saat restore)
docker compose -f docker-compose.prod.yml stop ckan datapusher

# Restore database
bash deploy/restore-data.sh $BACKUP/ckan_default.dump

# Restore file storage
bash deploy/restore-storage.sh $BACKUP/var-lib-ckan.tar.gz

# Start CKAN lagi
docker compose -f docker-compose.prod.yml up -d

# Rebuild Solr index (sesuai data baru)
docker compose -f docker-compose.prod.yml exec ckan ckan search-index rebuild
```

### Step 6 — Configure host nginx

```bash
sudo cp deploy/nginx-satudata.conf.example /etc/nginx/sites-available/satudata
sudo nano /etc/nginx/sites-available/satudata   # update SSL paths

sudo ln -sf /etc/nginx/sites-available/satudata /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default      # kalau perlu

sudo nginx -t
sudo systemctl reload nginx
```

### Step 7 — Verify

```bash
# Lokal di VM
curl -I http://127.0.0.1:8080
curl http://127.0.0.1:8080/api/action/status_show

# Eksternal
curl -I https://satudata.bantendev.id
```

---

## Update Workflow (setiap kali ada update)

### Dari local Mac (push)

```bash
cd /Users/herihandoko/Sites/satudata
# edit kode, theme, dll
git add .
git commit -m "Update: ..."
git push
```

### Di VM (pull & deploy)

```bash
cd ~/satudata
bash deploy/update.sh
```

Script update akan:
1. Backup database (safety net, retention 10 backup terakhir)
2. `git pull --ff-only`
3. Rebuild image CKAN
4. Recreate container CKAN & datapusher (db/solr/redis tidak disentuh)
5. Health check

**Data persist** di `/var/lib/satudata-data/` selama proses update.

---

## Daily Backup (rekomendasi)

```bash
# Setup cron untuk daily backup jam 2 pagi
crontab -e
```

Tambahkan baris:
```
0 2 * * * /home/$USER/satudata/deploy/backup.sh >> /var/log/satudata-backup.log 2>&1
```

Backup tersimpan di `/var/lib/satudata-backups/<timestamp>/` dengan retention 14 hari.

---

## Common Operations

### Lihat logs

```bash
docker compose -f docker-compose.prod.yml logs -f ckan
docker compose -f docker-compose.prod.yml logs --tail=100 db
```

### Restart specific service

```bash
docker compose -f docker-compose.prod.yml restart ckan
```

### Stop everything

```bash
docker compose -f docker-compose.prod.yml down       # stop & remove containers (data SAFE)
docker compose -f docker-compose.prod.yml down -v    # ⚠️ TIDAK terjadi karena pakai bind mount
```

### Manual backup ad-hoc

```bash
bash deploy/backup.sh
```

### Manual DB restore

```bash
bash deploy/restore-data.sh /path/to/backup.dump
```

### Akses CKAN CLI

```bash
docker compose -f docker-compose.prod.yml exec ckan bash
# di dalam container:
ckan user list
ckan sysadmin add admin
ckan search-index rebuild
ckan db upgrade
```

### Reset Solr index

```bash
docker compose -f docker-compose.prod.yml exec ckan ckan search-index rebuild
```

---

## Rollback (kalau update bermasalah)

```bash
cd ~/satudata

# 1. Rollback source code
git log --oneline -10
git reset --hard <commit-hash-yang-bagus>

# 2. Rebuild
docker compose -f docker-compose.prod.yml build ckan
docker compose -f docker-compose.prod.yml up -d

# 3. Kalau perlu, restore DB dari pre-update backup
ls -lh ~/satudata-update-backups/
bash deploy/restore-data.sh ~/satudata-update-backups/pre-update-XXXXX.dump
```

---

## Troubleshooting

### CKAN container restart loop

```bash
docker compose -f docker-compose.prod.yml logs ckan --tail=200
```

Common: extension error, env var salah, atau db belum migrated.

### "Site URL doesn't match"

Edit `.env` → `CKAN_SITE_URL=https://satudata.bantendev.id` → restart ckan.

### Reset admin password

```bash
docker compose -f docker-compose.prod.yml exec ckan \
    ckan user setpass admin
# (ikuti prompt)
```

### Disk full

```bash
docker system prune -a   # cleanup unused images
du -sh /var/lib/satudata-data/*
du -sh /var/lib/satudata-backups/*
```
