import sys
from cffi import FFI

ffibuilder = FFI()

ffibuilder.set_source('xorn._storage', '#include <xornstorage.h>')

with open(sys.argv[1]) as f:
    ffibuilder.cdef(f.read())

if __name__ == '__main__':
    ffibuilder.emit_c_code(sys.argv[2])
