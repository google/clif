# CLIF python frontend

load("@clif_python_deps//:requirements.bzl", "requirement")

package(
    default_visibility = ["//clif:__subpackages__"],
)

licenses(["notice"])

exports_files([
    # Every py_clif_cc needs that to scan for standard types.
    "stltypes.h",
    "types.h",
])

cc_library(
    name = "clif",
    srcs = [
        "instance.h",
        "pyproto.cc",
        "pyproto.h",
        "runtime.cc",
        "slots.cc",
        "types.cc",
    ],
    hdrs = [
        # Mostly #include'd in the CLIF-generated code.
        "postconv.h",
        "runtime.h",
        "slots.h",
        "stltypes.h",
        "types.h",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "@com_github_google_glog//:glog",
        "@com_google_absl//absl/base:config",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/numeric:int128",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:cord",
        "@com_google_absl//absl/types:optional",
        "@com_google_absl//absl/types:variant",
        "@com_google_protobuf//:proto_api",
        "@com_google_protobuf//:protobuf_headers",
        "@com_google_protobuf//:protobuf_lite",
        "@python_runtime//:python_headers",
    ],
)

cc_test(
    name = "pyobj_test",
    size = "small",
    srcs = [
        "pyobj.h",
        "pyobj_test.cc",
    ],
    deps = [
        ":instance",
        "@com_github_google_glog//:glog",
        "@com_google_googletest//:gtest_main",
        "@python_runtime//:python_headers",
        "@python_runtime//:python_lib",
    ],
)

cc_library(
    name = "instance",
    testonly = 1,
    hdrs = ["instance.h"],
)

cc_test(
    name = "instance_test",
    srcs = ["instance_test.cc"],
    deps = [
        ":instance",
        "@com_google_googletest//:gtest_main",
    ],
)

cc_library(
    name = "proto_util",
    srcs = ["proto_util.cc"],
    hdrs = ["proto_util.h"],
    visibility = [
        "//clif/python/clif:__pkg__",
    ],
    deps = [
        "@com_github_google_glog//:glog",
        "@com_google_protobuf//:protobuf",
        "@com_google_protobuf//:protobuf_headers",
    ],
)

py_library(
    name = "ast_manipulations_lib",
    srcs = ["ast_manipulations.py"],
    srcs_version = "PY2AND3",
    deps = ["//clif/protos:ast_py_pb2"],
)

py_library(
    name = "generator_lib",
    srcs = [
        "astutils.py",
        "clif_types.py",
        "gen.py",
        "postconv.py",
        "py3slots.py",
        "pyext.py",
        "slots.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":ast_manipulations_lib",
        "//clif/protos:ast_py_pb2",
    ],
)

