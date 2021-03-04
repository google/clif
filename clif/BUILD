package(default_visibility = [":__subpackages__"])

licenses(["notice"])

py_binary(
    name = "pyclif",
    srcs = ["pyclif.py"],
    deps = [
        "//clif/protos:ast_py_pb2",
        "//clif/python:generator_lib",
        "//clif/python:parser_lib",
        "@com_google_protobuf//:protobuf_python",
    ],
)
