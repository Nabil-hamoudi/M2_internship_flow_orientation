CC				= gcc
PYTHON			= python
EPANET_DIR		= librairie/EPANET_2_3_5_LINUX_x86_64
CFLAGS			= -O3 -Wall -I$(EPANET_DIR)
LDFLAGS			= -L$(EPANET_DIR) -lepanet2 -lm -Wl,-rpath=$(EPANET_DIR)
EXEC			= epanet_exec
SRC				= src/structure.c src/algorithm_flow.c src/epanet_parser.c src/main.c

ARCHIVE_NAME	= projet_eau.zip

SRC_FILES		= main.py src/ Makefile $(EPANET_DIR)/

.PHONY: all run clean zip

all: $(EXEC)

run: $(EXEC)
	./$(EXEC) $(ARGS)

$(EXEC): $(SRC)
	$(CC) $(CFLAGS) -o $@ $(SRC) $(LDFLAGS)

zip: clean
	zip -r $(ARCHIVE_NAME) $(SRC_FILES)

clean:
	rm -f $(EXEC) $(ARCHIVE_NAME)