py_test(
    name = "gen_test",
    size = "small",
    srcs = ["gen_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [":generator_lib"],
)

# Postconvertion utilities.
py_library(
    name = "postconv_lib",
    testonly = 1,
    srcs = ["postconv.py"],
    srcs_version = "PY2AND3",
)

py_test(
    name = "postconv_test",
    size = "small",
    srcs = ["postconv_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [":postconv_test_lib"],
)

py_library(
    name = "postconv_test_lib",
    testonly = 1,
    srcs = ["postconv_test.py"],
    srcs_version = "PY2AND3",
    deps = [
        ":postconv_lib",
        "//clif/protos:ast_py_pb2",
        "@com_google_protobuf//:protobuf_python",
        "@io_abseil_py//absl/testing:absltest",
    ],
)

cc_library(
    name = "postconv_clib",
    testonly = 1,
    hdrs = ["postconv.h"],
    deps = ["@com_github_google_glog//:glog"],
)

cc_test(
    name = "postconv_clib_test",
    size = "small",
    srcs = ["postconv_test.cc"],
    deps = [
        ":postconv_clib",
        "@com_google_googletest//:gtest_main",
    ],
)

# Postprocessing utilities.
py_library(
    name = "postproc",
    srcs = ["postproc.py"],
    srcs_version = "PY2AND3",
)

py_test(
    name = "postproc_test",
    size = "small",
    srcs = ["postproc_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":postproc",
        requirement("parameterized"),
        "@io_abseil_py//absl/testing:absltest",
    ],
)

# PYTD parsing

py_library(
    name = "parser_lib",
    srcs = [
        "pytd2proto.py",
        "pytd_parser.py",
    ],
    srcs_version = "PY2AND3",
    visibility = ["//clif:__subpackages__"],
    deps = [
        ":ast_manipulations_lib",
        "//clif/protos:ast_py_pb2",
        requirement("pyparsing"),
    ],
)

py_test(
    name = "pytd_parser_test",
    size = "small",
    srcs = ["pytd_parser_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [":pytd_parser_test_lib"],
)

py_library(
    name = "pytd_parser_test_lib",
    testonly = 1,
    srcs = ["pytd_parser_test.py"],
    srcs_version = "PY2AND3",
    deps = [
        ":parser_lib",
        requirement("pyparsing"),
        "@io_abseil_py//absl/testing:absltest",
    ],
)

# This test does not work in google3 environment, but invoked from devtools/clif/python.
py_library(
    name = "pytd2proto_test",
    testonly = 1,
    srcs = ["pytd2proto_test.py"],
    data = [
        "stltypes.h",
        "types.h",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":parser_lib",
        "@com_google_protobuf//:protobuf_python",
        "@io_abseil_py//absl/testing:absltest",
    ],
)

# Utility for generating py3slots.py.
# This target is not actually used. See slot_extractor.py module docstring.
py_binary(
    name = "slot_extractor",
    srcs = ["slot_extractor.py"],
    python_version = "PY3",
)

py_test(
    name = "module_test",
    size = "small",
    srcs = ["module_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [":module_test_lib"],
)

py_library(
    name = "module_test_lib",
    testonly = 1,
    srcs = ["module_test.py"],
    srcs_version = "PY2AND3",
    deps = [
        ":generator_lib",
        "//clif/protos:ast_py_pb2",
        "@com_google_protobuf//:protobuf_python",
        "@io_abseil_py//absl/testing:absltest",
    ],
)

py_test(
    name = "func_test",
    size = "small",
    srcs = ["func_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [":func_test_lib"],
)

py_library(
    name = "func_test_lib",
    testonly = 1,
    srcs = ["func_test.py"],
    srcs_version = "PY2AND3",
    deps = [
        ":generator_lib",
        "//clif/protos:ast_py_pb2",
        "@com_google_protobuf//:protobuf_python",
        "@io_abseil_py//absl/testing:absltest",
    ],
)

py_test(
    name = "class_test",
    size = "small",
    srcs = ["class_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [":class_test_lib"],
)

py_library(
    name = "class_test_lib",
    testonly = 1,
    srcs = ["class_test.py"],
    srcs_version = "PY2AND3",
    deps = [
        ":generator_lib",
        "//clif/protos:ast_py_pb2",
        "@com_google_protobuf//:protobuf_python",
        "@io_abseil_py//absl/testing:absltest",
    ],
)

py_test(
    name = "types_test",
    size = "small",
    srcs = ["types_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [":types_test_lib"],
)

py_library(
    name = "types_test_lib",
    testonly = 1,
    srcs = ["types_test.py"],
    srcs_version = "PY2AND3",
    deps = [
        ":generator_lib",
        "@io_abseil_py//absl/testing:absltest",
    ],
)

py_test(
    name = "slots_test",
    size = "small",
    srcs = ["slots_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [":slots_test_lib"],
)

py_library(
    name = "slots_test_lib",
    testonly = 1,
    srcs = ["slots_test.py"],
    srcs_version = "PY2AND3",
    deps = [
        ":generator_lib",
        "@io_abseil_py//absl/testing:absltest",
    ],
)

# This test does not work in google3 environment, but invoked from devtools/clif/python.
py_library(
    name = "pyext_test",
    testonly = 1,
    srcs = ["pyext_test.py"],
    data = [
        "stltypes.h",
        "types.h",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":generator_lib",
        ":parser_lib",
        "@io_abseil_py//absl/testing:absltest",
    ],
)

py_library(
    name = "type_customization",
    srcs = ["type_customization.py"],
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
)
