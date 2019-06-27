@echo off
for /f "delims=\" %%a in ("%cd%") do if "%%~nxa"=="scripts" cd ..

where pipenv >NUL 2>&1 || echo Please install pipenv first. && goto :EOF

set install-dir="%LOCALAPPDATA%\trakt scrobbler"
echo Installing to %install-dir%

xcopy /i /s /r /y .\trakt_scrobbler %install-dir%\ >NUL
xcopy /i /r /y Pipfile %install-dir%\ >NUL
xcopy /i /r /y Pipfile.lock %install-dir%\ >NUL

pushd %install-dir%
pipenv install

for /F "tokens=* USEBACKQ" %%F in (`pipenv --venv`) do set venv_path=%%F
set py_path="%venv_path%\Scripts\pythonw.exe"

echo Adding to startup commands.
set batch_path="%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\trakt-scrobbler.bat"
echo @echo off >%batch_path%
echo pushd %install-dir% >>%batch_path%
echo start %py_path% %install-dir%\main.py >>%batch_path%

echo Setup complete. Starting device authentication.
pipenv run python -c "import trakt_interface; trakt_interface.get_access_token()"
popd
%py_path% %install-dir%\main.py
echo Done.
:EOF
