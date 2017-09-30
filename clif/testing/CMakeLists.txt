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

file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/__init__.py" "")

# Do not add build targets for header only libraries.

add_clif_test_cc_library(t2
  t2.h
  t2.cc
)

add_proto_library(clif_testing_nested_proto nested.proto)
add_pyclif_proto_library(clif_testing_nested_proto_wrapper
  nested.proto
  clif_testing_nested_proto
)

add_clif_test_cc_library(t4
  t4.h
  t4.cc
)
target_link_libraries(clif_testing_t4 clif_testing_nested_proto)

add_subdirectory("python")
