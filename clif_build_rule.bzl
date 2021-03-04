"""Provide bazel rules for OSS CLIF."""

# Label for our OSS CLIF binary pyclif.
CLIF_PYCLIF = "//clif:pyclif"

# Label for our OSS CLIF C++ runtime headers and sources.
CLIF_CPP_RUNTIME = "//clif/python:clif"

# Label for clif matcher for pyclif script's --matcher_bin
CLIF_MATCHER = "//clif/backend:clif_matcher"

# Label for types.h for pyclif script's --prepend
CLIF_TYPES = "//clif/python:types.h"

# Label for LLVM headers
LLVM_HEADERS = "//third_party/llvm:llvm-headers"

# The CLIF generated code only compiles with C++17.
EXTRA_CC_FLAGS = ["-std=c++17"]

_PROTO_LIBRARY_SUFFIX = "_pyclif"

PYCLIF_PYEXT_SUFFIX = ".so"

PYCLIF_CC_LIB_SUFFIX = "_cclib"

PYCLIF_WRAP_SUFFIX = "_clif_wrap"

def _get_transitive_headers(hdrs, deps):
    """Obtain the header files for a target and its transitive dependencies.

      Args:
        hdrs: a list of header files
        deps: a list of targets that are direct dependencies

      Returns:
        A collection of the transitive headers.
      """
    return depset(
        hdrs,
        transitive = [dep[CcInfo].compilation_context.headers for dep in deps],
    )

def _clif_wrap_cc_impl(ctx):
    """Executes CLIF cmdline tool to produce C++ python model from a CLIF spec."""
    if len(ctx.files.srcs) != 1:
        fail("Exactly one CLIF source file label must be specified.", "srcs")

    clif_spec_file = ctx.files.srcs[0]

    # Inputs is a set of all of the things we depend on, not inputs to the CLIF
    # program itself.
    initial_inputs = [clif_spec_file]
    initial_inputs += ctx.files._cliflib
    initial_inputs += ctx.files.clif_deps
    initial_inputs += ctx.files.toolchain_deps
    inputs = _get_transitive_headers(initial_inputs, ctx.attr.deps).to_list()

    # Compute the set of include directories for CLIF so it can find header files
    # used in the CLIF specification. These are the repo roots for all of our
    # inputs (aka deps) plus all of the quote and system includes for our C++
    # deps.
    include_dirs = depset(
        _get_repository_roots(ctx, inputs),
        transitive = [
            dep[CcInfo].compilation_context.quote_includes
            for dep in ctx.attr.deps
        ] + [
            dep[CcInfo].compilation_context.system_includes
            for dep in ctx.attr.deps
        ] + [
            dep[CcInfo].compilation_context.includes
            for dep in ctx.attr.deps
        ],
    )

    # Construct our arguments for CLIF.
    args = [
        "--py3output",
        "--modname",
        ctx.attr.package_name + "." + ctx.attr.module_name,
        "-c",
        ctx.outputs.cc_out.path,
        "-g",
        ctx.outputs.h_out.path,
        "-i",
        ctx.outputs.ccinit_out.path,
        "--matcher_bin",
        ctx.executable._clif_matcher.path,
        "--prepend",
        ctx.files._clif_types[0].path,
    ]
    include_args = ["-I" + i for i in include_dirs.to_list()]

    # Add these includes to CLIF itself.
    args += include_args

    # Add these includes to those passed through by CLIF to its C++ matcher.
    args.append("-f" + " ".join(include_args + EXTRA_CC_FLAGS))

    # The last argument is the actual CLIF specification file.
    args.append(clif_spec_file.path)

    outputs = [ctx.outputs.cc_out, ctx.outputs.h_out, ctx.outputs.ccinit_out]
    ctx.actions.run(
        executable = ctx.executable._clif,
        arguments = args,
        inputs = inputs + ctx.files._clif_matcher,
        outputs = outputs,
        mnemonic = "CLIF",
        progress_message = "CLIF wrapping " + clif_spec_file.path,
    )

_clif_wrap_cc = rule(
    attrs = {
        "srcs": attr.label_list(
            mandatory = True,
            allow_files = True,
        ),
        "deps": attr.label_list(
            allow_files = True,
            providers = [CcInfo],
        ),
        "toolchain_deps": attr.label_list(
            allow_files = True,
        ),
        # For rule "//foo/python:bar_clif" this should be "bar".
        "module_name": attr.string(mandatory = True),
        # For rule "//foo/python:bar_clif" this should be "foo/python".
        "package_name": attr.string(mandatory = True),
        "clif_deps": attr.label_list(allow_files = True),
        # Hidden attribute: the Label for our PYCLIF binary itself.
        "_clif": attr.label(
            default = Label(CLIF_PYCLIF),
            executable = True,
            cfg = "host",
        ),
        # Hidden attribute: The label to the C++ CLIF header files.
        "_cliflib": attr.label(
            default = Label(CLIF_CPP_RUNTIME),
            allow_files = True,
        ),
        # Hidden attribute: The label to the clif_matcher binary.
        "_clif_matcher": attr.label(
            default = Label(CLIF_MATCHER),
            executable = True,
            cfg = "host",
        ),
        # Hidden attribute: The label to the C++ CLIF types header file.
        "_clif_types": attr.label(
            default = Label(CLIF_TYPES),
            allow_single_file = True,
        ),
    },
    output_to_genfiles = True,
    outputs = {
        "cc_out": "%{module_name}.cc",
        "h_out": "%{module_name}_clif.h",
        "ccinit_out": "%{module_name}_init.cc",
    },
    implementation = _clif_wrap_cc_impl,
)

