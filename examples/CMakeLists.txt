# Copyright 2017-2020 Google LLC
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
cmake_minimum_required(VERSION 3.10)

set(CMAKE_CXX_STANDARD 17)

# We need the Python libraries for generating PyCLIF wrappers.
find_package(PythonInterp REQUIRED)
find_package(PythonLibs REQUIRED)

include(FindPkgConfig)
# Lookup include and library directories using pkg-config.
pkg_check_modules(GOOGLE_PROTOBUF REQUIRED protobuf)

find_program(PROTOC "protoc")
if(PROTOC-NOTFOUND)
  message(FATAL_ERROR "The protobuf compiler 'protoc' not found.")
endif(PROTOC-NOTFOUND)

# Path to the "pyclif" binary should either be passed as -DPYCLIF= argument to
# cmake, or should be in the path.
if(NOT PYCLIF)
  find_program(PYCLIF pyclif)
  if(NOT PYCLIF)
    message(FATAL_ERROR "The 'pyclif' program was not found. Specify with -DPYCLIF.")
  endif(NOT PYCLIF)
endif(NOT PYCLIF)
string(REGEX REPLACE "/bin/pyclif$" "" CLIF_INSTALL_DIR ${PYCLIF})

if(NOT PYCLIF_PROTO)
  find_program(PYCLIF_PROTO pyclif_proto)
  if(NOT PYCLIF_PROTO)
    message(FATAL_ERRPR "The 'pyclif_proto' program was not found. Specify with -DPYCLIF_PROTO.")
  endif(NOT PYCLIF_PROTO)
endif(NOT PYCLIF_PROTO)

execute_process(
    COMMAND ${PYTHON_EXECUTABLE} -c "import clif; print(clif.__path__[0])"
    OUTPUT_VARIABLE CLIF_INSTALL_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

set(CLIF_EXAMPLES_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR})
set(CLIF_EXAMPLES_BINARY_DIR ${CMAKE_CURRENT_BINARY_DIR})

function(clif_target_name name target_var)
  string(REPLACE "${CLIF_EXAMPLES_SOURCE_DIR}/" "" relative_path ${CMAKE_CURRENT_SOURCE_DIR})
  string(REPLACE "/" "_" target_prefix ${relative_path})
  set(${target_var} "${target_prefix}_${name}" PARENT_SCOPE)
endfunction(clif_target_name name)

function(clif_extension_module_name name name_var)
  string(REPLACE "${CLIF_EXAMPLES_SOURCE_DIR}/" "" relative_path ${CMAKE_CURRENT_SOURCE_DIR})
  string(REPLACE "/" "." path_prefix ${relative_path})
  string(REPLACE "-" "_" ${path_prefix} ${path_prefix})
  string(REPLACE "-" "_" clean_name ${name})
  set(${name_var} "${path_prefix}.${clean_name}" PARENT_SCOPE)
