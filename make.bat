@echo off

cd /D "%~dp0"

if not exist env (
    python -m venv env
)

call env\Scripts\activate

REM python -m pip install --upgrade pip
REM pip install -r requirments.txt

if "%~2" EQU "" (
    python dublicates.py "..\Drive_NSFW\Bilder\Anime\SauceNAO\SauceNAO" "img"
) else (
    start pythonw dublicates.py "%~2"
)

REM "..\Drive_NSFW\Bilder\Anime\SauceNAO\SauceNAO"

call deactivate