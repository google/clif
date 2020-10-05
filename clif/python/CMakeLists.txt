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

# This CMake file will build the PyCLIF runtime along with the CLIF backend.

include(GoogleTest)

file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/__init__.py"
  "import pkgutil; __path__ = pkgutil.extend_path(__path__, __name__)"
)

add_protobuf_include_directories()
add_protobuf_library_directories()

add_library(pyClifRuntime SHARED
  postconv.h
  pyproto.h
  pyproto.cc
  runtime.cc
  runtime.h
  instance.h
  slots.cc
  slots.h
  stltypes.h
  types.cc
  types.h
)

target_include_directories(pyClifRuntime PUBLIC
  "${CLIF_SRC_DIR}"
  "${PYTHON_INCLUDE_DIRS}"
  "${GOOGLE_GLOG_INCLUDE_DIRS}"
)

add_target_protobuf_link_libraries(pyClifRuntime)
target_link_libraries(pyClifRuntime PRIVATE
  "${PYTHON_LIBRARIES}"
  "${GOOGLE_GLOG_LIBRARIES}"

  absl::memory
  absl::optional
)

add_custom_target(runPyClifUnitTests
  COMMAND
    "PYTHONPATH=${CLIF_SRC_DIR}" "CLIF_DIR=${CLIF_SRC_DIR}" ${PYTHON_EXECUTABLE} -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR} -p "*_test.py"
  WORKING_DIRECTORY ${CLIF_BIN_DIR}
  DEPENDS clifAstProto
)

add_library(proto_util_cc STATIC
  proto_util.h
  proto_util.cc
)

target_include_directories(proto_util_cc
  PUBLIC
  ${CLIF_SRC_DIR}
  ${CLIF_BIN_DIR}
  ${PYTHON_INCLUDE_DIRS}
)

target_link_libraries(proto_util_cc PRIVATE
  pyClifRuntime
  ${PYTHON_LIBRARIES}
)
add_target_protobuf_link_libraries(proto_util_cc)

add_py_library(type_customization type_customization.py)
add_py_library(postproc postproc.py)

add_subdirectory(utils)

function(add_clif_python_unittest name cc_file)
  clif_target_name(${name} test_target_name)

  add_executable(${test_target_name} ${cc_file})
  add_dependencies(${test_target_name}
    pyClifRuntime
  )
  target_link_libraries(${test_target_name} PRIVATE
    pyClifRuntime
    ${PYTHON_LIBRARIES}

    gtest
    gtest_main
    pthread
  )
  add_target_protobuf_link_libraries(${test_target_name})

  gtest_discover_tests(${test_target_name})
endfunction(add_clif_python_unittest)

add_clif_python_unittest(instance_test instance_test.cc)

add_clif_python_unittest(postconv_test postconv_test.cc)

add_clif_python_unittest(pyobj_test pyobj_test.cc)
