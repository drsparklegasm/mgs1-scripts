@echo off
setlocal

REM This script runs the python script recursively, first to export all calls, then translate individual calls

set SCRIPT=myScripts\RadioDatToolsXMLoutput.py
set RADIODAT=%1
set input_dir=extractedCallBins

python %SCRIPT% %RADIODAT% Headers.txt -sH

for %%f in (%input_dir%\*.bin) do (
    set base_filename=%%~nf
    set output=%input_dir%\%base_filename%-decrypted.txt

    python myScripts\RadioDatTools.py %%f %output% -zx
)

endlocal