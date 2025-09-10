@echo off
echo ========================================
echo ADICIONAR PERGUNTAS - FLUXO CORRETO
echo ========================================
echo.

echo Este script adiciona perguntas seguindo o fluxo correto:
echo 1. Adiciona ao staging (perguntas_test.json)
echo 2. Executa sincronizacao automatica
echo 3. Mantem controle de duplicatas
echo.

set /p arquivo=Digite o caminho do arquivo de perguntas a adicionar: 

if "%arquivo%"=="" (
    echo Erro: Nenhum arquivo informado!
    pause
    exit /b 1
)

if not exist "%arquivo%" (
    echo Erro: Arquivo nao encontrado: %arquivo%
    pause
    exit /b 1
)

echo.
echo 1. Adicionando ao staging...
python -c "
import sys
sys.path.append('.')
from adicionar_ao_staging import adicionar_perguntas_ao_staging
adicionar_perguntas_ao_staging('%arquivo%')
"

if %ERRORLEVEL% neq 0 (
    echo Erro ao adicionar ao staging!
    pause
    exit /b 1
)

echo.
echo 2. Executando sincronizacao...
python sincronizar_perguntas.py

if %ERRORLEVEL% neq 0 (
    echo Erro na sincronizacao!
    pause
    exit /b 1
)

echo.
echo ========================================
echo PROCESSO CONCLUIDO COM SUCESSO!
echo ========================================
echo.
echo As perguntas foram adicionadas seguindo o fluxo correto:
echo - Staging atualizado
echo - Sincronizacao executada
echo - Duplicatas controladas
echo.

pause
