@echo off
echo ========================================
echo SCRIPT: FINALIZAR TRABALHO
echo ========================================
echo.

set /p mensagem=Digite uma mensagem para o commit (ou Enter para padrao): 

if "%mensagem%"=="" (
    for /f "tokens=1-4 delims=/ " %%i in ('date /t') do set mydate=%%i/%%j/%%k
    for /f "tokens=1-2 delims=: " %%i in ('time /t') do set mytime=%%i:%%j
    set mensagem=Atualizacoes realizadas em !mydate! !mytime!
)

echo Mensagem do commit: %mensagem%
echo.

echo 1. Sincronizando alteracoes (SEM apagar pasta Git)...
robocopy "G:\Meu Drive\prjetos python\quiz\quiz v1.3" "C:\Users\jfrib\github\quzapp_v1.3" /E /XD venv __pycache__ .git .vscode node_modules /XF *.pyc *.pyo .env /PURGE /NP

echo 2. Navegando para repositorio Git...
cd /d "C:\Users\jfrib\github\quzapp_v1.3"

echo 3. Adicionando arquivos...
git add .

echo 4. Fazendo commit...
git commit -m "%mensagem%"

echo 5. Enviando para GitHub...
git push origin main

echo 6. Retornando para pasta de trabalho...
cd /d "G:\Meu Drive\prjetos python\quiz\quiz v1.3"

echo.
echo ========================================
echo TRABALHO FINALIZADO E SINCRONIZADO!
echo ========================================
echo Suas alteracoes foram enviadas para o GitHub
echo.

pause
