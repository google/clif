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
cmake_minimum_required(VERSION 3.5)

# We need the Python libraries for generating PyCLIF wrappers.
find_package(PythonInterp REQUIRED)
find_package(PythonLibs REQUIRED)

# Path to the "pyclif" binary should either be passed as -DPYCLIF= argument to
# cmake, or should be in the path.
if(NOT PYCLIF)
  find_program(PYCLIF pyclif)
  if(NOT PYCLIF)
    message(FATAL_ERROR "The 'pyclif' program was not found. Specify with -DPYCLIF.")
  endif(NOT PYCLIF)
endif(NOT PYCLIF)
string(REGEX REPLACE "/bin/pyclif$" "" CLIF_INSTALL_DIR ${PYCLIF})

set(CLIF_EXAMPLES_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR})
set(CLIF_EXAMPLES_BINARY_DIR ${CMAKE_CURRENT_BINARY_DIR})

# Function to set up rules to invoke pyclif on a .clif file and generate
# the wrapper .cc, and .h files.
#
# Usage:
#   add_pyclif_library(
#     name
#     pyclif_file
#     # This a list of all cc libraries to which the wrapped constructs belong.
#     [CC_DEPS name1 [name2...]]
#     [CLIF_DEPS name1 [name2...]] # List of other pyclif_library deps.
#     [CXX_FLAGS flag1 [flag2...]]  # Compile flags to be passed to clif-matcher
#   )
function(add_pyclif_library name pyclif_file)
  cmake_parse_arguments(PYCLIF_LIBRARY "" "" "CC_DEPS;CLIF_DEPS;CXX_FLAGS" ${ARGN})

  string(REPLACE ".clif" "" pyclif_file_basename ${pyclif_file})
  set(gen_cc "${CMAKE_CURRENT_BINARY_DIR}/${pyclif_file_basename}.cc")
  set(gen_h "${CMAKE_CURRENT_BINARY_DIR}/${pyclif_file_basename}.h")
  set(gen_init "${CMAKE_CURRENT_BINARY_DIR}/${pyclif_file_basename}_init.cc")

  string(REPLACE "-" "_" module_name ${pyclif_file_basename})

  add_custom_target(
    ${name}
    BYPRODUCTS ${gen_cc} ${gen_h} ${gen_init}
    COMMAND
      ${PYCLIF}
      # If this is not run in a virtualenv after INSTALL.sh, then the following
      # two lines should be uncommented to point to the correct types.h and
      # the matcher binary.
      # -p${CLIF_INSTALL_DIR}/python/types.h
      # --matcher_bin=${CLIF_INSTALL_DIR}/clang/bin/clif-matcher
      -c${gen_cc} -g${gen_h} -i${gen_init}
      # Specify the path to the generated files.
      -I${CLIF_EXAMPLES_BINARY_DIR}/../..
      --modname=${module_name}
      "-f-I${PYTHON_INCLUDE_DIRS} -I${CLIF_INSTALL_DIR}/.. -I${CLIF_EXAMPLES_SOURCE_DIR}/../.. -I${CLIF_EXAMPLES_BINARY_DIR}/../.. -std=c++11 ${PYCLIF_LIBRARY_CXX_FLAGS}"
      ${CMAKE_CURRENT_SOURCE_DIR}/${pyclif_file}
    VERBATIM
    DEPENDS ${PYCLIF_LIBRARY_CC_DEPS} ${PYCLIF_LIBRARY_CLIF_DEPS}
  )
endfunction(add_pyclif_library)

# Add path to the root "clif" directory to the include path.
include_directories(${CLIF_EXAMPLES_SOURCE_DIR}/../..)

add_subdirectory("callbacks")
add_subdirectory("inheritance")
add_subdirectory("property")
add_subdirectory("templates")
add_subdirectory("wrapfunc")
add_subdirectory("wrapmethod")
add_subdirectory("wrappod")
