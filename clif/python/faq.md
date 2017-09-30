## CLIF - Frequently Asked Questions

[TOC]

---
This document answers some frequently asked questions about the CLIF
open source project. If you have a question that isn't answered here, join the
[discussion group](http://groups.google.com/group/pyclif) and ask away!

## General

#### **Q:** Specifying C++ type is annoying and unpythonic. Can we get rid of it?

**A:** We'd like to get rid of it, but it appeared to be difficult.

#### **Q:** PyCLIF describe types, why does it not follow [PEP 484](https://www.python.org/dev/peps/pep-0484/) style?

**A:** PEP 484 was limited to (a) Python syntax and (b) Python execution
semantics.
PyCLIF is free of those limitations and chose the most expressive syntax for the
task.

#### **Q:** Can I wrap a class and specify a base class wrapped in another .clif file?

**A:** Yes. Be careful to use a Python import to get the base class, not
a C header. Use
```
from python.path.to.the.generated.wrapper.module import BaseClass
class Derived(BaseClass)
```
Note that in many cases you don’t even need to wrap the C++ base class.
It’s a C++ implementation detail not relevant to the Python API.
CLIF will take care of it.

#### **Q:** Why are there different quote types in CLIF?

**A:** As you probably noticed, files are always in "double quotes" and C++
names in \`backquotes\`.

#### **Q:** What about interfacing C++ with languages other than Python such as Java and Go?

**A:** CLIF is designed to support multiple language frontends. Python is our
first target. We expect success with Python to drive the desire to actually
implement and support other languages.

#### **Q:** How do I wrap an API that involves Protocol Buffers?

**A:** Use the `pyclif_proto` tool to wrap a proto with CLIF.  Import the
generated header as any other C++ header.
All messages and enums are now available to use in the .clif file.
To access a nested type use normal.python.dotted.notation.

#### **Q:** Why does CLIF insist on using the `package` statement in Protocol Buffers?

**A:** CLIF uses C++ argument-dependent lookup
((ADL)[http://en.cppreference.com/w/cpp/language/adl]) to find proper conversion
functions which does not work in the global namespace (that’s where proto
messages end up without a package). You can still use such a proto but it will
have a limited functionality without ADL (that mostly affects using proto in
containers). To generate the C++ source add **--allow_empty_package** flag to
the pyclif_proto run:
```
pyclif_proto --allow_empty_package -c somename.cc -h somename.h your_proto.proto
```

#### **Q:** Why does CLIF not have a standard support for NumPy?

**A:** CLIF allows users to extend it by writing to/from Python conversion
functions.
For ex. protobuf has a canonical C++ representation, so pyclif_proto generates
a CLIF C++ extension library that converts between Python canonical proto and
C++ canonical proto.
OTOH C++ has no canonical "numarray", so CLIF does not know what to convert
NumPy types to/from. Users must write the conversions.

## SWIG

#### **Q:** Can we still use CLIF and SWIG wrappers interchangeably?

**A:** CLIF can coexist with SWIG in one binary. To pass a SWIG-wrapped type as
CLIF input parameter add the following to the SWIG-wrapper:
```
%extend %{
PyObject* as_my_Foo() { return PyCapsule_New($self, “::my::Foo”, NULL); }
%}
```

#### **Q:** SWIG allows the use of IN_OUT parameters, why doesn't CLIF?

**A:** Unlike wrapped C++ classes, most other types are completely different
objects in C++ and Python. So “modify-in-place” C++ idiom does not work and CLIF
makes no attempt to hide double conversion needed to pass from Python to C++ and
back. Every time the author must make a choice either do that explicitly in
C++ adapter code or do something else. CLIF does not make that decision for
them.

#### **Q:** SWIG allows me to insert arbitrary Python / C++ code. Can I do the same in CLIF?

**A:** No. This SWIG misfeature proved to be difficult to maintain and
error-prone (almost no one gets Python refcounting and error processing right
especially for nested containers). All language code must go into corresponding
(py/c++) libraries for review and testing like any other code.  It also makes
such code available for static analysis and refactoring tools.

#### **Q:** SWIG supports overloaded C++ functions. How do I do that in CLIF?

**A:** Python does not support function overloading. To expose different
signatures of a C++ function to Python use different Python names (or default
arguments).
```
def Func()
def `Func` as FuncWithDelay(delay: int)
```

## C++ types

#### **Q:** Why is my __<put_your_favorite_here>__ C++ construct / API not supported?

**A:** Not all of C++ is supported by design. Plain C (macros, varargs, C arrays,
char\* strings) are also not supported.

#### **Q:** How do I pass Callbacks (or other function pointers)?

**A:** Use `std::function` instead. It will take a Python callable but still
check the number and type of arguments with `inspect.getcallargs()`.

#### **Q:** Can I use the `T* output` convention to return additional values from a `std::function`?

**A:** No. CLIF only supports input parameters in `std::function`.
Use `std::tuple` to return multiple values.

#### **Q:** Why doesn't CLIF accept varargs?

**A:** CLIF needs C++ type to be checked at language boundary and varargs does
not provide it.

#### **Q:** Why doesn't CLIF accept **T***?

**A:** It does. Although many things in modern C++ are better passed by value
e.g. `std::function`.

Also be extra careful accepting `T*` from CLIF - there is no object lifetime
guarantee, so don't store it.

#### **Q:** What about returning a **const T***?

**A:** Since Python doesn't have a good mapping of the C++ `const` construct
(there is no const object), CLIF doesn't support `const T*` other than making a
copy of it because CLIF cannot guarantee object constness requested by C++
author.

#### **Q:** How do I return a derived class pointer? My C++ function returns a base class pointer.

**A:** Change your C++ signature to return the derived class pointer as it
actually does. It should not disrupt your C++ code (an implicit cast will happen
on base class pointer assignment) but CLIF will know that a proper derived class
[smart] pointer is returned and do the right thing.

## Errors

#### **Q:** I'm getting a compile error: no matching function for call to 'Clif_PyObjAs'

**A:** The .clif file declares a valid C++ type but does not import a CLIF
wrapper for that type, so CLIF does not know how to deal with it. Look at the
error - next lines show candidates with that type <code>no known conversion
from <strong>'unknown_type</strong> *'</code>.
Use a [c_header_import](README.md#c_header-import-statement-cimport) statement
to tell CLIF about this type.

#### **Q:** I'm getting a compile error: call to deleted function 'Clif_PyObjFrom'

**A:** Python was trying create a copy on non-copyable C++ object. Either it was
an attempt of passing it by value or by const* (see [above](#q-what-about-const-t)).

#### **Q:** I’m getting a compile error: functions that differ only in their return type cannot be overloaded

**A:** If the next line says “previous declaration is here” and refers to a
standard library function, you unfortunately have a C++ header with
a name, along with Python extension module calling convention, that collides
with a standard function. You need to rename the C++ header file.

#### **Q:** I’m getting a TypeError: {function} argument {name} is not valid for ::absl::string_view (unicode given): expecting str.

**A:** This is a Python 2 only problem. Due to a limited API, there is nobody
to handle intermediate PyObject with encoded str. Consider a
`std::vector<absl::string_view>` getting unicode input. Each str creates an
encoded PyObject and either they leak or get destroyed immediately after we
finish that vector element conversion.

So the Python 2 caller has to encode prior to passing unicode to CLIF-wrapped
C++ taking a `absl::string_view` which is a “pointer” to a string data stored
elsewhere, ie. within a Python str object. In Python 3 such UTF-8 encoded
string data is hidden inside PyUnicodeObject representation. In non-pointer
C++ types it also not a problem as string data is copied from Python to C++
rather than referenced.

#### **Q:** How to debug “Is the keyword "explicit" missed in C++'s definition of constructors?” ?

**A:** This usually comes together with the multi match error: "Multiple C++
symbols with same name found.” By Google convention, constructors that can be
called with a single argument, except for copy and move constructors, must be
marked `explicit` in the class definition to avoid unexpected implicit
conversions. Check if you missed any `explicit` in your C++ definition of
single argument constructors. See (primer.md) for more details.

#### **Q:** How to debug “no matching constructor for initialization of 'typename std::remove_const<***>::type' ” ?

**A:** If you are wrapping a container type like `std::vector<type>` and
`std::unordered_map<type>` as functions parameters, add a default constructor
to the C++ nested type. When wrapping C++ container types, CLIF constructs a
local object of the nested type at backend. Thus, CLIF requires the nested type
of the container to be default constructible.
