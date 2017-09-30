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

# CLIF requires the protocol buffer runtime library and compiler. See this
# github link on how to download and install them for C++:
#
#   https://github.com/google/protobuf.
#
# Once installed, the paths to protocol buffer runtime directories are
# discovered using the pkg-config utility via the FindPkgConfig cmake module.
# The minimum version of protocol buffers which supports pkg-config is 2.2.0.
#
# If the protobuf runtime is installed in a non-standard prefix directory, then
# one should specify the prefix directory with
# -DCMAKE_PREFIX_PATH=<non-standard prefix path to protobuf installation>.
# Specifying this option will also help the find_program command to look up
# the protoc compiler binary in the non-standard location.
include(FindPkgConfig)
# Lookup include and library directories using pkg-config.
pkg_check_modules(GOOGLE_PROTOBUF REQUIRED protobuf)

function(add_protobuf_include_directories)
  if(GOOGLE_PROTOBUF_INCLUDE_DIRS)
    include_directories(${GOOGLE_PROTOBUF_INCLUDE_DIRS})
  endif(GOOGLE_PROTOBUF_INCLUDE_DIRS)
endfunction(add_protobuf_include_directories)

function(add_target_protobuf_include_directories target)
  if(GOOGLE_PROTOBUF_INCLUDE_DIRS)
    target_include_directories(${target} PUBLIC ${GOOGLE_PROTOBUF_INCLUDE_DIRS})
  endif(GOOGLE_PROTOBUF_INCLUDE_DIRS)
endfunction(add_target_protobuf_include_directories target)

function(add_protobuf_library_directories)
  if(GOOGLE_PROTOBUF_LIBRARY_DIRS)
    link_directories(${GOOGLE_PROTOBUF_LIBRARY_DIRS})
  endif(GOOGLE_PROTOBUF_LIBRARY_DIRS)
endfunction(add_protobuf_library_directories)

function(add_target_protobuf_link_libraries target)
  if(GOOGLE_PROTOBUF_LIBRARIES)
    target_link_libraries(${target} ${GOOGLE_PROTOBUF_LIBRARIES})
  endif(GOOGLE_PROTOBUF_LIBRARIES)
endfunction(add_target_protobuf_link_libraries target)

include(CMakeParseArguments)

# A convenience function to generate unique target names.
# If this function is invoked from a CMakeLists.txt file in directory
# "path/to/target" as:
#
#   clif_target_name(my_target full_target_name)
#
# Then, a variable with name "full_target_name" will be inserted into the
# callers scope and will have a value "path_to_target_my_target".
function(clif_target_name name target_var)
  string(REPLACE "${LLVM_TOOLS_DIR}/" "" relative_path ${CMAKE_CURRENT_SOURCE_DIR})
  string(REPLACE "/" "_" target_prefix ${relative_path})
  set(${target_var} "${target_prefix}_${name}" PARENT_SCOPE)
endfunction(clif_target_name name)

function(clif_extension_module_name name name_var)
  string(REPLACE "${LLVM_TOOLS_DIR}/" "" relative_path ${CMAKE_CURRENT_SOURCE_DIR})
  string(REPLACE "/" "." path_prefix ${relative_path})
  string(REPLACE "-" "_" ${path_prefix} ${path_prefix})
  string(REPLACE "-" "_" clean_name ${name})
  set(${name_var} "${path_prefix}.${clean_name}" PARENT_SCOPE)
endfunction(clif_extension_module_name name_var)

# The pkg_check_modules function does not set any vars pointing to the protobuf
# compiler binary "protoc". Hence, look it up explicitly.
#
# The find_program command can lookup the "protoc" binary if it is in CMake's
# lookup path. If protobuf package is installed at a non-standard location, then
# specifying this location with -DCMAKE_PREFIX_PATH will add the non-standard
# location to CMake's lookup paths (and hence find_program can find "protoc"
# and also works for include path).
find_program(PROTOC "protoc")
if(PROTOC-NOTFOUND)
  message(FATAL_ERROR "The protobuf compiler 'protoc' not found.")
endif(PROTOC-NOTFOUND)

