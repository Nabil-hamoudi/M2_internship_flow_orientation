import os
import re
from cffi import FFI

ffi = FFI()

cdef_content = """
struct Project;
typedef struct Project *EN_Project;
"""

src_dir = os.path.abspath("./src")

headers = [
    os.path.join(src_dir, "structure.h"),
    os.path.join(src_dir, "epanet_parser.h"),
    os.path.join(src_dir, "algorithm_flow.h")
]

for header in headers:
    with open(header, "r") as f:
        content = f.read()
        content = re.sub(r'#include\s+.*', '', content)
        cdef_content += content + "\n"

ffi.cdef(cdef_content)

lib_dir = os.path.abspath("./librairie")
epanet_dir = os.path.join(lib_dir, "EPANET_2_3_5_LINUX_x86_64")

ffi.set_source(
    "_reseau_C",
    """
    #include "structure.h"
    #include "epanet_parser.h"
    #include "algorithm_flow.h"
    """,
    include_dirs=[src_dir, epanet_dir, os.path.join(epanet_dir, "include")],
    libraries=["reseau", "epanet2"],
    library_dirs=[lib_dir, epanet_dir, os.path.join(epanet_dir, "lib")],
    extra_link_args=[
        f"-Wl,-rpath,{lib_dir}",
        f"-Wl,-rpath,{epanet_dir}",
        f"-Wl,-rpath,{os.path.join(epanet_dir, 'lib')}"
    ]
)

if __name__ == "__main__":
    ffi.compile(tmpdir=lib_dir, verbose=True)
