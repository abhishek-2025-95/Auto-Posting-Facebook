# RunPod setup: 24/7 or scheduled posting in the cloud

Run the Auto Posting Facebook pipeline on RunPod (e.g. RTX 2000 Ada) for 24/7 or scheduled posting without using your PC.

**Deploy link (RTX 2000 Ada + PyTorch):**  
[https://console.runpod.io/deploy?type=GPU&gpu=RTX+2000+Ada&count=1&template=runpod-torch-v240](https://console.runpod.io/deploy?type=GPU&gpu=RTX+2000+Ada&count=1&template=runpod-torch-v240)

---

## Run everything on RunPod only (no VPS, no split)

If you want **only** the RunPod GPU to run your system — news, caption, image (Z-Image-Turbo), overlay, and Facebook post all on the same pod — use this path. No VPS, no `runpod_image_server.py`, no `RUNPOD_IMAGE_API_URL`, no tunnel.

1. **Deploy a GPU pod** (link above or Step 1 below). Add your SSH key in the pod **Connect** tab.
2. **SSH in** and run the steps below (clone project, venv, install, `.env`, then run with `RUNPOD=1`).
3. **On the pod:** create `.env` with `GEMINI_API_KEY`, `PAGE_ID`, `PAGE_ACCESS_TOKEN`, optional `NEWS_API_KEY`. Do **not** set `RUNPOD_IMAGE_API_URL`.
4. **On the pod:** always set `RUNPOD=1` when running so the app uses the GPU on the same machine (Z-Image-Turbo via diffusers).

**One-off test (one post):**
```bash
cd /workspace/auto-posting-facebook
source .venv/bin/activate
export RUNPOD=1
python run_one_cycle.py
```

**24/7 in background:**
```bash
cd /workspace/auto-posting-facebook && source .venv/bin/activate && export RUNPOD=1 && nohup python run_continuous_posts.py > runpod.log 2>&1 &
```

**Cron (e.g. every 6 hours):**
```bash
0 */6 * * * cd /workspace/auto-posting-facebook && RUNPOD=1 .venv/bin/python run_one_cycle.py >> /workspace/runpod.log 2>&1
```

Details: follow **Step 1** (Deploy), **Step 2** (Connect, clone, venv, `pip install -r requirements.txt`), **Step 3** (`.env`, no `RUNPOD_IMAGE_API_URL`), **Step 4** (run with `RUNPOD=1`).

---

## One-command setup from your PC (split: image-only on RunPod)

If you want **only the image server** on RunPod and the rest on a VPS, you can set up the pod from Windows in one go:

1. Deploy a GPU pod (Step 1 below), add your SSH public key in the pod’s **Connect** tab, and note the **SSH username** (e.g. `t4yp4bdgfbei8h-64410ea3`).
2. In your project folder, add to `.env` (or pass as argument):
   ```
   RUNPOD_SSH_USER=t4yp4bdgfbei8h-64410ea3
   ```
   Optionally set `RUNPOD_SSH_KEY=C:\Users\user\.ssh\id_ed25519` if your key is elsewhere.
3. From PowerShell (in the project folder):
   ```powershell
   python setup_runpod.py
   ```
   Or: `python setup_runpod.py t4yp4bdgfbei8h-64410ea3`

The script will SSH into the pod, create `/workspace/auto-posting-facebook`, upload `runpod_image_server.py`, create a venv, install dependencies (flask, torch, diffusers, etc.), and start the server in the background. To watch progress:  
`ssh -i C:\Users\user\.ssh\id_ed25519 <RUNPOD_SSH_USER>@ssh.runpod.io "tail -f /workspace/auto-posting-facebook/server.log"`  
When you see "Model loaded.", set `RUNPOD_IMAGE_API_URL=http://<pod-ip>:5000` on your VPS.

**Run one cycle from Windows (no Direct TCP needed):** If your PC cannot reach the pod’s public IP (connection refused), use the SSH tunnel runner so the pipeline talks to RunPod via `localhost:5000`:
```powershell
python run_one_cycle_with_runpod.py
```
Or double‑click `run_one_cycle_with_runpod.cmd`. This script (1) ensures the image server is running on the pod, (2) opens an SSH tunnel from your PC’s port 5000 to the pod’s 5000, (3) runs one post cycle using `RUNPOD_IMAGE_API_URL=http://127.0.0.1:5000`. Requires `RUNPOD_SSH_USER` (and optionally `RUNPOD_SSH_KEY`) in `.env`.

---

## Step 1: Deploy a pod on RunPod

1. Sign in at [console.runpod.io](https://console.runpod.io).
2. Use the link above or: **Deploy** → **GPU** → select **RTX 2000 Ada** (or similar, 16GB+ VRAM) → **RunPod Torch** template (or any PyTorch/CUDA template).
3. Choose **Secure Cloud** (stable) or **Community Cloud** (cheaper, spot).
4. Deploy the pod. Note the **SSH** command (e.g. `ssh root@... -p 22 -i ~/.ssh/your_key`).
5. (Optional) Attach a **Network Volume** for persistent storage (e.g. `posted_articles.json`, logs). Mount path is often `/runpod-volume`.

---

## Step 2: Connect and prepare the environment

1. **SSH into the pod** (use the command from the RunPod console):
   ```bash
   ssh root@<pod-ip> -p <port> -i ~/.ssh/your_key
   ```

2. **Install system deps** (if needed):
   ```bash
   apt-get update && apt-get install -y git python3-venv
   ```

3. **Clone the project** (or upload via SCP/SFTP):
   ```bash
   cd /workspace
   git clone https://github.com/YOUR_USERNAME/auto-posting-facebook.git
   cd auto-posting-facebook
   ```
   If you don’t use git, create the folder and upload the project files (e.g. with `scp` or RunPod’s file browser).

4. **Create a virtualenv and install dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   The RunPod Torch template usually has PyTorch/CUDA; if not, install:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
   ```

---

## Step 3: Configure secrets

1. **Create `.env`** in the project root (same as local):
   ```bash
   cp .env.example .env
   nano .env
   ```

2. **Fill in** (required for posting):
   - `GEMINI_API_KEY` – [Google AI Studio](https://aistudio.google.com/apikey) (or use Ollama only, see below)
   - `PAGE_ID` – Facebook Page ID  
   - `PAGE_ACCESS_TOKEN` – Facebook Page access token  
   - `NEWS_API_KEY` – (optional) [newsdata.io](https://newsdata.io/) for more news sources  

3. **Enable RunPod image path** (use built-in Z-Image-Turbo via diffusers, no extra repo):
   ```bash
   export RUNPOD=1
   ```
   Add this to your run script or shell profile so it’s set when you run the app.

---

## Step 4: Run the pipeline

**One-off test (one post):**
```bash
cd /workspace/auto-posting-facebook
source .venv/bin/activate
export RUNPOD=1
python run_continuous_posts.py
```
(The script posts once, then continues with cooldown. Stop with Ctrl+C after one cycle if you only want a test.)

**24/7 in the background (with nohup):**
```bash
cd /workspace/auto-posting-facebook
source .venv/bin/activate
export RUNPOD=1
nohup python run_continuous_posts.py > runpod.log 2>&1 &
tail -f runpod.log
```

**Scheduled (cron, one post per run):** Use `run_one_cycle.py` so each cron run does one cycle and exits:
```bash
crontab -e
```
Add (example: every 6 hours; set `RUNPOD=1` in the script or in crontab):
```
0 */6 * * * cd /workspace/auto-posting-facebook && RUNPOD=1 .venv/bin/python run_one_cycle.py >> /workspace/runpod.log 2>&1
```
Adjust the schedule as needed (e.g. `0 */4 * * *` for every 4 hours).

---

## Step 5: Optional – Ollama for caption/prompt (open source)

To use **Ollama** instead of Gemini for caption and image prompt:

1. **Install Ollama** on the pod:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama serve &
   ollama pull llama3.2
   ```

2. **In `.env`** set:
   ```
   USE_OLLAMA=true
   ```

3. Run the pipeline as above; caption and prompt will use Ollama, image still uses Z-Image-Turbo (RunPod diffusers path).

---

## Alternative: Split setup (image-only on RunPod, rest on VPS)

Run **only** the GPU image step on RunPod; run news, caption, overlay, and Facebook posting on a **VPS** (no GPU needed there). This keeps GPU cost on RunPod minimal and uses a cheap VPS for the rest.

### On RunPod (GPU pod)

1. Deploy a pod as in Step 1–2 (clone/venv/install).
2. Install Flask and image-gen deps (no full app deps needed):
   ```bash
   pip install flask torch diffusers transformers accelerate safetensors
   ```
3. Run **only** the image server (no `.env` needed on RunPod for Gemini/Facebook):
   ```bash
   python runpod_image_server.py
   ```
   The server listens on `0.0.0.0:5000` (or `PORT`). Note the **pod’s public IP** and port (e.g. `http://1.2.3.4:5000`).

### On VPS

1. Clone the full project and set up `.env` with `GEMINI_API_KEY`, `PAGE_ID`, `PAGE_ACCESS_TOKEN`, `NEWS_API_KEY` (optional).
2. Set the RunPod image API URL (use the RunPod public IP and port from above):
   ```bash
   export RUNPOD_IMAGE_API_URL=http://<RUNPOD_PUBLIC_IP>:5000
   ```
   Or add to `.env`: `RUNPOD_IMAGE_API_URL=http://<RUNPOD_PUBLIC_IP>:5000`
3. Run the pipeline **without** `RUNPOD=1` (no GPU on VPS):
   ```bash
   python run_continuous_posts.py
   ```
   or `python run_one_cycle.py` for cron. Image generation will be sent to the RunPod server; news, caption, overlay, and posting run on the VPS.

**Note:** RunPod’s pod must be reachable from the VPS (same provider/region or use RunPod’s public IP; firewall/security group must allow the chosen port).

---

## Summary

| Step | Action |
|------|--------|
| 1 | Deploy RunPod pod (RTX 2000 Ada + PyTorch template). |
| 2 | SSH in, clone/upload project, `python3 -m venv .venv`, `pip install -r requirements.txt`. |
| 3 | Copy `.env.example` to `.env`, add `GEMINI_API_KEY`, `PAGE_ID`, `PAGE_ACCESS_TOKEN`; set `RUNPOD=1` when running. |
| 4 | Run `python run_continuous_posts.py` (foreground or with `nohup` / cron). |
| 5 | (Optional) Install Ollama and set `USE_OLLAMA=true` for fully open-source caption/prompt. |
| *Split* | RunPod: only `runpod_image_server.py`. VPS: full app with `RUNPOD_IMAGE_API_URL=http://<pod-ip>:5000`. |

**Cost:** Billed by the second (e.g. ~$0.24/hr for RTX 2000 Ada). Stop the pod when not posting to save money.

**Support:** Open source and commercial models both work; the pod is a standard Linux + GPU environment.

---

## True SSH (optional)

By default, RunPod provides terminal access via a **proxy** (`USER@ssh.runpod.io`). You may see *"Your SSH client doesn't support PTY"* — that’s from the proxy; our scripts hide it and commands still run.

If you want a **real SSH daemon** in the pod (e.g. for SCP, SFTP, or IDE remote SSH), use RunPod’s guide: [How to Achieve True SSH in Runpod](https://www.runpod.io/blog/how-to-achieve-true-ssh-in-runpod). In short:

- Use **Secure Cloud** (TCP enabled by default) or **Expose TCP port 22** in your template.
- In **Edit Template** → **Container Start Command**, add the script that installs/configures OpenSSH and adds your **public key**.
- Connect via the **Direct TCP** command (e.g. `ssh root@<pod-ip> -p <port> -i ~/.ssh/id_ed25519`) from the Connect tab.

RunPod’s PyTorch / “Runpod stack” templates may already set this up. For our one-command scripts (`setup_runpod.py`, `setup_runpod_full.py`), the proxy SSH is enough; use true SSH if you need SCP or direct `root@ip` access.
