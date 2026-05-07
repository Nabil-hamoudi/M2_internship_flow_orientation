CC		 = gcc
PYTHON		 = python
SRC_DIR		 = src
LIB_DIR		 = librairie
EPANET_DIR	 = $(LIB_DIR)/EPANET_2_3_5_LINUX_x86_64
CFLAGS		 = -O3 -Wall -I$(EPANET_DIR) -fPIC
EXTERNAL_LDFLAGS = -L$(EPANET_DIR) -lepanet2 -lm -Wl,-rpath=$(EPANET_DIR)
EXEC		 = epanet_exec
LIB		 = $(LIB_DIR)/libreseau.so
MAIN_C		 = $(SRC_DIR)/api.c
SRC		 = $(SRC_DIR)/structure.c $(SRC_DIR)/algorithm_flow.c $(SRC_DIR)/epanet_parser.c
HDR		 = $(SRC_DIR)/structure.h $(SRC_DIR)/algorithm_flow.h $(SRC_DIR)/epanet_parser.h
MAIN_PY		 = main.py analyse.py
CFFI		 = $(SRC_DIR)/build_ffi.py

OBJ		 = $(patsubst $(SRC_DIR)/%.c, $(LIB_DIR)/%.o, $(SRC))

ARCHIVE_NAME	 = projet_eau.zip

SRC_FILES	 = main.py $(SRC_DIR)/ Makefile $(EPANET_DIR)/

.PHONY: all run clean zip

all: $(LIB_DIR) $(EPANET_DIR) $(LIB) $(EXEC)

$(LIB_DIR):
	@mkdir -p $@

$(EPANET_DIR):
	curl https://github.com/OpenWaterAnalytics/EPANET/releases/download/v2.3.5/EPANET_2_3_5_LINUX_x86_64.zip EPANET_2_3_5_LINUX_x86_64.zip
	unzip EPANET_2_3_5_LINUX_x86_64.zip -d $@
	rm EPANET_2_3_5_LINUX_x86_64.zip

$(LIB_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

$(LIB): $(OBJ)
	$(CC) -shared -o $@ $(OBJ) $(EXTERNAL_LDFLAGS)

$(EXEC): $(LIB) $(MAIN_C)
	$(CC) $(CFLAGS) -o $@ $(MAIN_C) -L$(LIB_DIR) -lreseau $(EXTERNAL_LDFLAGS) -Wl,-rpath,.

run: $(EXEC)
	./$(EXEC) $(ARGS)

zip: clean
	zip -r $(ARCHIVE_NAME) $(SRC) $(HDR) $(IPYN) $(MAIN_C) $(CFFI)

clean:
	rm -f $(OBJ) $(EXEC) $(LIB)
