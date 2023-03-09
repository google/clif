load("@com_google_protobuf//:protobuf.bzl", "py_proto_library")

package(
    default_applicable_licenses = ["//third_party/clif:license"],
    default_visibility = ["//clif:__subpackages__"],
)

licenses(["notice"])

proto_library(
    name = "ast",
    srcs = ["ast.proto"],
)

cc_proto_library(
    name = "ast_cc_proto",
    deps = [":ast"],
)

py_proto_library(
    name = "ast_py_pb2",
    srcs = ["ast.proto"],
)
