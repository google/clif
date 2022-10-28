package(
    default_visibility = ["//clif:__subpackages__"],
)

licenses(["notice"])

exports_files([
    "another_file.h",
    "test.h",
    "test_clif_aux.h",
    "test_subdir/test_clif_aux.h",
    "versioned_smart_ptr_test.h",
])

cc_binary(
    name = "clif_matcher",
    srcs = ["matcher_main.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":matcher",
        "//clif/protos:ast_cc_proto",
        "@llvm-project//llvm:Support",
    ],
)

cc_library(
    name = "ast",
    srcs = [
        "ast.cc",
    ],
    hdrs = [
        "ast.h",
    ],
    deps = [
        ":strutil",
        "@com_google_absl//absl/strings",
        "@com_google_googletest//:gtest_prod",
        "@llvm-project//clang:ast",
        "@llvm-project//clang:ast_matchers",
        "@llvm-project//clang:basic",
        "@llvm-project//clang:frontend",
        "@llvm-project//clang:sema",
        "@llvm-project//clang:tooling",
        "@llvm-project//llvm:Support",
    ],
)

cc_library(
    name = "matcher",
    srcs = [
        "code_builder.cc",
        "matcher.cc",
    ],
    hdrs = [
        "code_builder.h",
        "matcher.h",
    ],
    deps = [
        ":ast",
        ":strutil",
        "//clif/protos:ast_cc_proto",
        "@com_google_absl//absl/container:btree",
        "@com_google_googletest//:gtest_prod",
        "@llvm-project//clang:ast",
        "@llvm-project//clang:sema",
        "@llvm-project//llvm:Support",
    ],
)

cc_library(
    name = "strutil",
    hdrs = ["strutil.h"],
    deps = [
        "@llvm-project//llvm:Support",
    ],
)

# This tests the interface between clang and the matcher.
cc_test(
    name = "ast_test",
    srcs = [
        "ast_test.cc",
    ],
    # We need a C++ header file as input to the test and this is a
    # convenient one.
    data = [
        "test.h",
    ],
    defines = ["CLIF_BACKEND_SOURCE_DIR=\\\"clif/backend\\\""],
    deps = [
        ":ast",
        "//devtools/build/runtime:get_runfiles_dir",
        "@com_google_absl//absl/flags:flag",
        "@com_google_googletest//:gtest_main",
        "@llvm-project//clang:ast",
        "@llvm-project//clang:ast_matchers",
        "@llvm-project//clang:frontend",
        "@llvm-project//clang:tooling",
    ],
)

# This tests the matcher itself.
cc_test(
    name = "matcher_test",
    srcs = ["matcher_test.cc"],
    data = [
        # C++ header files which will be used as input to the tests.
        "test.h",
        "test_clif_aux.h",
        "test_subdir/test_clif_aux.h",
        "another_file.h",
        # versioned_smart_ptr_test.h test for match and set for versioned smart pointers.
        "versioned_smart_ptr_test.h",
    ],
    defines = ["CLIF_BACKEND_SOURCE_DIR=\\\"clif/backend\\\""],
    deps = [
        ":ast",
        ":matcher",
        ":strutil",
        "//clif/protos:ast_cc_proto",
        "//devtools/build/runtime:get_runfiles_dir",
        "//net/proto2/public:proto2",
        "@com_google_absl//absl/flags:flag",
        "@com_google_googletest//:gtest_main",
        "@llvm-project//llvm:Support",
    ],
)
