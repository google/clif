"""Configure CLIF dependencies as a 3rd-party consumer."""

load("@com_google_protobuf//:protobuf_deps.bzl", "protobuf_deps")
load("@llvm-bazel//:terminfo.bzl", "llvm_terminfo_disable")
load("@llvm-bazel//:zlib.bzl", "llvm_zlib_disable")
load("@llvm-bazel//:configure.bzl", "llvm_configure")

def clif_configure():
    # Configure LLVM Bazel repository following
    # https://github.com/google/llvm-bazel/blob/http-archive-demo/http-archive-demo/WORKSPACE
    llvm_terminfo_disable(
        name = "llvm_terminfo",
    )

    llvm_zlib_disable(
        name = "llvm_zlib",
    )

    llvm_configure(
        name = "llvm-project",
        src_path = ".",
        src_workspace = "@llvm-project-raw//:WORKSPACE",
    )

    # Load common protobuf dependencies if they are not already available.
    protobuf_deps()
