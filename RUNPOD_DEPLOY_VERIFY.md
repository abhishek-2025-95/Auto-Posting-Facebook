# Why Redeploy Might Not Change Anything – and How to Fix It

After you run `python setup_runpod_full.py`, the pod should have the latest code. If images and behavior look the same, one of the following is usually wrong.

---

## 1. **Old process still running (most common)**

The deploy script **now stops any existing pipeline** before starting the new one. If you deployed with an older version of the script, the **previous** process (old code) kept running and the new one may have exited or never taken over.

**Fix:** Redeploy with the **current** `setup_runpod_full.py` (it runs `pkill -f start_runpod|run_continuous_posts` before starting). Then only the new code runs.

**Or manually:** SSH in and run:
```bash
pkill -f run_continuous_posts
pkill -f start_runpod
cd /workspace/auto-posting-facebook && source .venv/bin/activate && RUNPOD=1 nohup python -u start_runpod.py >> runpod.log 2>&1 &
```

---

## 2. **Deploying from the wrong folder**

The tarball is built from the folder where you run `python setup_runpod_full.py`. If that folder is **not** your "Auto Posting Facebook" project with the latest changes, the pod gets old code.

**Fix:** Always run deploy from the project root:
```powershell
cd "c:\Users\user\Documents\Auto Posting Facebook"
python setup_runpod_full.py
```
Confirm this folder has the updated files (e.g. `text_removal.py`, `content_generator.py` with `_sanitize_image_prompt_no_headline`, etc.).

---

## 3. **GIT_CLONE_URL is set**

If `.env` (or the environment) has **GIT_CLONE_URL** set, the deploy script **clones from git** instead of uploading your local tarball. The pod then runs whatever is in that repo, not your local edits.

**Fix:** If you want to deploy **local** code, **unset** or remove `GIT_CLONE_URL` from `.env` and redeploy. If you use git, push your changes and then deploy so the clone gets the latest commit.

---

## 4. **RunPod routing you to a different container**

With **ssh.runpod.io** (proxy), RunPod can route different SSH sessions to **different containers**. So you might deploy to container A but later SSH into container B, which never received the deploy.

**Fix:** Use **Direct TCP** so you always hit the same container:
- In RunPod Connect tab, note **Direct TCP** host and port.
- In `.env` set:
  - `RUNPOD_SSH_HOST=<that host>`
  - `RUNPOD_SSH_PORT=<that port>`
- Add your SSH key in RunPod **account** settings (not only pod).
- Redeploy. Deploy and SSH will both use that container.

---

## 5. **Verify the pod is running the new code**

After deploy, the pipeline prints a **build id** at startup. Check the log on the pod:

```bash
ssh ... "grep -i 'Pipeline build' /workspace/auto-posting-facebook/runpod.log"
```

You should see something like:
```
Pipeline build: no-magazine-headlines-v1
```

If you see that, the pod is running the version that includes:
- Title-word stripping and “do not use these words” in the image prompt
- Text removal (EasyOCR / OpenCV fallback / magazine-band removal)
- No-magazine-headline negative prompt

If that line is missing or the build id is different, the process that’s running is not from the latest deploy.

---

## 6. **Dependencies (opencv, easyocr) not installed on the pod**

Text removal needs **opencv** and ideally **easyocr** (or the OpenCV-only fallback runs). If the deploy failed during `pip install -r requirements.txt` (e.g. timeout or error), the venv may be missing them.

**Fix:** SSH in and run:
```bash
cd /workspace/auto-posting-facebook && source .venv/bin/activate
pip install -r requirements.txt
```
Then restart the pipeline (see step 1).

---

## Quick checklist

| Step | Action |
|------|--------|
| 1 | Run deploy from `c:\Users\user\Documents\Auto Posting Facebook` (no GIT_CLONE_URL if you want local code). |
| 2 | Use Direct TCP in .env if you had “wrong container” issues. |
| 3 | After deploy, SSH in and run: `grep "Pipeline build" /workspace/auto-posting-facebook/runpod.log` and confirm the build id. |
| 4 | If the build id is old or missing, run `pkill -f start_runpod; pkill -f run_continuous_posts` then start again with `RUNPOD=1 python -u start_runpod.py`. |
| 5 | Ensure `pip install -r requirements.txt` succeeded on the pod (so opencv/easyocr are there for text removal). |
