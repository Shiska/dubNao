@setlocal
@echo off

for %%i in (.) do (
    set folder=%%~ni
)
cd ..

call env\Scripts\activate

python -m %folder%.%~n1