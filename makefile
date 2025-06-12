MCU = atmega328p
PORT = COM3
BAUD = 115200
PROGRAMMER = arduino
TXT = teste1.txt
PYTHON_SCRIPT = main.py
ASM_SRC = out/gerado.S funcoes_assembly.S
ELF = out/programa.elf
HEX = out/programa.hex

# Alvo padrão: tudo
all: $(HEX) upload

# Executa o script Python
$(ASM_SRC): $(TXT)
python $(PYTHON_SCRIPT) $(TXT) --asm
# Compila o código assembly
$(ELF): $(ASM_SRC)
avr-gcc -mmcu=$(MCU) -Os -o $(ELF) $(ASM_SRC)

# Gera o arquivo HEX
$(HEX): $(ELF)
avr-objcopy -O ihex $(ELF) $(HEX)

# Faz upload para o microcontrolador
upload: $(HEX)
avrdude -c $(PROGRAMMER) -p $(MCU) -P $(PORT) -b $(BAUD) -U flash:w:$(HEX)

# Limpa os arquivos gerados
clean:
rm -f $(ELF) $(HEX) out/gerado.S

.PHONY: all upload clean
