# Running Receipt Digitizer on your own machine

A step-by-step guide from a blank machine to a working app in your browser — no prior Docker/Git experience assumed. Every command below is typed into a terminal (on Windows, that's **Git Bash**, installed alongside Git in step 1).

## 1. Install the prerequisites

You need three things: **Git**, **Docker Desktop**, and (Windows only) **WSL2**.

### Windows
1. Install **Git for Windows**: https://git-scm.com/download/win — this also gives you "Git Bash", the terminal you'll use for every command below.
2. Install **WSL2**: open PowerShell **as Administrator** and run:
   ```powershell
   wsl --install
   ```
   Restart your computer when it asks.
3. Install **Docker Desktop**: https://www.docker.com/products/docker-desktop/ — during/after install, open Docker Desktop → **Settings → Resources → WSL Integration** and make sure it's turned on. Restart Docker Desktop.

### macOS
1. Install **Git**: open Terminal and run `git --version` — if it's not installed, macOS will prompt you to install the Xcode Command Line Tools, which include Git.
2. Install **Docker Desktop for Mac**: https://www.docker.com/products/docker-desktop/

### Linux
1. Install Git via your package manager, e.g. `sudo apt install git`.
2. Install Docker Engine + Compose following your distro's official Docker docs.

**Verify everything's installed** (same command on every OS, in your terminal):
```bash
git --version
docker --version
docker compose version
```
All three should print a version number. If `docker --version` fails on Windows, double-check the WSL Integration toggle from step 3 and restart your terminal.

## 2. Set up SSH access to GitHub

This lets your machine clone/push to GitHub without typing a password every time. You only do this once per machine.

**Check if you already have a key:**
```bash
ls ~/.ssh/id_ed25519.pub
```
If that prints a file path, skip to step 2.3. If it says "No such file or directory", continue to step 2.1.

### 2.1 Generate a new SSH key
```bash
ssh-keygen -t ed25519 -C "your-github-email@example.com"
```
- Press **Enter** to accept the default file location.
- You can press **Enter** twice more to skip setting a passphrase, or set one if you want extra security.

### 2.2 Start the SSH agent and add your key
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### 2.3 Copy your public key
```bash
cat ~/.ssh/id_ed25519.pub
```
Select and copy the entire output (starts with `ssh-ed25519` and ends with your email).

### 2.4 Add it to your GitHub account
1. Go to https://github.com/settings/keys
2. Click **New SSH key**
3. Give it any title (e.g. "My Laptop")
4. Paste the key you copied, click **Add SSH key**

### 2.5 Test the connection
```bash
ssh -T git@github.com
```
Type `yes` if asked to confirm the host. You should see:
```
Hi <your-github-username>! You've successfully authenticated, but GitHub does not provide shell access.
```
That message (even though it sounds like an error) means it worked.

## 3. Clone the repository

```bash
git clone git@github.com:daffa-pradana/receipt_digitizer.git
cd receipt_digitizer
```

## 4. Set your git identity (for this repo only)

So any commits you make here use your own name/email, separate from any other identity on your machine:
```bash
git config user.name "Your Name"
git config user.email "your-personal@email.com"
```

## 5. Configure the environment file

```bash
cp .env.example .env
```
The defaults inside are fine to run locally — no editing needed.

## 6. Build and start the app

```bash
make up
```
No `make` available (e.g. plain Windows without Git Bash's extras)? Use the equivalent raw command instead:
```bash
docker compose up --build -d
```

**Heads up: the first build is large and slow** — it downloads PyTorch and bakes in the EasyOCR deep-learning models, which can take a long time depending on your internet connection (expect several minutes, possibly more). This only happens once; every run after this is fast. Good idea to start this and go make a coffee.

## 7. Open the app

Once the build finishes, open your browser to:
```
http://localhost:8501
```
You should see the "Receipt Digitizer" title, an intro paragraph, and a file upload box.

## 8. Test it

1. **Upload 1–5 receipt photos** (jpg/jpeg/png) using the upload box. There are sample receipts in `tests/sample_receipts/` in this repo if you don't have your own handy.
2. Wait for "Reading receipts..." to finish — this runs OCR on each photo.
3. An **editable table** appears below with merchant, category, amount, and OCR confidence per receipt. Check the results:
   - If a row has a `⚠️` next to it, that means the amount is missing or OCR confidence was low — double check it against the photo (there's an expander above the table to view the uploaded photos).
   - You can correct any cell directly by clicking into it. Category is a dropdown.
4. Click **Save**. You should see a "Saved N transaction(s)" success message.
5. Scroll down — the **pie chart** under "Spending by category" should now reflect what you saved.
6. Reload the page — the pie chart data should still be there (it's saved in the database, not just in your browser).

If all of that worked, the app is running correctly on your machine.

## 9. Useful commands afterward

```bash
make down       # stop the app (your saved data is kept)
make logs       # watch the app's logs live
make reset-db   # wipe saved test transactions, keep everything else
make nuke       # stop everything AND delete all saved data (fresh start)
make test       # run the automated tests (needs Python, not Docker)
make help       # list all available commands
```

## Troubleshooting

- **`docker: command not found`** — Docker Desktop isn't running, or (Windows) WSL Integration isn't enabled. Open Docker Desktop, check Settings → Resources → WSL Integration, restart your terminal.
- **Port 8501 already in use** — something else on your machine is using that port. Stop it, or ask in the group chat and we'll figure out a different port.
- **Blank page in the browser with just a "Deploy" button, nothing else** — this happened to us once during development; it meant the container was serving old code. Try `make down` then `make up` again (forces a rebuild).
- **Permission errors deleting files under `app/` or `tests/` afterward** — Docker sometimes leaves behind files owned by `root`. Ask Daffa; there's a one-line fix using Docker itself to clean them up.
- **Anything else** — post the exact error message in the group chat; don't guess/retry blindly, the actual error text is what makes it fixable fast.
