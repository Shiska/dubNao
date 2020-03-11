@echo off

cd /D "%~dp0"

if not exist env (
    python -m venv env
)

call env\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirments.txt

if "%~2" EQU "" (
    python dublicates.py "img"
) else (
    start pythonw dublicates.py "%~2"
)

call deactivate