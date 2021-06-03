# Dev Notes

## Char type casting difference between PyCLIF Python C API and Pybind11

*   PyCLIF Python C API casts C++ char type to Python int type. See
    https://source.corp.google.com/piper///depot/clif/python/types.h;l=154;rcl=359819524.
    However, Pybind11 casts C++ char type to Python str type. See
    https://source.corp.google.com/piper///depot/third_party/pybind11/include/pybind11/cast.h;l=493;rcl=366831977.
