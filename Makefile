CC		= gcc
PYTHON		= python

EPANET_DIR	= librairie/EPANET_2_3_5_LINUX_x86_64

CFLAGS		= -O3 -Wall -I$(EPANET_DIR)

LDFLAGS		= -L$(EPANET_DIR) -lepanet2 -lm -Wl,-rpath=$(EPANET_DIR)

EXEC		= epanet_exec

SRC		= src/structure.c src/ford_fukerson.c src/epanet_parser.c

ARCHIVE_NAME	= projet_eau.zip

SRC_FILES	= main.py src/ Makefile $(EPANET_DIR)/

.PHONY: all run clean zip

all: $(EXEC)

run: $(EXEC)
	$(PYTHON) main.py

$(EXEC): $(SRC)
	$(CC) $(CFLAGS) -o $@ $(SRC) $(LDFLAGS)

zip: clean
	zip -r $(ARCHIVE_NAME) $(SRC_FILES)

# Règle de nettoyage
clean:
	rm -f $(EXEC) $(ARCHIVE_NAME)
	rm -rf __pycache__
