# Deploying to Railway

Step-by-step guide to move this Flask app from PythonAnywhere to Railway with a persistent volume for `users.db` and uploaded files.

---

## Before you start

You need:
- A GitHub account
- A Railway account (sign up at railway.com)
- Git installed on your Mac
- (Optional) Railway CLI: `brew install railway` — needed to upload `users.db` and existing uploads into the volume.

---

## 1. Generate a Gmail App Password

Your code uses Gmail SMTP. The old password (`ybgj pskk tjrv uxwi`) was hardcoded — we removed it. Generate a fresh one:

1. Go to https://myaccount.google.com/apppasswords
2. Sign in as `3omarislam911@gmail.com`
3. Create a new app password (label it "Railway Meerim")
4. Copy the 16-character password. You'll paste it into Railway in step 5.

---

## 2. Test locally (optional but recommended)

```bash
cd "/Users/ibrahim/Desktop/my projects/meeriem"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and fill in MAIL_PASSWORD, ADMIN_PASSWORD, SECRET_KEY
python flask_app.py
```

Open http://localhost:5000 — confirm login, admin dashboard, file upload all still work.

---

## 3. Push to GitHub

```bash
cd "/Users/ibrahim/Desktop/my projects/meeriem"
git init
git add .
git status     # ← double-check .env and instance/users.db are NOT listed
git commit -m "Initial commit for Railway deployment"
```

Then create a **private** GitHub repo (don't make it public — the code references your Gmail account and admin username) at https://github.com/new, then:

```bash
git branch -M main
git remote add origin https://github.com/<your-username>/meeriem.git
git push -u origin main
```

---

## 4. Create the Railway project

1. Go to https://railway.com/new
2. Choose **Deploy from GitHub repo** → select the repo you just pushed
3. Railway will detect Python and start building. **Let the first build fail or run** — we'll configure it next before it actually serves traffic.

---

## 5. Set environment variables

In your Railway project → service → **Variables** tab, add:

| Variable | Value |
|---|---|
| `SECRET_KEY` | A long random string. Generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `MAIL_PASSWORD` | The Gmail App Password from step 1 |
| `MAIL_USERNAME` | `3omarislam911@gmail.com` |
| `ADMIN_USERNAME` | `Meerim` |
| `ADMIN_PASSWORD` | A new strong password (the old one was visible in code) |
| `DATABASE_URL` | `sqlite:////data/users.db` (note: **four** slashes) |
| `UPLOAD_FOLDER` | `/data/uploads` |
| `FLASK_DEBUG` | `0` |

Click **Deploy** after saving.

---

## 6. Create the persistent volume

1. In your Railway service → **Settings** → **Volumes**
2. Click **+ New Volume**
3. **Mount path**: `/data`
4. Choose a size — **1 GB is plenty** to start (your DB is 454 KB and uploads are small). You can grow it later.
5. Save. Railway will restart the service with the volume mounted.

---

## 7. Seed the volume with your existing data

Your `users.db` and existing uploaded files need to get into `/data` on the Railway volume. Use the Railway CLI:

```bash
# Log in
railway login

# Link to your project (run from the project folder)
cd "/Users/ibrahim/Desktop/my projects/meeriem"
railway link

# Open a shell on the running service
railway shell
```

Inside the Railway shell:
```bash
ls /data         # should be empty at first
mkdir -p /data/uploads
exit
```

Now from your local machine, upload the files. The easiest way is `railway run` to copy via standard tools, **but Railway doesn't have a direct file-copy command**. Two options:

### Option A — One-time seed via a temporary upload endpoint
Easiest: temporarily add a small admin-only route in `flask_app.py` that accepts file uploads to `/data`, deploy, push your files via curl, then remove the route. Tell me if you want this and I'll write it.

### Option B — Use `railway run` with rsync over the service
Railway doesn't expose SSH on Hobby plans. The practical path is Option A or using a Railway "one-off" deployment with a startup script that pulls files from a public URL (e.g., a Google Drive link you delete afterward).

### Option C — Commit the data to a private "seed" branch (simplest for small files)
Since the DB is only 454 KB and your uploads are small:

1. Make a one-time branch `seed-data` that includes `instance/users.db` and `static/uploads/*`
2. Add a startup script (`seed.py`) that runs on first boot: copies them to `/data` if `/data/users.db` doesn't exist yet
3. After the first deploy seeds the volume, remove the data from git

If you want me to set this up, say so — it's about 20 lines of code.

---

## 8. Verify

Visit your Railway app URL (shown in the service dashboard, something like `meeriem-production.up.railway.app`):

- [ ] Homepage loads
- [ ] Existing users can log in (passwords still work — hashes copied with the DB)
- [ ] Admin dashboard works
- [ ] Uploading a new file works AND the file survives a redeploy
- [ ] Email sending works (try the apply form)

---

## 9. Custom domain (optional)

In Railway → Settings → Domains → add your domain. Railway gives you a CNAME to point at.

---

## Troubleshooting

- **App crashes on start**: Check the Deploy Logs tab. Most common cause: missing env var or a Python package missing from `requirements.txt`.
- **"Database is locked" errors**: SQLite under high load. Move to Postgres (Railway → Add Service → Postgres, then change `DATABASE_URL` to the one Railway provides).
- **Uploads disappear after redeploy**: The volume isn't mounted, or `UPLOAD_FOLDER` env var isn't pointing at `/data/uploads`.
- **Login broken**: Make sure the volume contains `users.db` — without it, the app creates an empty new DB.

---

## Files added for Railway

- `Procfile` — tells Railway to run `gunicorn flask_app:app`
- `requirements.txt` — Python dependencies
- `runtime.txt` — pins Python 3.12.7
- `.gitignore` — keeps secrets and the local DB out of git
- `.env.example` — template for local `.env`
- `DEPLOY_RAILWAY.md` — this file
