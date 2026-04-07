@echo off
REM Reinstall transformers + tokenizers in THIS folder's default python (fix broken/partial installs).
REM Prefer: create .venv, activate, then run this with: .venv\Scripts\python -m pip ...
cd /d "%~dp0"
echo Using: 
where python
python -m pip install --force-reinstall "transformers>=4.52.0,<5.0" "tokenizers>=0.22.0,<=0.23.0"
echo.
echo Test (PyTorch-only; avoids TensorFlow + protobuf 5+ requirement):
set USE_TORCH=1
set USE_TF=0
python -c "from transformers import PreTrainedModel, AutoImageProcessor; print('OK')"
pause
