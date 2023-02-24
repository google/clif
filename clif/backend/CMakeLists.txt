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

include(GoogleTest)

include_directories(
  ${LLVM_INCLUDE_DIRS}
)

link_directories(
  ${LLVM_LIBRARY_DIR}
)

add_protobuf_include_directories()
add_protobuf_library_directories()

add_definitions(
  # Disable RTTI in the protobuf runtime library as the LLVM build
  # uses -fno-rtti
  -DGOOGLE_PROTOBUF_NO_RTTI
)

add_library(clifMatcher
  ast.cc
  matcher.cc
  code_builder.cc
)

add_dependencies(clifMatcher clifAstProto)

add_executable(clif-matcher
  matcher_main.cc
)

set(CLIF_BACKEND_LINK_LIBRARIES
  # Clif library
  clifMatcher
  clifAstProto

  utf8_validity

  absl::absl_check
  absl::absl_log
  absl::cord
  absl::flat_hash_map
  absl::flat_hash_set
  absl::strings

  # Clang libraries
  clang
  clangAST
  clangASTMatchers
  clangFrontend
  clangSema
  clangSerialization
  clangTooling

  # LLVM Libraries
  LLVM
)

target_link_libraries(clif-matcher PRIVATE
  ${CLIF_BACKEND_LINK_LIBRARIES}
)
add_target_protobuf_link_libraries(clif-matcher)

function(add_clif_backend_unittest name cc_file)
  clif_target_name(${name} test_target_name)

  add_executable(${test_target_name} ${cc_file})
  add_dependencies(${test_target_name}
    clifMatcher
  )
  # Set the path to source directory as the test data will picked from here.
  target_compile_options(${test_target_name}
    PRIVATE "-DCLIF_BACKEND_SOURCE_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}\""
  )
  target_link_libraries(${test_target_name} PRIVATE
    ${CLIF_BACKEND_LINK_LIBRARIES}

    gtest
    gtest_main
    pthread
  )
  add_target_protobuf_link_libraries(${test_target_name})

  gtest_discover_tests(${test_target_name})
endfunction(add_clif_backend_unittest)

add_clif_backend_unittest(matcher_test matcher_test.cc)

add_clif_backend_unittest(ast_test ast_test.cc)

install(TARGETS clif-matcher DESTINATION "bin")
