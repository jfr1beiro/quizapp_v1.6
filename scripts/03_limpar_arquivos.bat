@echo off
echo ========================================
echo LIMPEZA DE ARQUIVOS DESNECESSARIOS
echo ========================================
echo.

echo Limpando arquivos temporarios e desnecessarios...
echo.

echo 1. Removendo arquivos Python temporarios...
for /r . %%d in (__pycache__) do (
    if exist "%%d" (
        echo    Removendo: %%d
        rmdir /s /q "%%d" 2>nul
    )
)

echo 2. Removendo arquivos .pyc...
del /s /q *.pyc 2>nul

echo 3. Removendo arquivos .tmp...
del /s /q *.tmp 2>nul

echo 4. Mantendo apenas 3 backups mais recentes...
python -c "
import os, glob
from datetime import datetime

# Encontrar todos os backups
backups = glob.glob('data/*.backup*') + glob.glob('*.backup*')
if len(backups) > 3:
    backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    for backup in backups[3:]:
        try:
            os.remove(backup)
            print(f'   Removido: {os.path.basename(backup)}')
        except:
            pass
else:
    print('   Nenhum backup antigo para remover')
"

echo.
echo ========================================
echo LIMPEZA CONCLUIDA!
echo ========================================
echo.
echo Arquivos mantidos:
echo - Scripts essenciais
echo - Dados principais (perguntas.json)
echo - 3 backups mais recentes
echo - Arquivos de configuracao
echo.

pause
