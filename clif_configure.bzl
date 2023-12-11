########################################################################
# STALE SNAPSHOT OF WORK IN PROGRESS - NEVER WAS IN WORKING CONDITION. #
########################################################################

"""Configure CLIF dependencies as a 3rd-party consumer."""

load("@com_google_protobuf//:protobuf_deps.bzl", "protobuf_deps")
load("@llvm-bazel//:terminfo.bzl", "llvm_terminfo_disable")
load("@llvm-bazel//:zlib.bzl", "llvm_zlib_disable")
load("@llvm-bazel//:configure.bzl", "llvm_configure")
load("@rules_python//python:pip.bzl", "pip_install")
load("//third_party/py:python_configure.bzl", "python_configure")

def clif_configure(name = None):
    """Configure CLIF dependencies needed to compile and use CLIF.

    Args:
        name: unused (argument required due to native.bind)
    """

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

    # Configure python shared libraries and headers
    python_configure(name = "python_runtime")

    # Bind python runtime's headers to //external:python_headers for protobuf.
    # See https://github.com/protocolbuffers/protobuf/blob/master/util/python/BUILD
    if not native.existing_rule("python_headers"):
        native.bind(
            name = "python_headers",
            actual = "@python_runtime//:python_headers",
        )

    pip_install(
        name = "clif_python_deps",
        extra_pip_args = ["-v"],
        requirements = "//:requirements.txt",
    )
