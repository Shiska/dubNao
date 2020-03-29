@setlocal
@echo off

cd /D "%~dp0"

if not exist env (
    python -m venv env
)
call env\Scripts\activate

REM python -m pip install --upgrade pip
REM pip install -r requirments.txt

if "%~x1" EQU ".py" (
    python dublicates.py "..\Drive_NSFW\Bilder\Anime\SauceNAO\SauceNAO"
) else (
    start pythonw dublicates.py %*
)