function(add_proto_library name proto_srcfile)
  string(REPLACE ".proto" ".pb.cc" gen_cc "${proto_srcfile}")
  string(REPLACE ".proto" ".pb.h" gen_h "${proto_srcfile}")
  string(REPLACE ".proto" "_pb2.py" gen_pb2 "${proto_srcfile}")

  add_custom_command(
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${gen_cc}
           ${CMAKE_CURRENT_BINARY_DIR}/${gen_h}
           ${CMAKE_CURRENT_BINARY_DIR}/${gen_pb2}
    COMMAND ${PROTOC}
            -I${CMAKE_CURRENT_SOURCE_DIR}
            ${CMAKE_CURRENT_SOURCE_DIR}/${proto_srcfile}
            --cpp_out=${CMAKE_CURRENT_BINARY_DIR}
            --python_out=${CMAKE_CURRENT_BINARY_DIR}
  )

  add_library(${name}
    ${CMAKE_CURRENT_BINARY_DIR}/${gen_cc}
    ${CMAKE_CURRENT_BINARY_DIR}/${gen_h}
  )

  target_include_directories(${name} PUBLIC "${GOOGLE_PROTOBUF_INCLUDE_DIRS}")
endfunction(add_proto_library)

# We need the Python libraries for building the CLIF runtime and the CLIF
# generated wrappers.
find_package(PythonLibs REQUIRED)
find_package(PythonInterp REQUIRED)

# Use this convenience function for creating test cc libraries as we want them
# to be built with custom properties. If the current source directory is
# current/source/dir, then the name of the added target is
# current_source_dir_${name}.
function(add_clif_test_cc_library name)
  clif_target_name(${name} lib_target_name)

  add_library(${lib_target_name}
    EXCLUDE_FROM_ALL
    # If a library does not have any CC files, then better not add a target for
    # it!
    ${ARGN}
  )

  target_include_directories(${lib_target_name}
    PRIVATE
      ${LLVM_TOOLS_DIR}
      ${LLVM_TOOLS_BIN_DIR}
  )

  set_target_properties(${lib_target_name}
    PROPERTIES
      LIBRARY_OUTPUT_NAME ${name}
      LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
  )
endfunction(add_clif_test_cc_library)

set(PYCLIF_CC_LIBRARY_PREFIX "py_clif_cc_")

# Function to set up rules to invoke pyclif on a .clif file and build
# the .so from the generated code. If the current source directory is
# current/source/dir, then the name of the added target is
# current_source_dir_${name}.
#
# Usage:
#   add_pyclif_library(
#     NAME
#     PYCLIF_FILE
#     # This a list of all cc libraries to which the wrapped constructs belong.
#     [CC_DEPS name1 [name2...]]
#     [CLIF_DEPS name1 [name2...]]  # List of other pyclif_library deps.
#     [CXX_FLAGS flag1 [flag2...]]  # Compile flags to be passed to clif-matcher
#     [PROTO_DEPS target1 [target2...]]  # List of pyclif_proto_library deps.
#   )
function(add_pyclif_library name pyclif_file)
  cmake_parse_arguments(PYCLIF_LIBRARY "" "" "CC_DEPS;CLIF_DEPS;CXX_FLAGS;PROTO_DEPS" ${ARGN})

  string(REPLACE ".clif" "" pyclif_file_basename ${pyclif_file})
  set(gen_cc "${CMAKE_CURRENT_BINARY_DIR}/${pyclif_file_basename}.cc")
  set(gen_h "${CMAKE_CURRENT_BINARY_DIR}/${pyclif_file_basename}.h")
  set(gen_init "${CMAKE_CURRENT_BINARY_DIR}/${pyclif_file_basename}.init.cc")

  clif_extension_module_name(${name} module_name)

  if (GOOGLE_PROTOBUF_INCLUDE_DIRS)
    set(GOOGLE_PROTOBUF_CXX_FLAGS "-I${GOOGLE_PROTOBUF_INCLUDE_DIRS}")
  endif(GOOGLE_PROTOBUF_INCLUDE_DIRS)

  add_custom_command(
    OUTPUT ${gen_cc} ${gen_h} ${gen_init}
    COMMAND
      # List LLVM_TOOLS_BIN_DIR before LLVM_TOOLS_DIR in PYTHONPATH as we
      # want to first load the __init__.py in LLVM_TOOLS_BIN_DIR.
      "PYTHONPATH=${LLVM_TOOLS_BIN_DIR}:${LLVM_TOOLS_DIR}" ${PYTHON_EXECUTABLE} ${PYCLIF}
      -p${CLIF_PYTHON_DIR}/types.h -c${gen_cc} -g${gen_h} -i${gen_init}
      -I${LLVM_TOOLS_DIR} -I${LLVM_TOOLS_BIN_DIR}
      --modname=${module_name}
      --matcher_bin=${CLIF_MATCHER}
      "-f-I${PYTHON_INCLUDE_DIRS} -I${LLVM_TOOLS_DIR} -I${LLVM_TOOLS_BIN_DIR} ${GOOGLE_PROTOBUF_CXX_FLAGS} -std=c++11 ${PYCLIF_LIBRARY_CXX_FLAGS}"
      ${CMAKE_CURRENT_SOURCE_DIR}/${pyclif_file}
    VERBATIM
    # This step invokes the clif-matcher. Hence, we need it to be built before
    # we can invoke it.
    DEPENDS clif-matcher ${PYCLIF_LIBRARY_CLIF_DEPS} ${PYCLIF_LIBRARY_PROTO_DEPS}
  )

  clif_target_name(${name} lib_target_name)

  add_protobuf_library_directories()

  add_library(${lib_target_name} SHARED
    EXCLUDE_FROM_ALL
    ${gen_cc}
    ${gen_h}
    ${gen_init}
  )

  set_target_properties(${lib_target_name}
    PROPERTIES
      LIBRARY_OUTPUT_NAME ${name}
      LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
      # We do not want any prefix like "lib" to be added to the library file.
      PREFIX ""
  )

  add_target_protobuf_include_directories(${lib_target_name})
  target_include_directories(${lib_target_name}
    PRIVATE
      ${LLVM_TOOLS_DIR}
      ${LLVM_TOOLS_BIN_DIR}
      ${PYTHON_INCLUDE_DIRS}
  )

  add_target_protobuf_link_libraries(${lib_target_name})
  target_link_libraries(${lib_target_name}
    ${PYCLIF_LIBRARY_CC_DEPS}
    ${PYCLIF_LIBRARY_CLIF_DEPS}
    ${PYCLIF_LIBRARY_PROTO_DEPS}
    pyClifRuntime
    ${PYTHON_LIBRARIES}
  )
