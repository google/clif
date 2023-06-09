# C++ Language Interface Foundation (CLIF)

![CI](https://github.com/google/clif/workflows/CI/badge.svg?branch=main&event=push)

PyCLIF defines a C++ API to be wrapped via a concise
*What You See Is What You Get* interface file
([example](
https://github.com/google/clif/blob/main/examples/wrapmethod/python/wrapmethod.clif)),
with a syntax derived from [pytypedecl](https://github.com/google/pytypedecl).

About the name of this repo: CLIF was started as a common foundation for
creating C++ wrapper generators for various languages. However, currently
Python is the only target language, and there is no development activity
for other target languages.

## Overview

PyCLIF consists of four parts:

  1. Parser
  1. Matcher
  1. Generator
  1. Runtime

### Parser

The parser converts a language-friendly C++ API description to the
language-agnostic internal format and passes it to the Matcher.

### Matcher

The matcher parses selected C++ headers with Clang (LLVM's C++ compiler) and
collects type information.  That info is passed to the Generator.

### Generator

The generator emits C++ source code for the wrapper.

The generated wrapper needs to be built according with language extension rules.
Usually that wrapper will call into the Runtime.

### Runtime

The runtime C++ library holds type conversion routines that are specific to
each target language but are the same for every generated wrapper.

## Python CLIF

See complete implementation of a Python wrapper generator in the `/python/`
subdirectory.  Both Python 2 and 3 are supported.

## Installation

### Prerequisites

 1. We use [CMake](http://llvm.org/docs/CMake.html), so make sure CMake
    version 3.5 or later is available.
    (For example, Debian 8 only has version 3.0,
    so in that case you'll need to install an up-to-date CMake.)

 1. We use Google
    [protobuf](https://developers.google.com/protocol-buffers/docs/downloads)
    for inter-process communication between the CLIF frontend and backend.
    Version 3.8.0 or later is required.
    Please install protobuf for both C++ and Python from source, as we will
    need some protobuf source code later on.

 1. You must have [virtualenv](https://pypi.python.org/pypi/virtualenv)
    installed.

 1. You must have pyparsing installed, so we can build protobuf. Use
    `pip install 'pyparsing==2.2.2'` to fetch the correct version.

 1. Make sure `pkg-config --libs python` works (e.g. install `python-dev` and
    `pkg-config`).

 1. We use [Clang (LLVM's C++ compiler)](http://llvm.org/) to parse C++ headers,
    so make sure Clang and LLVM version 11 is available. On Ubuntu and
    Debian, you can install the prebuilt version from https://apt.llvm.org.

 1. You must have [abseil-cpp](https://github.com/abseil/abseil-cpp) installed.

 1. We use [googletest](https://github.com/google/googletest) for unit testing
    C++ libraries.

For references, there is a [Dockerfile](https://github.com/google/clif/blob/main/Dockerfile)
running an Ubuntu image with all the prerequisites already installed. See the
instructions at the top of the file.

### Building

To build and install CLIF to a virtualenv, run:

```bash
virtualenv --python=python3.x clif-venv
./INSTALL.sh clif-venv/bin/python
```


The following outlines the steps in `INSTALL.sh` for clarification.

1.  Build and install the CLIF backend. If you use
    [Ninja](https://ninja-build.org/) instead of `make` your build will go
    significantly faster. It is used by Chromium, LLVM et al. Look at
    `INSTALL.sh` for the directory setup and proper ...flags... to supply the
    `cmake` command here:

    ```bash
    mkdir build
    cd build
    cmake ...flags... $CLIFSRC_DIR
    make clif-matcher
    make install
    ```

    Replace the cmake and make commands with these to use Ninja:

    ```bash
    cmake -G Ninja ...flags... $CLIFSRC_DIR
    ninja clif-matcher
    ninja -j 2 install
    ```

    If you have more than one Python version installed (eg. python3.6 and
    python3.7) cmake may have problems finding python libraries for the Python
    you specified as INSTALL.sh argument and uses the default Python instead. To
    help cmake use the correct Python add the following options to the cmake
    command (substitute the correct path for your system):

    ```bash
    cmake ... \
      -DPYTHON_INCLUDE_DIR="/usr/include/python3.6" \
      -DPYTHON_LIBRARY="/usr/lib/x86_64-linux-gnu/libpython3.6m.so" \
      -DPYTHON_EXECUTABLE="/usr/bin/python3.6" \
      "${CMAKE_G_FLAGS[@]}" "$CLIFSRC_DIR"
    ```

1.  Get back to your CLIF python checkout and install it using pip.

    ```bash
    cd "$CLIFSRC_DIR"
    cp "$BUILD_DIR/clif/protos/ast_pb2.py" clif/protos/
    cp "$BUILD_DIR/clif/python/utils/proto_util.cc" clif/python/utils/
    cp "$BUILD_DIR/clif/python/utils/proto_util_clif.h" clif/python/utils/
    cp "$BUILD_DIR/clif/python/utils/proto_util.init.cc" clif/python/utils/
    pip install .
    ```

That version is guaranteed to work. Older versions likely do not work (they lack
some APIs); later versions might work, at your own risk.

INSTALL.sh will build and install clif-matcher to CMake install directory and
CLIF for Python to the given Python (virtual) environment.

To run Python CLIF use `pyclif`.

## Using your newly built pyclif

First, try some examples:

```bash
cd examples
less README.md
```

Next, read the [Python CLIF User Manual](clif/python/README.md).

For more details please refer to:

1.  [CLIF Python Primer](clif/python/primer.md)
1.  [CLIF FAQ](clif/python/faq.md)

## Disclaimer

This is not an official Google product.
