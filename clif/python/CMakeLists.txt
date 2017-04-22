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

# This CMake file will build the PyCLIF runtime along with the CLIF backend.

file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/__init__.py"
  "import pkgutil; __path__ = pkgutil.extend_path(__path__, __name__)"
)

add_library(pyClifRuntime SHARED
  optional.h
  optional.cc
  postconv.h
  ptr_util.h
  runtime.cc
  runtime.h
  shared_ptr.h
  slots.cc
  slots.h
  stltypes.h
  types.cc
  types.h
)

target_include_directories(pyClifRuntime PUBLIC
  "${LLVM_MAIN_SRC_DIR}/tools"
  "${PYTHON_INCLUDE_DIRS}"
)

target_link_libraries(pyClifRuntime PUBLIC
  "${PYTHON_LIBRARIES}"
)

add_custom_target(runPyClifUnitTests
  COMMAND
    "PYTHONPATH=${LLVM_TOOLS_DIR}" "CLIF_DIR=${LLVM_TOOLS_DIR}" ${PYTHON_EXECUTABLE} -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR} -p "*_test.py"
  WORKING_DIRECTORY ${LLVM_TOOLS_BIN_DIR}
  DEPENDS clifAstProto
)
