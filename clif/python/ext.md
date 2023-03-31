# Extending CLIF with C++ libraries

CLIF has a number of C++ types it already knows, but it can't cover them all. Normally
CLIF is used for wrapping new types by creating a .clif file and running CLIF.
However, when the C++ API uses a type that can't be wrapped normally, the user
can teach CLIF how to handle that type by writing a C++ library. This doc
explains how to do that.

When CLIF passes data to/from C++ across the language boundary, it does the
conversion between C++'s internal storage representation and Python's internal
storage representation. This conversion might be as simple as copying a C++
pointer or as complex as serializing and deserializing a protocol buffer. By
writing a C++ library, the author can control how CLIF performs this conversion.
However, this requires an understanding of the internal representations of the
data in both languages.

Teaching CLIF a new type requires implementing the following:

1.  Conversion function(s) to pass data from Python to C++ (`Clif_PyObjAs`).
2.  Conversion function(s) to pass data from C++ to Python (`Clif_PyObjFrom`).
3.  Definition of a CLIF name to refer to the C++ type from .clif files.

CLIF uses [ADL](http://en.cppreference.com/w/cpp/language/adl) to find the
conversion function, so those functions should be placed in the namespace where
the C++ type we're teaching CLIF about is located.

The various possible conversions are described below. None of them are required.
Rather, you should only write the conversions which make sense for your data
type. CLIF will use the presence or absence of certain conversions as an
indicator of the type capabilities.

## Passing data from Python to C++

Conversions of this type are supplied by writing a function named
`Clif_PyObjAs`, which returns a `bool` to indicate if an input Python object was
successfully passed to C++. When returning `false` the routine **must** set a
Python exception (eg. with *PyErr_SetString(PyExc_ValueError, "invalid value for
CppType")* call).

You may write one or more of the following overloads, depending on the type of
conversions which make sense for your data type. Note that it is your
responsibility to increase or decrease the reference count for the provided
`PyObject` to support the behavior described below. This should be done in
within the `Clif_PyObjAs` implementation.

1.  To support **copying** data from Python to C++, write a function with the
    signature

    ```c++
    bool Clif_PyObjAs(PyObject*, CppType*);
    ```

    The second argument points to a default-constructed object which you should
    fill in with a copy of the data in the `PyObject`. If you would like to
    construct the C++ object yourself, use the signature

    ```c++
    bool Clif_PyObjAs(PyObject*, std::optional<CppType>*);
    ```

2.  To support **moving** data from Python to C++, write a function with the
    signature

    ```c++
    bool Clif_PyObjAs(PyObject*, std::unique_ptr<CppType>*);
    ```

    Your function should ensure the `PyObject` has no remaining references, so
    that after the move, the Python object will be invalidated and raise an
    exception on access attempt.

3.  To support **sharing** data between Python and C++, write a function with
    the signature

    ```c++
    bool Clif_PyObjAs(PyObject*, std::shared_ptr<CppType>*);
    ```

    When implementing this function, you are responsible for ensuring that both
    Python and C++ access valid memory throughout. If the C++ object you create
    points to memory owned by the supplied PyObject, then one way to ensure this
    is to increase the Python reference count when creating the `shared_ptr`,
    and create a custom deleter for the `shared_ptr` which decreases the Python
    reference count. Here is an example which does just that:

    ```c++
    bool Clif_PyObjAs(PyObject* py, std::shared_ptr<CppType>* c) {
      CppType* cpp_type = new CppType;
      // TODO: Set up `cpp_type` to point to the data within `py`.

      // Increase Python ref counter now.
      Py_INCREF(py);
      *c = std::shared_ptr<CppType>(cpp_type, [py](CppType* unused) {
        // Decrease Python ref counter when `cpp_type` is deleted.
        PyGILState_STATE state = PyGILState_Ensure();
        Py_DECREF(py);
        PyGILState_Release(state);
      });
      return true;
    }
    ```

    Note that due to a CLIF
    [limitation](https://b.corp.google.com/issues/79540676), creating a
    `shared_ptr` conversion requires the existence of a `unique_ptr` conversion
    as well. You can work around this by defining a deleted `unique_ptr`
    conversion, like below:

    ```c++
    bool Clif_PyObjAs(PyObject* py, std::unique_ptr<CppType>*) = delete;
    ```

4.  To support **borrowing** data from Python to C++, write a function with the
    signature

    ```c++
    bool Clif_PyObjAs(PyObject*, CppType**);
    ```

    This pointer represents *borrowing* data from Python, not an ownership
    transfer. This form gives C++ a raw pointer to the internal representation
    of the Python object. Be careful as the Python object can disappear, making
    the pointer invalid.

## Passing data from C++ to Python

Conversions of this type are supplied by writing a function named
`Clif_PyObjFrom`, which returns a **new** `PyObject`. If the conversion fails,
the function should ensure a Python error is set and return `nullptr`.

You may write one or more of the following forms, depending on the type of
conversions which make sense for your data type:

1.  To support **copying** data from C++ to Python, write a function with the
    signature

    ```c++
    PyObject* Clif_PyObjFrom(const CppType&, const ::clif::py::PostConv&);
    ```

2.  To support **moving** data from C++ to Python, write a function with the
    signature

    ```c++
    PyObject* Clif_PyObjFrom(std::unique_ptr<CppType>, const ::clif::py::PostConv&);
    ```

3.  To support **sharing** data between C++ and Python, write a function with
    the signature

    ```c++
    PyObject* Clif_PyObjFrom(std::shared_ptr<CppType>, const ::clif::py::PostConv&);
    ```

4.  To support **borrowing** data from C++ to Python, write a function with the
    signature

    ```c++
    PyObject* Clif_PyObjFrom(CppType*, const ::clif::py::PostConv&);
    ```

    Warning: This conversion type is extremely dangerous: Python will likely
    store the pointer, which can easily become dangling as C++ object lifetime
    is different from Python object lifetime. Better use other conversion types.

### Python post-conversion processing

Sometimes a C++ type is not enough to determine which Python type to convert to.
For example in Python 3 `std::string` might be converted to `bytes` or `str`.
That information is provided in the .clif file and passed along in
`::clif::py::PostConv` argument. To get its definition `#include
"clif/python/postconv.h"`.

Post-conversion processing provides a function pointer to a `PyObject*
(*)(PyObject*);` C function that needs to be called during conversion to the
Python type that needs extra processing. However all other converter functions
need to play along and pass that information through even if they don't use it
themselves. That is especially true for containers to enable post-conversion
processing for contained types. Take a look at
`clif/python/stltypes.h` in the CLIF runtime library and
`absl::StatusOr` examples.

## Introducing a CLIF name for the C++ type

Usually you will need a CLIF name to identify the C++ type within .clif files.
To add a CLIF name add a structured comment of this form:

```c++
// CLIF use `::fq::CppType` as ClifName
```

Strictly speaking the CLIF name is internal to CLIF and only works in the
context of `.clif` files, but often the CLIF and Python names are identical,
in particular for Python built-in types like `int`, `set`, `dict`.

Multiple C++ type names may map to the same CLIF name. Currently CLIF uses
a simple "last mapping seen wins" approach which can lead to surprises when
a new `// CLIF use` is added, or even if it is just that the order of
C++ `#include`s changes in a refactoring project. For example, a
``// CLIF use `my::BytesLikeType` as bytes`` may suddenly take precedence over
``// CLIF use `std::string` as bytes``. There is a simple way to work around
this with `// CLIF use2` (think: "use this, too, but with lower priority"),
for example:

```c++
// CLIF use2 `my::BytesLikeType` as bytes
```

In most cases it will be best to prefer `use2` when adding a mapping to a CLIF
name that is established elsewhere already.

## Using the library

Besides adding the `cc_library` to the `py_clif_cc` deps use normal

```python
from "path/to/the/library/header" import *
```

to load the `ClifName` in a .clif file.
