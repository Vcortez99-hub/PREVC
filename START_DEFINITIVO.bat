@echo off
echo ===============================================
echo    GERADOR RPA DOC - VERSAO DEFINITIVA
echo ===============================================
echo.
echo INICIANDO SERVIDOR...
echo.
echo URLs de acesso:
echo - http://localhost:5000
echo - http://127.0.0.1:5000
echo.
echo IMPORTANTE: Se aparecer alerta do Firewall,
echo            CLIQUE EM 'PERMITIR ACESSO'
echo.
echo Para parar: Feche esta janela ou Ctrl+C
echo ===============================================

python start_fixo.py

echo.
echo Servidor finalizado.
pause