licenses(["restricted"])

package(default_visibility = ["//visibility:public"])

# cc rule for LLVM builtin headers is not yet available in llvm-bazel
# since cc_embed_data is not yet supported
# (https://github.com/bazelbuild/rules_cc/issues/41).
cc_library(
    name = "llvm-headers",
    hdrs = ["@llvm-project//clang:builtin_headers_gen"],
    strip_include_prefix = "/clang/staging/include",
)
