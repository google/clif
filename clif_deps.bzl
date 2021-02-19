"""Load dependencies needed to compile CLIF as a 3rd-party consumer."""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

LLVM_COMMIT = "1f21de535d37997c41b9b1ecb2f7ca0e472e9f77"  # 2021-01-15
LLVM_BAZEL_TAG = "llvm-project-%s" % (LLVM_COMMIT,)
LLVM_BAZEL_SHA256 = "f2fd051574fdddae8f8fff81f986d1165b51dc0b62b70d9d47685df9f2d804e1"
LLVM_SHA256 = "3620b7e6efa72e73e2e83420d71dfc7fdf4c81cff1ee692f03e3151600250fe0"
LLVM_URLS = [
    "https://storage.googleapis.com/mirror.tensorflow.org/github.com/llvm/llvm-project/archive/{commit}.tar.gz".format(commit = LLVM_COMMIT),
    "https://github.com/llvm/llvm-project/archive/{commit}.tar.gz".format(commit = LLVM_COMMIT),
]

def clif_deps():
    """Load common dependencies needed to compile and use CLIF."""

    if not native.existing_rule("llvm-project"):
        http_archive(
            name = "llvm-bazel",
            sha256 = LLVM_BAZEL_SHA256,
            strip_prefix = "llvm-bazel-{tag}/llvm-bazel".format(tag = LLVM_BAZEL_TAG),
            url = "https://github.com/google/llvm-bazel/archive/{tag}.tar.gz".format(tag = LLVM_BAZEL_TAG),
        )

        http_archive(
            name = "llvm-project-raw",
            build_file_content = "#empty",
            sha256 = LLVM_SHA256,
            strip_prefix = "llvm-project-" + LLVM_COMMIT,
            urls = LLVM_URLS,
        )

    if not native.existing_rule("com_google_protobuf"):
        http_archive(
            name = "com_google_protobuf",
            sha256 = "bf0e5070b4b99240183b29df78155eee335885e53a8af8683964579c214ad301",
            strip_prefix = "protobuf-3.14.0",
            urls = [
                "https://storage.googleapis.com/mirror.tensorflow.org/github.com/protocolbuffers/protobuf/archive/v3.14.0.zip",
                "https://github.com/protocolbuffers/protobuf/archive/v3.14.0.zip",
            ],
        )

    if not native.existing_rule("com_google_absl"):
        http_archive(
            name = "com_google_absl",
            sha256 = "6622893ab117501fc23268a2936e0d46ee6cb0319dcf2275e33a708cd9634ea6",
            strip_prefix = "abseil-cpp-20200923.3",
            urls = ["https://github.com/abseil/abseil-cpp/archive/20200923.3.zip"],
        )

    if not native.existing_rule("com_google_googletest"):
        http_archive(
            name = "com_google_googletest",
            sha256 = "9dc9157a9a1551ec7a7e43daea9a694a0bb5fb8bec81235d8a1e6ef64c716dcb",
            strip_prefix = "googletest-release-1.10.0",
            urls = [
                "https://mirror.bazel.build/github.com/google/googletest/archive/release-1.10.0.tar.gz",
                "https://github.com/google/googletest/archive/release-1.10.0.tar.gz",
            ],
        )
