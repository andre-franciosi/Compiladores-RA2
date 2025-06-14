# ---------- Configurações ----------
MCU          = atmega328p
PORT         = COM3
BAUD         = 115200
PROGRAMMER   = arduino

TXT          = teste1.txt
PYTHON_SCRIPT = main.py

ASM_SRC      = out/gerado.S funcoes_assembly.S
ELF          = out/programa.elf
HEX          = out/programa.hex

# ---------- Alvos principais ----------
all: $(HEX) upload

# ---------- Geração do Assembly ----------
out/gerado.S: $(TXT) | out
	python $(PYTHON_SCRIPT) $(TXT) --asm      

# ---------- Compilação ----------
$(ELF): $(ASM_SRC) | out
	avr-gcc -mmcu=$(MCU) -Os -o $(ELF) $(ASM_SRC)

# ---------- Conversão ELF → HEX ----------
$(HEX): $(ELF)
	avr-objcopy -O ihex $(ELF) $(HEX)

# ---------- Upload ----------
upload: $(HEX)
	avrdude -c $(PROGRAMMER) -p $(MCU) -P $(PORT) -b $(BAUD) -U flash:w:$(HEX)

# ---------- Utilitários ----------
clean:
	rm -f $(ELF) $(HEX) out/gerado.S

out:
	mkdir out  # no Windows “mkdir” já ignora se a pasta existir

.PHONY: all upload clean
