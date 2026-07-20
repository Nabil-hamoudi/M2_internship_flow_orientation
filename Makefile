CC		 = gcc
PYTHON		 = python
SRC_DIR		 = src
LIB_DIR		 = librairie
EPANET_DIR	 = $(LIB_DIR)/EPANET_2_3_5_LINUX_x86_64
CFLAGS		 = -O3 -Wall -I$(EPANET_DIR) -fPIC
EXTERNAL_LDFLAGS = -L$(EPANET_DIR) -lepanet2 -lm -Wl,-rpath=$(EPANET_DIR)
LIB		 = $(LIB_DIR)/libreseau.so
SRC		 = $(SRC_DIR)/structure.c $(SRC_DIR)/algorithm_flow.c $(SRC_DIR)/epanet_parser.c
HDR		 = $(SRC_DIR)/structure.h $(SRC_DIR)/algorithm_flow.h $(SRC_DIR)/epanet_parser.h
MAIN_PY		 = main.py analyse.py
CFFI		 = $(SRC_DIR)/build_ffi.py
OBJ		 = $(patsubst $(SRC_DIR)/%.c, $(LIB_DIR)/%.o, $(SRC))
ARCHIVE_NAME	 = projet_eau.zip
SRC_FILES	 = $(MAIN_PY) $(SRC_DIR)/ Makefile

.PHONY: all build run clean zip build_python

all: $(LIB_DIR) $(EPANET_DIR) $(LIB) build_python

build: clean all

$(LIB_DIR):
	@mkdir -p $@

$(EPANET_DIR):
	curl -L -o EPANET_2_3_5_LINUX_x86_64.zip https://github.com/OpenWaterAnalytics/EPANET/releases/download/v2.3.5/EPANET_2_3_5_LINUX_x86_64.zip
	unzip EPANET_2_3_5_LINUX_x86_64.zip -d $(LIB_DIR)
	rm EPANET_2_3_5_LINUX_x86_64.zip

$(LIB_DIR)/%.o: $(SRC_DIR)/%.c | $(EPANET_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(LIB): $(OBJ)
	$(CC) -shared -o $@ $(OBJ) $(EXTERNAL_LDFLAGS)

build_python: $(LIB)
	$(PYTHON) $(CFFI)

zip: clean
	zip -r $(ARCHIVE_NAME) $(SRC_FILES)

clean:
	rm -rf $(LIB_DIR) $(EXEC)
