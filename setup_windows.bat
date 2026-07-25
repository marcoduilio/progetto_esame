@echo off
setlocal

if not exist ".venv\Scripts\activate.bat" (
	py -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Ambiente pronto. Per riaprirlo in futuro usa:
echo   .venv\Scripts\activate.bat
endlocal