def _get_repository_roots(ctx, files):
    """Returns abnormal root directories under which files reside.

    When running a ctx.action, source files within the main repository are all
    relative to the current directory; however, files that are generated or exist
    in remote repositories will have their root directory be a subdirectory,
    e.g. bazel-out/local-fastbuild/genfiles/external/jpeg_archive. This function
    returns the set of these devious directories, ranked and sorted by popularity
    in order to hopefully minimize the number of I/O system calls within the
    compiler, because includes have quadratic complexity.

    Args:
      ctx: context
      files: list of paths
    Returns:
      list of directories
    """
    ctx = ctx  # unused
    result = {}
    for f in files:
        root = f.root.path
        if root:
            if root not in result:
                result[root] = 0
            result[root] -= 1
        work = f.owner.workspace_root
        if work:
            if root:
                root += "/"
            root += work
        if root:
            if root not in result:
                result[root] = 0
            result[root] -= 1
    return [k for v, k in sorted([(v, k) for k, v in result.items()])]

def _clif_to_lib(label, extension):
    """Gets a C++/python/etc library corresponding to a CLIF library rule.

    Args:
      label: string. The name of a clif_rule. If the name is of the
        form <target>_pyclif we will stripe off the `_pyclif` ending.
      extension: string. The expected extension of our name library.

    Returns:
      <target>_extension.
    """
    if label.endswith(_PROTO_LIBRARY_SUFFIX):
        basename = label[:-len(_PROTO_LIBRARY_SUFFIX)]
    else:
        basename = label
    return basename + extension

def clif_deps_to_cclibs(labels):
    """Gets the cc_library name for each of label as a list."""
    return [_clif_to_lib(name, PYCLIF_CC_LIB_SUFFIX) for name in labels]

def py_clif_cc(
        name,
        srcs,
        clif_deps = [],
        pyclif_deps = [],
        deps = [],
        copts = [],
        py_deps = [],
        **kwargs):
    """Defines a CLIF wrapper rule making C++ libraries accessible to Python.

    Here are two example working py_clif_cc rules:

    py_clif_cc(
        name = "proto_cpp",
        srcs = ["proto_cpp.clif"],
        pyclif_deps = ["//oss_clif:oss_pyclif"],
        deps = ["//oss_clif:proto_cpp_lib"],
    )

    py_clif_cc(
        name = "pyclif_dep",
        srcs = ["pyclif_dep.clif"],
        deps = ["//oss_clif:pyclif_dep_lib"],
    )

    Args:
      name: The name of the rule. This name becomes a suitable target for Python
        libraries to access the C++ code.
      srcs: A list that must contain a single file named <name>.clif containing
        our CLIF specification.
      clif_deps: A list of other CLIF rules included by this one.
      pyclif_deps: A potentially empty list of pyclif_proto_library rules
      deps: A list of C++ dependencies.
      copts: List of copts to provide to our native.cc_library when building our
        python extension module.
      py_deps: List of dependencies to provide to our the native.py_library
        created by this rule.
      **kwargs: kwargs passed to py_library rule created by this rule.
    """
    extended_cc_deps = deps + [CLIF_CPP_RUNTIME] + pyclif_deps

    # Here's a rough outline of how we build our pyclif library:
    #
    # Suppose we have a module named 'foo'.
    #
    # _clif_wrap_cc runs pyclif to produce foo.cc, foo.h, and foo_init.cc which
    # C++ python extension module.

    deps = extended_cc_deps + clif_deps_to_cclibs(clif_deps)

    _clif_wrap_cc(
        name = name + PYCLIF_WRAP_SUFFIX,
        srcs = srcs,
        deps = deps + [LLVM_HEADERS],
        clif_deps = clif_deps_to_cclibs(clif_deps),
        toolchain_deps = ["@bazel_tools//tools/cpp:current_cc_toolchain"],
        module_name = name,
        # Turns //foo/bar:baz_pyclif into foo.bar to create our fully-qualified
        # python package name.
        package_name = native.package_name().replace("/", "."),
    )
