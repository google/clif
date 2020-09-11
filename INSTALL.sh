#!/bin/bash
#
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Install CLIF primer script.

set -x -e

INSTALL_DIR=${INSTALL_DIR:="$HOME/opt"}
CLIFSRC_DIR="$PWD"
LLVM_DIR="$CLIFSRC_DIR/../clif_backend"
BUILD_DIR="$LLVM_DIR/build_matcher"

# Ensure CMake is installed (needs 3.5+)

CV=$(cmake --version | head -1 | cut -f3 -d\ ); CV=(${CV//./ })
if (( CV[0] < 3 || CV[0] == 3 && CV[1] < 5 )); then
  echo "Install CMake version 3.5+"
  exit 1
fi

# Ensure Google protobuf C++ source is installed (needs v3.2+).

PV=$(protoc --version | cut -f2 -d\ ); PV=(${PV//./ })
if (( PV[0] < 3 || PV[0] == 3 && PV[1] < 2 )); then
  echo "Install Google protobuf version 3.2+"
  exit 1
fi
PROTOC_PREFIX_PATH="$(dirname "$(dirname "$(which protoc)")")"

# If Ninja is installed, use it instead of make.  MUCH faster.

declare -a CMAKE_G_FLAG
declare -a MAKE_PARALLELISM
if which ninja; then
  CMAKE_G_FLAGS=(-G Ninja)
  MAKE_OR_NINJA="ninja"
  MAKE_PARALLELISM=()  # Ninja does this on its own.
  # ninja can run a dozen huge ld processes at once during install without
  # this flag... grinding a 12 core workstation with "only" 32GiB to a halt.
  # linking and installing should be I/O bound anyways.
  MAKE_INSTALL_PARALLELISM=(-j 2)
  echo "Using ninja for the clif backend build."
else
  CMAKE_G_FLAGS=()  # The default generates a Makefile.
  MAKE_OR_NINJA="make"
  MAKE_PARALLELISM=(-j 2)
  if [[ -r /proc/cpuinfo ]]; then
    N_CPUS="$(cat /proc/cpuinfo | grep -c ^processor)"
    [[ "$N_CPUS" -gt 0 ]] && MAKE_PARALLELISM=(-j $N_CPUS)
    MAKE_INSTALL_PARALLELISM=(${MAKE_PARALLELISM[@]})
  fi
  echo "Using make.  Build will take a long time.  Consider installing ninja."
fi

# Determine the Python to use.

if [[ "$1" =~ ^-?-h ]]; then
  echo "Usage: $0 [python interpreter]"
  exit 1
fi
if [[ -n "$1" ]]; then
  PYTHON="$1"
else
  PYTHON=$(which python)
fi
echo -n "Using Python interpreter: $PYTHON"

# Determine if clif is installed in verbose mode. Users could invoke the verbose
# mode by:
#   CLIF_VERBOSE=1 ./INSTALL.sh
if [[ "$CLIF_VERBOSE" -eq 1 ]]; then
  MAKE_VERBOSE="VERBOSE=1"
  PIP_VERBOSE="-v"
fi

# Create a virtual environment for the pyclif installation.

CLIF_VIRTUALENV="$INSTALL_DIR"/clif
CLIF_PIP="$CLIF_VIRTUALENV/bin/pip"
virtualenv -p "$PYTHON" "$CLIF_VIRTUALENV"
# Older pip and setuptools can fail.
# TODO: These work the first time but run into errors if rerun? ugh.
# Regardless, *necessary* on systems with older pip and setuptools.  comment
# these out if they cause you trouble.  if the final pip install fails, you
# may need a more recent pip and setuptools.
"$CLIF_PIP" install --upgrade pip
"$CLIF_PIP" install --upgrade setuptools

# Download, build and install LLVM and Clang (needs a specific revision).

mkdir -p "$LLVM_DIR"
cd "$LLVM_DIR"
svn co https://llvm.org/svn/llvm-project/llvm/trunk@321388 llvm
cd llvm/projects
if [[ $(uname) == "Darwin" ]]; then
  # Build and use libc++ on macOS.
  svn co https://llvm.org/svn/llvm-project/libcxx/trunk@321388 libcxx
fi
cd ../tools
svn co https://llvm.org/svn/llvm-project/cfe/trunk@321388 clang
ln -s -f -n "$CLIFSRC_DIR/clif" clif

# Build and install the CLIF backend.  Our backend is part of the llvm build.
# NOTE: To speed up, we build only for X86. If you need it for a different
# arch, change it to your arch, or just remove the =X86 line below.

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"
cmake -DCMAKE_INSTALL_PREFIX="$CLIF_VIRTUALENV/clang" \
      -DCMAKE_PREFIX_PATH="$PROTOC_PREFIX_PATH" \
      -DLLVM_INSTALL_TOOLCHAIN_ONLY=true \
      -DCMAKE_BUILD_TYPE=Release \
      -DLLVM_BUILD_DOCS=false \
      -DLLVM_TARGETS_TO_BUILD=X86 \
      -DPYTHON_EXECUTABLE="$PYTHON" \
      "${CMAKE_G_FLAGS[@]}" "$LLVM_DIR/llvm"
# No quotes since MAKE_VERBOSE may be an empty string for non-verbose mode.
"$MAKE_OR_NINJA" $MAKE_VERBOSE "${MAKE_PARALLELISM[@]}" clif-matcher clif_python_utils_proto_util
"$MAKE_OR_NINJA" $MAKE_VERBOSE "${MAKE_INSTALL_PARALLELISM[@]}" install

# Get back to the CLIF Python directory and have pip run setup.py.

cd "$CLIFSRC_DIR"
# Grab the python compiled .proto
cp "$BUILD_DIR/tools/clif/protos/ast_pb2.py" clif/protos/
# Grab CLIF generated wrapper implementation for proto_util.
cp "$BUILD_DIR/tools/clif/python/utils/proto_util.cc" clif/python/utils/
cp "$BUILD_DIR/tools/clif/python/utils/proto_util.h" clif/python/utils/
cp "$BUILD_DIR/tools/clif/python/utils/proto_util.init.cc" clif/python/utils/
# No quotes since PIP_VERBOSE may be an empty string for non-verbose mode.
"$CLIF_PIP" $PIP_VERBOSE install .

echo "SUCCESS - To use pyclif, run $CLIF_VIRTUALENV/bin/pyclif."
