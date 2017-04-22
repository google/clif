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

include_directories(
  # Path to LLVM include directory
  "${LLVM_MAIN_SRC_DIR}/include"

  # Path to gtest directory
  "${LLVM_MAIN_SRC_DIR}/utils/unittest/googletest/include"

  # Path to Clang include directories
  "${LLVM_MAIN_SRC_DIR}/tools/clang/include"
  "${LLVM_BINARY_DIR}/tools/clang/include"

  # Add path to the clif directory. Since the "clif" directory does not follow
  # the layout conventions of other LLVM projects, we will have to add path to
  # the "tools" directory instead of to a "clif" or a "clif/include" directory.
  "${LLVM_MAIN_SRC_DIR}/tools"
  "${LLVM_BINARY_DIR}/tools"

  # Add path to protobuf libs
  "${GOOGLE_PROTOBUF_INCLUDE_DIRS}"
)

link_directories(
  "${GOOGLE_PROTOBUF_LIBRARY_DIRS}"
)

add_definitions(
  # Disable RTTI in the protobuf runtime library as the LLVM build
  # uses -fno-rtti
  -DGOOGLE_PROTOBUF_NO_RTTI
)

add_llvm_library(clifMatcher
  ast.cc
  matcher.cc
  code_builder.cc

  DEPENDS
  # CLIF proto
  clifAstProto

  # Clang libraries
  clangAST
  clangASTMatchers
  clangFrontend
  clangSema
  clangSerialization
  clangTooling
  clangToolingCore

  # LLVM Libraries
  LLVMSupport
)

add_llvm_executable(clif-matcher
  matcher_main.cc

  DEPENDS
  clifMatcher
  clifAstProto
  # We want the clang binary also to be available before we can start using
  # clif-matcher. Hence, let it depend on clang to avoid all confusions.
  # This way, the clang binaries will be built before clif-matcher is built.
  clang
)

set(CLIF_BACKEND_LINK_LIBRARIES
  # Clif library
  clifMatcher
  clifAstProto

  # Clang libraries
  clangAST
  clangASTMatchers
  clangFrontend
  clangSema
  clangSerialization
  clangTooling
  clangToolingCore

  # LLVM Libraries
  LLVMSupport

  # Protobuf runtime
  ${GOOGLE_PROTOBUF_LIBRARIES}
)

target_link_libraries(clif-matcher
  ${CLIF_BACKEND_LINK_LIBRARIES}
)

# The test suite target to be used with the function add_unittest.
# Building this one target will build all the individual unittest targets.
add_custom_target(clifBackendUnitTests)

function(add_clif_backend_unittest name cc_file)
  add_unittest(clifBackendUnitTests ${name}
    ${cc_file}
  )
  add_dependencies(${name}
    clifMatcher
  )
  # Set the path to source directory as the test data will picked from here.
  target_compile_options(${name}
    PRIVATE "-DCLIF_BACKEND_SOURCE_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}\""
  )
  target_link_libraries(${name}
    ${CLIF_BACKEND_LINK_LIBRARIES}
  )
endfunction(add_clif_backend_unittest)

add_clif_backend_unittest(clifMatcherUnitTest
  matcher_test.cc
)
add_clif_backend_unittest(clifAstUnitTest
  ast_test.cc
)

add_custom_target(runClifBackendUnitTests
  COMMAND
    $<TARGET_FILE:clifMatcherUnitTest>
  COMMAND
    $<TARGET_FILE:clifAstUnitTest>
  DEPENDS
    clifBackendUnitTests
)

install(TARGETS clif-matcher DESTINATION "bin")
