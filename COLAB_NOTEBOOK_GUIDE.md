# Colab notebook guide (colab_image_test.ipynb)

Use this only for **one-off tests**. Keep real posting in `run_continuous_posts.py` locally.

---

## 1. Open the notebook in Cursor

- **File → Open File** (or `Ctrl+O`)
- Go to: `c:\Users\user\Documents\Auto Posting Facebook\`
- Open **`colab_image_test.ipynb`**

---

## 2. Use Colab as the kernel

1. Click the **kernel selector** (top right of the notebook, e.g. “Select Kernel” or Python version).
2. Choose **“New Colab Server”** (or “Connect to Colab”).
3. When asked for hardware, pick **T4 GPU**.
4. Wait until the kernel shows as **connected**.

---

## 3. Run the cells

- **Cell 1:** Installs `diffusers`, loads a small Stable Diffusion model, and generates one image. The image is shown in the notebook.
- **Cell 2:** Saves the image as `colab_generated_image.jpg`. On Colab it can also trigger a download.

Run Cell 1 first, then Cell 2.

---

## 4. Change what you’re testing

| Goal | What to change |
|------|----------------|
| **New image model** | In Cell 1, set `model_id` to another Hugging Face model (e.g. `"stabilityai/stable-diffusion-2-1-base"`). |
| **Caption / prompt** | In Cell 1, change the `prompt` string and run the cell again. |

---

**Reminder:** Do not run your full posting pipeline from Colab. Use this notebook only for testing models and prompts.
