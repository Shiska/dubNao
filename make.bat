@setlocal
@echo off

cd /D "%~dp0"

if not exist env (
    python -m venv env
)
call env\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirments.txt

if "%~x1" EQU ".py" (
    python dublicates.py
) else (
    start pythonw dublicates.py %*
)