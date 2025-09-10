@echo off
echo ========================================
echo SCRIPT: INICIAR TRABALHO
echo ========================================
echo.

echo 1. Navegando para repositorio Git...
cd /d "C:\Users\jfrib\github\quzapp_v1.3"

echo 2. Baixando atualizacoes do GitHub...
git pull origin main

echo 3. Sincronizando arquivos (SEM apagar scripts)...
robocopy . "G:\Meu Drive\prjetos python\quiz\quiz v1.3" /E /XD .git venv __pycache__ .vscode node_modules scripts /XF *.pyc *.pyo .env /NP

echo 4. Retornando para pasta de trabalho...
cd /d "G:\Meu Drive\prjetos python\quiz\quiz v1.3"

echo.
echo ========================================
echo PRONTO PARA TRABALHAR!
echo ========================================
echo Voce pode agora fazer suas alteracoes no VS Code
echo Quando terminar, execute: scripts\02_finalizar.bat
echo.

pause