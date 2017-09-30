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

# This is the top-level CMakeLists.txt file to be used to build the CLIF backend
# binary "clif-matcher".
#
# The setup of CLIF's CMakeLists.txt files assume that clif-matcher will be
# built as part of an LLVM+Clang build. The source layout assumed is as follows:
#
# - llvm
#     - tools
#         - clang
#         - clif  # This can be a symlink to the clif source tree elsewhere.
#
# The "clif" directory represents the directory in which this file is present.
#
# Without the "clif" directory/symlink, this tree is similar to the LLVM+Clang
# source tree requirement. As with an LLVM+Clang build, one will have to build
# LLVM+Clang+CLIF in a build directory which is outside the root LLVM source
# directory. For example, after arranging the source tree as above, the steps
# to build LLVM+Clang+CLIF are as follows:
#
# $> mkdir llvm_build
# $> cd llvm_build
# $> cmake [-G Ninja] <path to the root LLVM source tree>
# $> make  # or ninja if -G Ninja was specified in the above step.
project(CLIF)

set(LLVM_TOOLS_DIR "${LLVM_MAIN_SRC_DIR}/tools")
set(LLVM_TOOLS_BIN_DIR "${LLVM_BINARY_DIR}/tools")
set(CLIF_PYTHON_DIR "${CMAKE_CURRENT_SOURCE_DIR}/python")

# Set the additional module path to the CLIF CMake utilities and load them.
set(CMAKE_MODULE_PATH
  "${CMAKE_MODULE_PATH}"
  "${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules"
)
include(CLIFUtils)

set(PYCLIF "${CMAKE_CURRENT_SOURCE_DIR}/pyclif.py")
set(PYCLIF_PROTO "${CMAKE_CURRENT_SOURCE_DIR}/python/proto.py")
set(CLIF_MATCHER "${LLVM_BINARY_DIR}/bin/clif-matcher")

file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/__init__.py"
  "import pkgutil; __path__ = pkgutil.extend_path(__path__, __name__)"
)

add_subdirectory("backend")
add_subdirectory("protos")
add_subdirectory("python")
add_subdirectory("testing")