endfunction(clif_extension_module_name name_var)

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
  cmake_parse_arguments(PYCLIF_LIBRARY "" "" "CC_DEPS;CLIF_DEPS;PROTO_DEPS;CXX_FLAGS" ${ARGN})

  string(REPLACE ".clif" "" pyclif_file_basename ${pyclif_file})
  set(gen_cc "${CMAKE_CURRENT_BINARY_DIR}/${pyclif_file_basename}.cc")
  set(gen_h "${CMAKE_CURRENT_BINARY_DIR}/${pyclif_file_basename}_clif.h")
  set(gen_init "${CMAKE_CURRENT_BINARY_DIR}/${pyclif_file_basename}_init.cc")

  clif_extension_module_name(${pyclif_file_basename} module_name)
  clif_target_name(${pyclif_file_basename} target_name)

  if (GOOGLE_PROTOBUF_INCLUDE_DIRS)
    set(GOOGLE_PROTOBUF_CXX_FLAGS "-I${GOOGLE_PROTOBUF_INCLUDE_DIRS}")
  endif(GOOGLE_PROTOBUF_INCLUDE_DIRS)

  add_custom_target(
    ${target_name}
    ALL
    BYPRODUCTS ${gen_cc} ${gen_h} ${gen_init}
    COMMAND
      ${PYCLIF}
      # If this is not run in a virtualenv after INSTALL.sh, then the following
      # two lines should be uncommented to point to the correct types.h and
      # the matcher binary.
      -p${CLIF_INSTALL_DIR}/python/types.h
      --matcher_bin=${CMAKE_INSTALL_PREFIX}/bin/clif-matcher
      -c${gen_cc} -g${gen_h} -i${gen_init}
      # Specify the path to the generated files.
      -I${CLIF_EXAMPLES_BINARY_DIR}
      --modname=${module_name}
      "-f-I${PYTHON_INCLUDE_DIRS} -I${CLIF_INSTALL_DIR}/.. -I${CLIF_EXAMPLES_SOURCE_DIR} -I${CLIF_EXAMPLES_BINARY_DIR} ${GOOGLE_PROTOBUF_CXX_FLAGS} -std=c++17 ${PYCLIF_LIBRARY_CXX_FLAGS}"
      ${CMAKE_CURRENT_SOURCE_DIR}/${pyclif_file}
    VERBATIM
    DEPENDS ${PYCLIF_LIBRARY_CC_DEPS} ${PYCLIF_LIBRARY_CLIF_DEPS} ${PYCLIF_LIBRARY_PROTO_DEPS}
  )
endfunction(add_pyclif_library)

function(add_proto_library name proto_srcfile)
  string(REPLACE ".proto" ".pb.cc" gen_cc "${proto_srcfile}")
  string(REPLACE ".proto" ".pb.h" gen_h "${proto_srcfile}")
  string(REPLACE ".proto" "_pb2.py" gen_pb2 "${proto_srcfile}")

  add_custom_target(
    ${name}
    BYPRODUCTS
           ${CMAKE_CURRENT_BINARY_DIR}/${gen_cc}
           ${CMAKE_CURRENT_BINARY_DIR}/${gen_h}
           ${CMAKE_CURRENT_BINARY_DIR}/${gen_pb2}
    COMMAND
      ${PROTOC}
      -I${CMAKE_CURRENT_SOURCE_DIR}
      ${CMAKE_CURRENT_SOURCE_DIR}/${proto_srcfile}
      --cpp_out=${CMAKE_CURRENT_BINARY_DIR}
      --python_out=${CMAKE_CURRENT_BINARY_DIR}
  )
endfunction(add_proto_library)

function(add_pyclif_proto_library name proto_file proto_lib)
  string(REPLACE ".proto" "" proto_file_basename ${proto_file})
  set(gen_cc "${CMAKE_CURRENT_BINARY_DIR}/${proto_file_basename}_pyclif.cc")
  set(gen_h "${CMAKE_CURRENT_BINARY_DIR}/${proto_file_basename}_pyclif.h")

  string(REPLACE "${CLIF_EXAMPLES_SOURCE_DIR}/" "" proto_file_relative_path ${proto_file})

  add_custom_target(
    ${name}
    BYPRODUCTS ${gen_cc} ${gen_h}
    COMMAND
      ${PYCLIF_PROTO}
      -s ${CLIF_EXAMPLES_SOURCE_DIR}
      -d ${CLIF_EXAMPLES_BINARY_DIR}
      -c ${gen_cc}
      -h ${gen_h}
      ${proto_file_relative_path}
    VERBATIM
    DEPENDS ${proto_lib}
  )
endfunction(add_pyclif_proto_library)

# Add path to the root "clif" directory to the include path.
include_directories(${CLIF_EXAMPLES_SOURCE_DIR}/../..)

add_subdirectory("callbacks")
add_subdirectory("clif_aux")
add_subdirectory("extend_from_clifaux")
add_subdirectory("extend_from_python")
add_subdirectory("inheritance")
add_subdirectory("property")
add_subdirectory("templates")
add_subdirectory("unique_ptr_member")
add_subdirectory("wrap_protos")
add_subdirectory("wrapfunc")
add_subdirectory("wrapmethod")
add_subdirectory("wrappod")
