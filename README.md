# C++ Language Interface Foundation (CLIF)

CLIF provides a common foundation for creating C++ wrapper generators for
various languages.

## Overview

It consists of four parts:

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
    Version 3.2.0 or later is required.
    Please install protobuf for both C++ and Python from source, as we will
    need some protobuf source code later on.

 1. You must have [virtualenv](https://pypi.python.org/pypi/virtualenv)
    installed.

 1. You must have Subversion installed, so we can fetch LLVM.

 1. You must have pyparsing installed, so we can build protobuf. Use
    `pip install 'pyparsing>=2.2.0'` to fetch the correct version.

 1. Make sure `pkg-config --libs python` works (e.g. install `python-dev` and
    `pkg-config`).

### Building

The steps below are in `INSTALL.sh` but outlined here for clarification.
The install script sets up a Python virtual environment where it installs CLIF.

1.  Checkout LLVM and Clang source trees (the exact SVN version as specified
    here is *required*)

    ```bash
    # We keep it separate of the CLIF tree to avoid pip unwanted copying.
    mkdir $LLVMSRC_DIR
    cd $LLVMSRC_DIR
    svn co https://llvm.org/svn/llvm-project/llvm/trunk@307315 llvm
    cd llvm/tools
    svn co https://llvm.org/svn/llvm-project/cfe/trunk@307315 clang
    ln -sf "$CLIFSRC_DIR/clif" clif
    ```

1.  Build and install the CLIF backend. If you use
    [Ninja](https://ninja-build.org/) instead of `make` your build will go
    significantly faster. It is used by Chromium, LLVM et al. Look at
    `INSTALL.sh` for the directory setup and proper ...flags... to supply the
    `cmake` command here:

    ```bash
    # Builds must be done outside of the LLVM tree.
    mkdir ../../build_matcher
    cd ../../build_matcher
    cmake ...flags... $LLVMSRC_DIR/llvm
    make clif-matcher
    make install
    ```

    Replace the cmake and make commands with these to use Ninja:

    ```bash
    cmake -G Ninja ...flags... $LLVMSRC_DIR/llvm
    ninja clif-matcher
    ninja -j 2 install
    ```

    If the clif-matcher build target is not found, check that you created the
    correct `llvm/tools/clif` symlink in the previous step. The CLIF backend
    builds as _part_ of an LLVM build.

    If you have more than one Python version installed (eg. python2.7 and
    python3.6) cmake may have problems finding python libraries for the Python
    you specified as INSTALL.sh argument and uses the default Python instead.
    To help cmake use the correct Python add the following options to the cmake
    command (substitute the correct path for your system):

    ```bash
    cmake ... \
      -DPYTHON_INCLUDE_DIR="/usr/include/python3.6" \
      -DPYTHON_LIBRARY="/usr/lib/x86_64-linux-gnu/libpython3.6m.so" \
      -DPYTHON_EXECUTABLE="/usr/bin/python3.6" \
      "${CMAKE_G_FLAGS[@]}" "$LLVM_DIR/llvm"
    ```

    NOTE: INSTALL.sh builds only for X86. If you want to build for another
    architecture, modify it to specify your target architecture, or just remove
    this restriction (see NOTE in INSTALL.sh).

1.  Get back to your CLIF python checkout and install it using pip.

    ```bash
    cd "$CLIFSRC_DIR"
    cp "$BUILD_DIR/tools/clif/protos/ast_pb2.py" clif/protos/
    pip install .
    ```

That version is guaranteed to work. Older versions likely do not work (they lack
some APIs); later versions might work, at your own risk.

INSTALL.sh will build and install CLIF for Python (and LLVM Clang as an internal
tool) to your system by default in `$HOME/opt/clif` and `$HOME/opt/clif/clang`.

To run Python CLIF use `$HOME/opt/clif/bin/pyclif`.

## Using your newly built pyclif

First, try some examples:

```bash
cd ~/opt/clif/examples
less README.md
```

Next, read the [Python CLIF User Manual](clif/python/README.md).

For more details please refer to:

1.  [CLIF Python Primer](clif/python/primer.md)
1.  [CLIF FAQ](clif/python/faq.md)

## Disclaimer

This is not an official Google product.
