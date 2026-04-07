#!/usr/bin/env python3
"""
Hands-free support for **Cursor-only** inbound images (no Z-Image / no PIL placeholders).

Modes (``CURSOR_INBOUND_AUTO_MODE``):

- **api** — Launch a `Cursor Background Agent`_ (HTTPS API) when ``CURSOR_POST_IMAGE_PROMPT.txt`` changes;
  poll until the run finishes; download the bitmap from the agent's GitHub branch to the local inbound path.
  Needs ``CURSOR_API_KEY`` (Dashboard → Integrations), ``CURSOR_BACKGROUND_AGENT_REPO`` or ``git remote origin``
  on GitHub, and usually ``CURSOR_BACKGROUND_AGENT_AUTO=1`` so **auto** mode can pick API without surprises.

- **focus** — Open the prompt in Cursor (``cursor -g path:1``) once per new bundle (you still trigger the image tool).

- **auto** (default) — Use **api** if ``CURSOR_API_KEY`` + ``CURSOR_BACKGROUND_AGENT_AUTO=1`` + GitHub repo; else **focus**
  if the ``cursor`` CLI exists; else **off**.

- **off** — Poll only.

.. _Cursor Background Agent: https://cursor.com/docs

Env (optional):

  CURSOR_INBOUND_BRIDGE_POLL_SECONDS — default 6
  CURSOR_BACKGROUND_AGENT_MAX_WAIT_SECONDS — default 600 (poll agent + raw download)
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))
os.chdir(_BASE)

_LOCK = _BASE / ".cursor_inbound_auto_bridge.lock"
_API = "https://api.cursor.com"
_RUNNING = frozenset(
    {"CREATING", "RUNNING", "PENDING", "QUEUED", "STARTING", "PROVISIONING", "INITIALIZING"}
)
_FAILED = frozenset({"FAILED", "ERROR", "CANCELLED", "CANCELED", "STOPPED"})


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _poll_seconds() -> float:
    try:
        return max(3.0, float((os.environ.get("CURSOR_INBOUND_BRIDGE_POLL_SECONDS") or "6").strip()))
    except ValueError:
        return 6.0


def _max_agent_wait() -> float:
    try:
        return max(60.0, float((os.environ.get("CURSOR_BACKGROUND_AGENT_MAX_WAIT_SECONDS") or "600").strip()))
    except ValueError:
        return 600.0


def _parse_bundle_paths(text: str) -> tuple[str | None, str | None]:
    if not (text or "").strip():
        return None, None
    lines = text.replace("\r\n", "\n").split("\n")
    inbound: str | None = None
    in_save = False
    in_prompt = False
    prompt_lines: list[str] = []
    for line in lines:
        s = line.strip()
        if "Save the file to this exact path" in line and "===" in line:
            in_save = True
            continue
        if in_save and s and not s.startswith("==="):
            inbound = s.strip()
            in_save = False
            continue
        if "Image prompt (paste into Cursor image tool)" in line and "===" in line:
            in_prompt = True
            continue
        if in_prompt:
            if s.startswith("===") and "Image prompt" not in line:
                break
            prompt_lines.append(line)
    prompt = "\n".join(prompt_lines).strip() if prompt_lines else None
    if inbound:
        inbound = os.path.abspath(os.path.expandvars(inbound.strip()))
    return inbound, prompt


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _inbound_repo_relpath(inbound_abs: str, base: Path) -> str:
    try:
        rel = os.path.relpath(inbound_abs, str(base))
        if rel.startswith(".."):
            return Path(inbound_abs).name
        return rel.replace("\\", "/")
    except ValueError:
        return Path(inbound_abs).name


def _origin_to_https(url: str) -> str | None:
    u = (url or "").strip()
    if not u:
        return None
    if u.startswith("git@github.com:"):
        path = u.split(":", 1)[1].strip()
        if path.endswith(".git"):
            path = path[:-4]
        return f"https://github.com/{path}"
    if u.startswith("https://github.com/") or u.startswith("http://github.com/"):
        u = u.replace("http://", "https://", 1)
        if u.endswith(".git"):
            u = u[:-4]
        return u.rstrip("/")
    return None


def _git_origin_https() -> str | None:
    try:
        out = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(_BASE),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if out.returncode != 0:
            return None
        return _origin_to_https(out.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        return None


def _effective_repo() -> str:
    try:
        from config import CURSOR_BACKGROUND_AGENT_REPO
    except ImportError:
        CURSOR_BACKGROUND_AGENT_REPO = ""
    r = (CURSOR_BACKGROUND_AGENT_REPO or "").strip()
    if r:
        return (_origin_to_https(r) or r.rstrip("/")).replace(".git", "")
    return _git_origin_https() or ""


def _find_cursor_cli() -> str | None:
    w = shutil.which("cursor")
    if w:
        return w
    for cand in (
        r"C:\Program Files\cursor\resources\app\bin\cursor.cmd",
        r"C:\Program Files\cursor\resources\app\bin\cursor.exe",
    ):
        if os.path.isfile(cand):
            return cand
    return None


def _auto_mode() -> str:
    raw = (os.environ.get("CURSOR_INBOUND_AUTO_MODE") or "auto").strip().lower()
    if raw == "off":
        return "off"
    if raw == "focus":
        return "focus"
    if raw == "api":
        return "api"
    try:
        from config import CURSOR_API_KEY, CURSOR_BACKGROUND_AGENT_AUTO
    except ImportError:
        CURSOR_API_KEY = os.environ.get("CURSOR_API_KEY", "").strip()
        _a = (os.environ.get("CURSOR_BACKGROUND_AGENT_AUTO") or "").strip().lower()
        CURSOR_BACKGROUND_AGENT_AUTO = _a in ("1", "true", "yes", "on")
    if CURSOR_API_KEY and CURSOR_BACKGROUND_AGENT_AUTO and _effective_repo():
        return "api"
    if _find_cursor_cli():
        return "focus"
    return "off"


def _api_request(method: str, path: str, api_key: str, body: dict | None = None, timeout: int = 120) -> dict:
    url = f"{_API}{path}"
    data = None
    headers = {"Authorization": f"Bearer {api_key}"}
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {path}: {err}") from e


def _github_raw_url(repo_https: str, branch: str, relpath: str) -> str:
    repo_https = repo_https.rstrip("/")
    prefix = "https://github.com/"
    if not repo_https.startswith(prefix):
        raise ValueError(f"Not a github.com repo URL: {repo_https}")
    rest = repo_https[len(prefix) :]
    owner, _, name = rest.partition("/")
    name = name.split("/")[0]
    if not owner or not name:
        raise ValueError(f"Bad repo URL: {repo_https}")
    segs = [urllib.parse.quote(s, safe="") for s in branch.split("/")]
    br = "/".join(segs)
    rel = relpath.strip("/").replace("\\", "/")
    rel_enc = "/".join(urllib.parse.quote(p, safe="") for p in rel.split("/"))
    return f"https://raw.githubusercontent.com/{owner}/{name}/{br}/{rel_enc}"


def _download_raw(url: str, dest: Path, timeout: int = 60) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if len(data) < 200:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(dest)
        return True
    except Exception:
        return False


def _launch_agent(api_key: str, repo: str, ref: str, prompt_text: str) -> str:
    source: dict = {"repository": repo}
    if (ref or "").strip():
        source["ref"] = ref.strip()
    body = {"prompt": {"text": prompt_text}, "source": source}
    data = _api_request("POST", "/v0/agents", api_key, body, timeout=120)
    aid = data.get("id") or data.get("agentId")
    if not aid:
        raise RuntimeError(f"Unexpected launch response: {data!r}")
    return str(aid)


def _get_agent(api_key: str, agent_id: str) -> dict:
    return _api_request("GET", f"/v0/agents/{agent_id}", api_key, body=None, timeout=60)


def _run_background_agent(
    api_key: str,
    repo: str,
    ref: str,
    bundle: str,
    rel_image: str,
) -> tuple[str | None, str | None]:
    """
    Returns (branch_name, error_message).
    """
    instructions = (
        "You are working in a GitHub checkout of this repository.\n\n"
        "TASK (Facebook cursor_only pipeline — read AGENTS.md in the repo root):\n"
        "1. Use Cursor's **native image / chat image generation** (the same product capability as the IDE image tool). "
        "Do **not** create the post image with PIL, matplotlib, Pillow, local Z-Image, or external diffusion scripts.\n"
        "2. The operator bundle below is also the file CURSOR_POST_IMAGE_PROMPT.txt. Follow it exactly.\n"
        "3. Commit the final bitmap to the repository at this path (relative to repo root): "
        f"`{rel_image}`\n"
        "4. Commit on your working branch and push so the file is available on the branch returned by the API.\n\n"
        "---BEGIN BUNDLE---\n"
        f"{bundle}\n"
        "---END BUNDLE---\n"
    )
    agent_id = _launch_agent(api_key, repo, ref, instructions)
    print(f"[cursor_inbound_auto_bridge] Launched background agent {agent_id}", flush=True)
    deadline = time.time() + _max_agent_wait()
    branch: str | None = None
    last_status = ""
    while time.time() < deadline:
        info = _get_agent(api_key, agent_id)
        status = str(info.get("status") or "").upper()
        last_status = status
        tgt = info.get("target") or {}
        if isinstance(tgt, dict) and tgt.get("branchName"):
            branch = str(tgt["branchName"])
        if status in _FAILED:
            return None, f"agent status={status}"
        if status and status not in _RUNNING:
            if branch:
                return branch, None
            return None, f"agent finished ({status}) but no branchName in API response"
        time.sleep(10.0)
    return None, f"timeout after {_max_agent_wait():.0f}s (last status={last_status!r})"


def _acquire_lock() -> bool:
    if _LOCK.is_file():
        try:
            pid = int(_LOCK.read_text(encoding="utf-8").strip() or "0")
        except (ValueError, OSError):
            pid = 0
        if pid > 0 and _pid_alive(pid):
            print("[cursor_inbound_auto_bridge] Another bridge is running. Exiting.", flush=True)
            return False
        try:
            _LOCK.unlink()
        except OSError:
            pass
    try:
        _LOCK.write_text(str(os.getpid()), encoding="utf-8")
    except OSError:
        pass
    return True


def _release_lock() -> None:
    try:
        if _LOCK.is_file():
            cur = int(_LOCK.read_text(encoding="utf-8").strip() or "0")
            if cur == os.getpid():
                _LOCK.unlink()
    except OSError:
        pass


def _focus_prompt(path: Path) -> None:
    cli = _find_cursor_cli()
    if not cli or not path.is_file():
        return
    arg = f"{path.resolve()}:{1}"
    try:
        subprocess.Popen(
            [cli, "-g", arg],
            cwd=str(_BASE),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        print(f"[cursor_inbound_auto_bridge] focus: opened {path} in Cursor", flush=True)
    except OSError as e:
        print(f"[cursor_inbound_auto_bridge] focus failed: {e}", flush=True)


def main() -> int:
    import atexit

    atexit.register(_release_lock)
    if not _acquire_lock():
        return 0

    try:
        import protobuf_runtime_shim  # noqa: F401
        from config import (
            CURSOR_API_KEY,
            CURSOR_BACKGROUND_AGENT_REF,
            CURSOR_POST_IMAGE_INBOUND,
            CURSOR_POST_IMAGE_PROMPT_PATH,
        )
    except ImportError:
        CURSOR_API_KEY = os.environ.get("CURSOR_API_KEY", "").strip()
        _r = os.environ.get("CURSOR_BACKGROUND_AGENT_REF")
        CURSOR_BACKGROUND_AGENT_REF = "main" if _r is None else _r.strip()
        CURSOR_POST_IMAGE_INBOUND = str(_BASE / "cursor_post_image.png")
        CURSOR_POST_IMAGE_PROMPT_PATH = str(_BASE / "CURSOR_POST_IMAGE_PROMPT.txt")

    mode = _auto_mode()
    prompt_path = Path(CURSOR_POST_IMAGE_PROMPT_PATH).resolve()
    default_inbound = Path(CURSOR_POST_IMAGE_INBOUND).resolve()
    poll = _poll_seconds()

    _ref_note = (
        "(omit → GitHub default)"
        if not (CURSOR_BACKGROUND_AGENT_REF or "").strip()
        else repr((CURSOR_BACKGROUND_AGENT_REF or "").strip())
    )
    print(
        f"[cursor_inbound_auto_bridge] mode={mode} poll={poll}s  api_ref={_ref_note}\n"
        f"  prompt={prompt_path}\n  default_inbound={default_inbound}\n  Ctrl+C to stop.",
        flush=True,
    )

    last_sig: str | None = None
    last_focus_sig: str | None = None

    while True:
        try:
            if not prompt_path.is_file():
                time.sleep(poll)
                continue
            try:
                mtime = prompt_path.stat().st_mtime
                sig = f"{mtime:.6f}:{_file_sha256(prompt_path)}"
            except OSError:
                time.sleep(poll)
                continue

            if sig == last_sig:
                time.sleep(poll)
                continue

            bundle = prompt_path.read_text(encoding="utf-8", errors="replace")
            inbound_abs, image_prompt = _parse_bundle_paths(bundle)
            if not image_prompt:
                time.sleep(poll)
                continue
            inbound = Path(inbound_abs) if inbound_abs else default_inbound

            if mode == "focus":
                if sig != last_focus_sig:
                    last_focus_sig = sig
                    _focus_prompt(prompt_path)
                last_sig = sig
                time.sleep(poll)
                continue

            if mode == "off":
                last_sig = sig
                time.sleep(poll)
                continue

            if mode == "api":
                if not CURSOR_API_KEY:
                    print("[cursor_inbound_auto_bridge] api mode but CURSOR_API_KEY missing.", flush=True)
                    last_sig = sig
                    time.sleep(poll)
                    continue
                repo = _effective_repo()
                if not repo:
                    print(
                        "[cursor_inbound_auto_bridge] api mode but no GitHub repo "
                        "(set CURSOR_BACKGROUND_AGENT_REPO or git remote origin).",
                        flush=True,
                    )
                    last_sig = sig
                    time.sleep(poll)
                    continue
                rel = _inbound_repo_relpath(str(inbound), _BASE)
                try:
                    branch, err = _run_background_agent(
                        CURSOR_API_KEY,
                        repo,
                        CURSOR_BACKGROUND_AGENT_REF,
                        bundle,
                        rel,
                    )
                    if err:
                        print(f"[cursor_inbound_auto_bridge] API path failed: {err}", flush=True)
                        last_sig = sig
                        time.sleep(poll)
                        continue
                    assert branch is not None
                    raw_url = _github_raw_url(repo, branch, rel)
                    ok = False
                    for attempt in range(36):
                        if _download_raw(raw_url, inbound):
                            ok = True
                            break
                        time.sleep(10.0)
                    if ok:
                        print(f"[cursor_inbound_auto_bridge] Wrote inbound from GitHub raw: {inbound}", flush=True)
                    else:
                        print(
                            f"[cursor_inbound_auto_bridge] Agent branch={branch} but raw download failed:\n  {raw_url}",
                            flush=True,
                        )
                except Exception as e:
                    err = str(e)
                    print(f"[cursor_inbound_auto_bridge] ERROR: {e}", flush=True)
                    if (
                        "Failed to verify existence of branch" in err
                        or "branch name is correct" in err
                        or "Failed to determine repository default branch" in err
                    ):
                        print(
                            "[cursor_inbound_auto_bridge] Cursor cannot read this GitHub repo over the API. "
                            "Fix: https://cursor.com/dashboard → Integrations (or Cloud Agents) → GitHub → "
                            "authorize the Cursor GitHub App for the **same GitHub account that owns** "
                            "CURSOR_BACKGROUND_AGENT_REPO in .env, and allow access to that repository. "
                            "Then restart this bridge.",
                            flush=True,
                        )
                last_sig = sig
                time.sleep(poll)
                continue

            last_sig = sig
            time.sleep(poll)

        except KeyboardInterrupt:
            print("\n[cursor_inbound_auto_bridge] Stopped.", flush=True)
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
