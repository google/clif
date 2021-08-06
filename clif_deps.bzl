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
            sha256 = "59b862f50e710277f8ede96f083a5bb8d7c9595376146838b9580be90374ee1f",
            strip_prefix = "abseil-cpp-20210324.2",
            urls = ["https://github.com/abseil/abseil-cpp/archive/20210324.2.tar.gz"],
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

    if not native.existing_rule("com_github_gflags_gflags"):
        http_archive(
            name = "com_github_gflags_gflags",
            sha256 = "34af2f15cf7367513b352bdcd2493ab14ce43692d2dcd9dfc499492966c64dcf",
            strip_prefix = "gflags-2.2.2",
            urls = ["https://github.com/gflags/gflags/archive/v2.2.2.tar.gz"],
        )

    if not native.existing_rule("com_github_google_glog"):
        http_archive(
            name = "com_github_google_glog",
            sha256 = "62efeb57ff70db9ea2129a16d0f908941e355d09d6d83c9f7b18557c0a7ab59e",
            strip_prefix = "glog-d516278b1cd33cd148e8989aec488b6049a4ca0b",
            urls = ["https://github.com/google/glog/archive/d516278b1cd33cd148e8989aec488b6049a4ca0b.zip"],
        )

    if not native.existing_rule("io_abseil_py"):
        http_archive(
            name = "io_abseil_py",
            sha256 = "ac357a83c27464f5a612fda94704d0cc4fd4be1f2c0667c1819c4037e875f7aa",
            strip_prefix = "abseil-py-pypi-v0.11.0",
            urls = [
                "https://mirror.bazel.build/github.com/abseil/abseil-py/archive/pypi-v0.11.0.zip",
                "https://github.com/abseil/abseil-py/archive/pypi-v0.11.0.zip",
            ],
        )

    if not native.existing_rule("six_archive"):
        http_archive(
            name = "six_archive",
            build_file = "@com_google_protobuf//:third_party/six.BUILD",
            sha256 = "d16a0141ec1a18405cd4ce8b4613101da75da0e9a7aec5bdd4fa804d0e0eba73",
            urls = ["https://pypi.python.org/packages/source/s/six/six-1.12.0.tar.gz"],
        )

    # rules_python 0.1.0 is needed for pip_install. Older versions of
    # rules_python might not have pip_install functionalities.
    if not native.existing_rule("rules_python"):
        http_archive(
            name = "rules_python",
            sha256 = "b6d46438523a3ec0f3cead544190ee13223a52f6a6765a29eae7b7cc24cc83a0",
            url = "https://github.com/bazelbuild/rules_python/releases/download/0.1.0/rules_python-0.1.0.tar.gz",
        )
