@echo off
rem Script de Build para Compilador RA4 -> Arduino

rem --- Configuracao ---
set MCU=atmega328p
set PROGRAMMER=arduino
set BAUDRATE=115200
set PORT=COM3

rem --- Verificacao ---
if "%1"=="" (
    echo.
    echo Uso: %0 ^<nome_do_arquivo_sem_extensao^>
    echo Exemplo: %0 teste1
    echo.
    goto :eof
)
set BASENAME=%1
set SRC_FILE=%BASENAME%.txt
set GENERATED_S_FILE=%BASENAME%.S
set ELF_FILE=out\%BASENAME%.elf
set HEX_FILE=out\%BASENAME%.hex

rem --- Comandos ---
echo.
echo [1/3] Gerando codigo Assembly de %SRC_FILE%...
python main.py %SRC_FILE% --asm
if %errorlevel% neq 0 (
    echo *** Falha ao gerar o codigo Assembly.
    goto :eof
)

echo.
echo [2/3] Compilando o projeto com avr-gcc...
if not exist out mkdir out
rem Compila o unico arquivo .S gerado, que agora contem tudo.
avr-gcc -mmcu=%MCU% -o %ELF_FILE% %GENERATED_S_FILE%
if %errorlevel% neq 0 (
    echo *** Falha na compilacao (avr-gcc).
    goto :eof
)

echo.
echo [3/3] Convertendo para .hex e enviando para o Arduino...
avr-objcopy -O ihex %ELF_FILE% %HEX_FILE%
if %errorlevel% neq 0 (
    echo *** Falha na conversao para .hex.
    goto :eof
)
avrdude -c %PROGRAMMER% -p %MCU% -P %PORT% -b %BAUDRATE% -U flash:w:%HEX_FILE%
if %errorlevel% neq 0 (
    echo *** Falha no envio (avrdude). Verifique a porta e a conexao.
    goto :eof
)

echo.
echo --- PROCESSO CONCLUIDO COM SUCESSO! ---