endfunction(add_pyclif_library)

function(add_pyclif_proto_library name proto_file proto_lib)
  string(REPLACE ".proto" "" proto_file_basename ${proto_file})
  set(gen_cc "${CMAKE_CURRENT_BINARY_DIR}/${proto_file_basename}_pyclif.cc")
  set(gen_h "${CMAKE_CURRENT_BINARY_DIR}/${proto_file_basename}_pyclif.h")

  add_custom_target(${name}_pyclif
    COMMAND
      "PYTHONPATH=${LLVM_TOOLS_BIN_DIR}:${LLVM_TOOLS_DIR}" ${PYTHON_EXECUTABLE} ${PYCLIF_PROTO}
      "${CMAKE_CURRENT_SOURCE_DIR}/${proto_file}"
      -c ${gen_cc} -h ${gen_h}
      -s ${LLVM_TOOLS_DIR}
      -d ${LLVM_TOOLS_BIN_DIR}
    BYPRODUCTS ${gen_cc} ${gen_h}
    VERBATIM
    DEPENDS clif_python_utils_proto_util
  )

  add_library(${name} STATIC
    EXCLUDE_FROM_ALL
    ${gen_cc}
    ${gen_h}
  )

  target_include_directories(${name}
    PRIVATE
      ${LLVM_TOOLS_DIR}
      ${LLVM_TOOLS_BIN_DIR}
      ${PYTHON_INCLUDE_DIRS}
  )

  target_link_libraries(${name}
    clif_python_utils_proto_util
    pyClifRuntime
    ${proto_lib}
    ${PYTHON_LIBRARIES}
  )
endfunction(add_pyclif_proto_library name proto_file)

function(add_pyclif_library_and_test name)
  add_pyclif_library(${name}
    ${ARGN}
  )

  clif_target_name(${name} lib_target_name)

  add_custom_target("${lib_target_name}_test"
    COMMAND "PYTHONPATH=${LLVM_TOOLS_BIN_DIR}" ${PYTHON_EXECUTABLE} -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR} -p "${name}_test.py"
    WORKING_DIRECTORY ${LLVM_TOOLS_BIN_DIR}
    DEPENDS ${lib_target_name}
  )
endfunction(add_pyclif_library_and_test)
