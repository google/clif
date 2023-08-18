# The Python CLIF Primer

This is a user guide for using Python CLIF - The Python extension module
generator that wraps C++ libraries.
It tries to be clear and explain all the nuances involved in detail.

.

The organization of this document is such that it starts with illustration of
the simplest of CLIF wrappings and progressively builds on this information
in the following sections. Hence, if you are new to CLIF, read these sections in
the order they appear here. If you are already using CLIF, you can jump to any
section of your choice but keep in mind that some of the CLIF features used in
that section were probably introduced in earlier sections.

NOTE: The examples used in this doc live in
[clif/examples](
../../examples).
Each example has its own directory. Within that directory, the CLIF wrapping is
in the subdirectory named `python`. The `python` directory also contains a test
illustrating the usage of the corresponding CLIF wrapping and its features.

## The Basics {#basics}

### File Organization {#basic_file_org}

CLIF enables you to wrap C++ constructs defined in header files. To avoid
[One Definition Rule](https://en.cppreference.com/w/cpp/language/definition)
(ODR) violations, a strict policy is suggested.

## C++-side customizations in `<HEADER>_clif_aux.h` {#clif_aux_h}

Generally, PyCLIF only allows wrapping functions and classes defined in one
specific `<HEADER>.h`, as explained above. The only exception is the option
to add a `<HEADER>_clif_aux.h` file with additional PyCLIF-specific C++ code,
usually implementing small functions to adapt or extend the existing C++
interface for Python. The `<HEADER>_clif_aux.h` file must be in the same
directory as the `<HEADER>.clif` file. A minimal example, showing how to
add in a simple function, can be found here:

*   [clif/examples/clif_aux/python/lib_hello_clif_aux.h](
    ../../examples/clif_aux/python/lib_hello_clif_aux.h)

Extending a C++ class with methods that only exist in Python is also possible
but a little more involved:

*   [clif/examples/extend_from_clifaux/python/](
    ../../examples/extend_from_clifaux/python/)
*   The unit tests in
    [clif/testing/python/extend_from_clifaux.clif](
    ../testing/python/extend_from_clifaux.clif)
    are also useful as a reference.

Extending a C++ class with constructors is special. All extended constructors
need to return a `unique_ptr` or `shared_ptr` to the created instance:

*   [clif/testing/python/extend_init_clif_aux.h](
    ../testing/python/extend_init_clif_aux.h)

C++ classes can also be extended with properties:

*   [clif/testing/python/extend_properties.clif](
    ../testing/python/extend_properties.clif)

Caveat: When extending nested classes, type names in extended functions or
properties must be fully qualified. For example::

```
class Outer:
  class Inner:
    def foo(other: Inner)  # Not using @extend: OK with unqualified type name.

    @extend
    def bar(other: Outer.Inner)  # Needs fully-qualified type name.
```

Unfortunately this is not easy to fix (cost/benefit is high).

The `_clif_aux.h` feature can also be useful to work around PyCLIF limitations
or bugs.

Please use `_clif_aux.h` strictly for implementing adapter code.
Implement anything more involved in regular `.h/cc` files. A good rule of
thumb: if your code needs unit tests to conform to best practices, do not
implement it in `_clif_aux.h`.

## Python-side customizations in `<HEADER>.py` {#py_library_wrapper}

The need for Python-side customizations arises most commonly when an
existing Python API is replaced with a new version building on PyCLIF,
but there can be other reasons, even for newly designed APIs. Of course,
Python-side customizations can be implemented in any `py_library`, but if
`<HEADER>` is the preferred Python import for some reason, the strict file
organization rules for `<HEADER>.clif` need a small exception. To make this
more concrete with an example: given `mylib.h`, `mylib.clif`, and a needed
`py_library(name="mylib")`, the standard `py_clif_cc(name="mylib")` clashes
with the `py_library` rule. To handle this case gracefully, PyCLIF supports
using an underscore as a prefix, with the effect to make the C++ extension
module **private**:

  ```build
  py_clif_cc(name="_mylib")
  ```

Note that the name of the `.clif` file is unchanged, but the Python import for
the extension changes from `mylib` to `_mylib`. With that, the Python-side
customizations can be implemented in `mylib.py`, which will usually import
`_mylib` either as

```python
from some.place import _mylib as ext
```

and/or (!)

```python
from some.place._mylib import *  # pylint: disable=wildcard-import
```

The second form may be preferable if `_mylib` wraps many functions or types,
which would otherwise need to be exported via many assignments like
`foo = ext.foo`.

Free functions can trivially be added in `mylib.py`, but adding Python-only
methods to wrapped C++ classes is slightly involved:

```python
from clif.python import type_customization

Bar = ext.Bar


@type_customization.extend(ext.Bar):
class _:

  def foo(self, ...):
    ...
```

Extending methods from Python in this way works for instance methods,
properties, classmethods, staticmethods, and even docstrings and other
data members.

To ensure that the Python-side customizations are always applied, it is
important to specify

```
OPTION is_extended_from_python = True
```

in mylib.clif (see go/pyclif#OPTION).

Current Limitation:

  * `@type_customization.extend` needs a pytype workaround as explained and
    tracked under b/161575039. See also:
    [clif/examples/extend_from_python/python/example.py](
    ../../examples/extend_from_python/python/example.py)

## Wrapping POD data types {#wrappod}

NOTE: The example, `wrappod`, used in this section lives in
[clif/examples/wrappod/](
../../examples/wrappod/).

We begin with learning how to wrap POD[^1] data types, namely, data types
defined as simple `struct`s/`class`es containing only POD data fields in C++.
Let us provide wrappers for the C++ struct `MyClass` defined in the file
`wrappod.h`:

```c++
namespace clif_example {
namespace wrappod {

struct MyClass {
  int a;       // Available in Python as an int value
  float f;     // Available in Python as a float value
  string s;    // Available in Python as a bytes object

  std::vector<int> v;    // Available in Python as a list of int values via
                         // getter and setter methods.
  std::pair<int, int> p; // Available in Python as a 2-tuple

  double d; // This field is unused in this example, so no need to wrap it.
};

}  // namespace wrappod
}  // namespace clif_example
```

The CLIF file wrapping the above struct should be named `wrappod.clif` and
reside in a directory named `python` (or `clif`) in the directory where the
header file `wrappod.h` is saved. Let us consider a CLIF wrapping as follows:

```python
from "clif/examples/wrappod/wrappod.h":
  namespace `clif_example::wrappod`:
    class MyClass:
      a: int
      f: float

      s: bytes  # C++ string types get wrapped into Python bytes.

      `p` as my_pair: tuple<int, int>  # C++ std pairs get wrapped into tuples.

      # The following two declarations make the C++ field
      # 'v' available in Python via getter and setter methods.
      @getter
      def `v` as getv(self) -> list<int> # C++ vectors get wrapped into Python
                                         # lists

      @setter
      def `v` as setv(self, l: list<int>)

```

### Header File

The very first line specifies the header file from which to fetch the C++
constructs. It is done using the `from` directive whose general syntax is as
follows:

```
from "path/to/the/header/file.h":
```

NOTE: The general rule in CLIF is to enclose file names and paths in double
quotes `"`.

### Constructs Declared in Namespaces

If the C++ construct that we want wrapped into Python is defined in a namespace,
then we should declare the namespace using the `namespace` directive. The above
CLIF example does exactly that with:

```
namespace `clif_example::wrappod`:
```

The general syntax of a namespace directive is as follows:

```
namespace `<FULLY_QUALIFIED_CPP_NAMESPACE>`:
```

NOTE: The general rule in CLIF is to enclose C++ names, that we do not want to
expose into Python, in back-ticks.

### Classes

Following the namespace directive is the class declaration. The class
declaration is similar to the header of a Python class definition. Since we want
to wrap the C++ struct `MyClass` into a Python class also named `MyClass`, the
declaration for our wrapped class is straight forward:

```
class MyClass:
```

We will talk about the general syntax of a class declaration in a later
section.

NOTE: A CLIF declaration wrapping a C++ final class should be decorated with
`@final.`

### Fields {#fields}

The syntax for the fields in a class declaration is intuitive. We declare each
field we want to expose in to Python, in the following format:

```
<FIELD_NAME>: <PYTHON_TYPE>
```

Notice that the CLIF file does not declare the field `d` of `MyClass`. This was
done intentionally to illustrate that if the CLIF file does not explicitly
specify that a particular C++ construct has to be wrapped, then it will not be
available in Python.

The wrapped fields end up in Python with types governed by the type conversion
rules specified [here](README.md#type-correspondence).

### Renaming a C++ API for use in Python {#renaming}

The C++ field `p` of `MyClass` has been exposed as `my_pair` in Python. While it
was not necessary to do such a renaming for this example, it has been done to
introduce the general CLIF facility to expose an API via a different,
potentially more pythonic, name in Python.
As we will see in a later section, such a facility helps us
expose overloaded C++ constructs, each with a different name, into Python as the
Python language does not support overloading.  To specify a new name, at
every place where a C++ name is to be used in a CLIF declaration, replace it
with:

```
`<CPP_NAME>` as <PYTHON_NAME>
```

Notice that the C++ name is enclosed in back-ticks as per rule that C++
names that we do not want to expose into Python should be enclosed in
back-ticks.

NOTE: As we will see later, which of the overloaded C++ constructs is to be
wrapped is deduced using other components of the declaration.

### Unproperty: Exposing C++ Fields via Setters/Getters in Python {#unproperty}

In the above example, the field `v` was not wrapped into a Python class
property. Instead, it was exposed via _getter_ and _setter_ methods `getv` and
`setv` respectively. This illustrates the CLIF _unproperty_ feature which
enables one to expose a C++ field not as a Python class property, but via getter
and setter methods.

As can be seen in the CLIF file, a getter _unproperty_ method should be
decorated with `@getter`. It should take exactly one argument named `self` and
return the wrapped C++ field in a Python object. The general syntax to declare a
getter is as follows:

```
@getter
def `<CPP_FIELD_NAME>` as <GETTER_METHOD_DECL>
```

where `GETTER_METHOD_DECL` should be in the PYTD method header syntax without
the `def` keyword:

```
<GETTER_METHOD_NAME>(self) -> <FIELD_TYPE>
```

The syntax for the declaration of the setter _unproperty_ method is very
similar:

```
@setter
def `<CPP_FIELD_NAME>` as <SETTER_METHOD_DECL>
```

A setter takes an additional argument, the new value of the C++ field, and
returns nothing:

```
<SETTER_METHOD_NAME>(self, val: FIELD_TYPE)
```

NOTE: A C++ field does not need to have both the _unproperty_ getter and setter
methods. One can choose to provide only the getter method. However, note that
providing only a setter is not supported by CLIF and results in error.

The above example also illustrates why CLIF needs to provide the _unproperty_
feature at all. If the C++ field `v` were to be a property, an access to it from
Python with eg. `obj.v`, actually refers to a copy of the C++ `v` and not
to the C++ `v` itself. Hence, mutations of `v` on the Python side will not
reflect on the C++ side. Consequently, a subsequent access to `v`, say again as
`obj.v`, will again refer to a copy of the un-mutated C++ `v` surprising Python
programmers. The following code snippet illustrates this.

```python
obj = wrappod.MyClass()

print('Before appending: ', obj.v)
obj.v.append(1)  # Succeeds silently
print('After appending: ', obj.v)
```

This prints:

```
'Before appending: ', []
'After appending: ', []
```

Clearly, the list property was not really mutated at all. In general, a returned
object or a property-accessed object of a container type (`list`, `dict`,
`set`, class object etc.) is not a reference to the underlying C++ container. It
is a copy of the C++ container and mutations to the object on Python side are
not reflected in C++.

To avoid such non-pythonic suprises, use the _unproperty_ feature to expose a
container field to Python as getter and setter methods.  That way calling
the _setter_ explicitly describes when to update the C++ field value.

## Wrapping Functions

NOTE: The example, `wrapfunc`, used in this section lives in
[clif/examples/wrapfunc/](
../../examples/wrapfunc/).

In this section, we will learn how to provide Python wrappers for plain (as in
non-member, non-template) C++ functions using CLIF. The functions we want to
wrap are present in a header file `wrapfunc.h` as follows:

```c++
namespace clif_example {
namespace wrappod {
class MyClass;
}  // namespace wrappod
}  // namespace clif_example

namespace clif_example {
namespace wrapfunc {

void ResetState();

// Sets the state to a.
void SetState(int a);

// Sets the state to a + b
void SetState(int a, int b);

// Sets the state to s.a
void SetState(const clif_example::wrappod::MyClass &s);

// Returns the state
int GetState();

/*
The following conflicts with "int GetState();" if we want to provide a wrapper
for GetState returning an int.
void GetState(int *a);
*/

// Stores the state in s.a
void GetState(clif_example::wrappod::MyClass *s);

}  // namespace wrapfunc
}  // namespace clif_example
```

Notice that some of the C++ functions defined in this header file use the struct
`MyClass` defined in the header file from an earlier example. Likewise, the
Python wrappings of these functions will make use of the Python wrappings of
that struct. The CLIF file wrapping these functions is as follows:

```python
# We use a type wrapped elsewhere in this .clif file.
# Hence, import the wrapped type from the CLIF generated C++ header file.
from "clif/examples/wrappod/python/wrappod_clif.h" import *

# By importing in the pythonic style as well, we improve PyType safety (when
# available), as the generated `.pyi` files can use `MyClass` rather than `Any`
# in the inputs and outputs.
from clif.examples.wrapped.python.wrappod import MyClass

from "clif/examples/wrapfunc/wrapfunc.h":
  namespace `clif_example::wrapfunc`:
    def ResetState()
    def SetState(a: int)
    def `SetState` as SetStateFromSum(a: int, b: int)
    def `SetState` as SetStateFromMyClass(s: MyClass)

    def `GetState` as GetState() -> int

    # The following two functions wrap the same C++ function, but in two
    # different flavors; One stores the state in the MyClass argument, the other
    # returns the state in a new MyClass object.
    def `GetState` as Store(a: MyClass)
    def `GetState` as StoreInNew() -> MyClass

```

There is an `import` statement at the top of the CLIF file. This is not a normal
Python `import` statement as we are not importing from a Python module; we are
actually importing C++ constructs that were CLIF-wrapped elsewhere. The header
file (`clif/examples/wrappod/python/wrappod_clif.h` in this example)
from which the wrapped constructs are imported was not written by a human, but
generated by CLIF when wrapping the dependent constructs. For this example, we
are importing the constructs (which is essentially the class `MyClass`) that
were wrapped in [this][wrappod] example.

To depend on the CLIF-generated header file, use the `clif_deps` attribute in
your BUILD file:

```bzl
py_clif_cc(
    name = "wrapfunc",
    srcs = ["wrapfunc.clif"],
    clif_deps = ["//clif/examples/wrappod/python:wrappod"],
    deps = ["//clif/examples/wrapfunc"],
)
```

The following `from` statement is a directive which tells CLIF that we are
wrapping C++ constructs defined in the specified header file (the file
`clif/examples/wrapfunc/wrapfunc.h` in this case).

As explained in the earlier [example][wrappod], the `namespace` directive tells
CLIF that the constructs being wrapped here are declared in the namespace
`clif_example::wrapfunc`.

Following the namespace directive are the declarations of the functions to be
wrapped and made available in Python.

### Wrapping Functions Taking No Arguments

Any function to be wrapped and made available in Python has to be declared with
a `def` statement. The syntax of this statement is similar to the function
header of a Python function definition. The first declaration in the above CLIF
file declares `ResetState`. This directs CLIF to wrap the C++ function
`ResetState` and make it available in Python with the same name `ResetState`. As
this function takes no arguments (and returns `void`), the argument list within
the parentheses is empty.

### Wrapping Functions Taking Arguments

The next function declared is `SetState`. Since this function takes a single
`int` argument, the argument list specifies this argument and its type. In
general, an argument has to be specified as follows:

```
<ARG_NAME>: <ARG_TYPE>
```

NOTE: `<ARG_NAME>` represents the Python name of the argument. Since argument
names are irrelevant in C++, they can be different from the ones listed in the
C++ source. You should choose names idiomatic in Python as they can be used as
keyword arguments.

The declaration of `SetState` directs CLIF to wrap the C++ function `SetState`
and make it available in Python also with the same name `SetState`.

### Function Overloading

The C++ header file, which contains the constructs that we want to wrap,
overloads the `SetState` function. Since Python does not support function
overloading, if we want to wrap overloaded C++ functions and make them available
in Python, we have to specify a different Python name for each of the overloaded
C++ functions and they all will be available in Python. The CLIF file above
declares two additional flavors of the `SetState` function, one taking two `int`
arguments and the other taking a `MyClass` argument, with Python names
`SetStateFromSum` and `SetStateFromMyClass` respectively. With this, all three
overloaded flavors of the C++ `SetState` function are now available in Python
with different names.

### Functions With Return Values

One flavor of the C++ function `GetState` returns an `int` value. We can wrap
such a function with CLIF by providing the return value type in the function
declaration as follows:

```
def <FUNC_NAME>(<ARG_LIST>) -> <RETURN_VALUE_TYPE>
```

The other flavor of C++ `GetState` actually takes a non-constant pointer to a
`MyClass` value. The intention here is that the state is actually _returned_ or
stored in the `MyClass` argument. Hence, to make this function available in
Python, one can wrap it in two flavors:

1. A function which takes a `MyClass` object as argument.
2. A function which takes no arguments but returns a new `MyClass` object.

The CLIF file above makes two functions, `Store` and `StoreInNew`, available in
Python corresponding to the two options above respectively.

In general, non-const pointers at the end of a C++
argument list can be treated either as arguments or as return values in Python.
If the C++ function already has a return value, then the Python function can be
made to return a tuple of values with the first element of tuple corresponding
to the actual C++ return value. The general syntax to declare a function which
returns a tuple of values is as follows:

```python
def <FUNC_NAME>(<ARG_LIST>) -> (<RET1_NAME>: <RET1_TYPE>, <RET2_NAME>: <RET2_TYPE>, ...)
```

### Wrapping Functions Returning/Receiving Callbacks

NOTE: The example, `callbacks`, used in this section lives in
[clif/examples/callbacks/](
../../examples/callbacks/)

With CLIF, one can wrap functions returning or receiving callbacks. When a
function receiving a callback argument is wrapped, it enables one to pass
Python callable objects as arguments to the wrapped function in Python.
Likewise, if a function returning a callable is wrapped, then the object
returned by calling the wrapped function in Python can be treated as a Python
callable.

NOTE: For constructs (functions/methods) involving callback types to be
wrappable with CLIF, the callback types should be overloads of the
`std::function` template class.

Consider the following C++ class and function definitions:

Look in the examples/callbacks/callbacks.h [file](../../examples/callbacks/callbacks.h).

The CLIF file wrapping the class `Data` and the functions `Get`, `Set` and
`GetCallback` is as follows:

Look in the examples/callbacks/python/callbacks.clif [file](../../examples/callbacks/python/callbacks.clif).

As can be seen in the above CLIF file, a callback parameter or a callback return
value, both are listed as one would list any normal parameter or a return
value. The syntax to convey that a particular parameter or a return value is a
callback, though very intuitive, is special; The general syntax to specify
a callback is as follows:

```
(PARAM_LIST) -> None | RETURN_TYPE
```
where `PARAM_LIST` is the list of parameters (and their types) that the
respective callback receives as arguments. It has the general form as follows:

```
([ARG1: ARG1_TYPE[, ARG2: ARG2_TYPE[, ...]]])
```

For a callback taking no arguments, the `PARAM_LIST` can be empty. The return
type should either be `None` or a concrete type.

The following unit test illustrates the usage of the above CLIF wrapping in
Python code.

Look in the examples/callbacks/python/callbacks_test.py [file](../../examples/callbacks/python/callbacks_test.py).

### Function with Default Values for Arguments

If desired, and if the C++ function declaration lists default values for its
arguments, then the function can be wrapped such that the same default values
reflect in the Python side as well. Consider the following C++ functions:

Look in the examples/wrapfunc/default_args.h [file](../../examples/wrapfunc/default_args.h).

The CLIF file wrapping the above functions is as follows:

Look in the examples/wrapfunc/python/default_args.clif [file](../../examples/wrapfunc/python/default_args.clif).

Let us first focus on the CLIF declaration of the function `Inc`. Its second
argument is _assigned_ a value of `default`. This indicates to CLIF that the
argument's default value, as specified in the C++ declaration, should carry over
into Python. The wrapped function `Inc` can then be called in Python without
the second argument. In such a case, the second argument takes the value `1`,
which is the default value as specified in its C++ declaration. The following
Python snippet illustrates this.

```python
assert Inc(5) == 6
assert Inc(5, 2) == 7
```

NOTE: It is an error to assign an argument to `default` if the C++ declaration
does not list a default value for that argument. On the other hand,
it is _not_ a requirement to assign arguments to `default` in the CLIF
declaration even if the C++ declaration lists default values. One should do so
only if the default value is relevant in Python as well. If such an argument is
not assigned to `default` in the CLIF declaration, then it will be like an
argument without a default value in Python.

Let us now turn our attention to the other function `Scale` in the above C++
example. Its C++ declaration lists default values for two of its arguments,
`ratio` and `offset`. If this were a normal Python function, one can omit
passing a value for the argument `ratio` while specifying an explicit value for
the argument `offset`. On the other hand, C++ does not allow one to skip
passing an argument while passing an explicit value for an argument later in the
declaration order. However, when the default value of an argument in the C++
declaration is a
[constexpr](http://en.cppreference.com/w/cpp/language/constexpr) of a
[fundamental type](http://en.cppreference.com/w/cpp/language/types), the CLIF
wrapped Python function will follow Python rules. With the wrapped `Scale`
function for example, one can omit the value of the argument `ratio` while
specifying the value of `offset`. This is illustrated in the following Python
snippet.

```python
assert Scale(5) == 10
assert Scale(5, offset=2) == 14  # passing a value for |ratio| is omitted
```

Currently, CLIF is unable to generate the default value if the value as
listed in the C++ declaration is not a `constexpr` or is not of a fundamental
type. Since C++ requires arguments (even if having default values) be passed in
the declaration order, we _can not_ omit such an argument value while specifying
a value for an argument occurring later in the declaration order even in Python.
This can be seen when using the wrapped `ScaleWithRatios` function:

```python
ScaleWithRatios(5, offset=2)  # Raises ValueError as a value for
                              # the |ratios| argument, which not
                              # of a fundamental type, is omitted.
```

### Post processing return values

C and C++ APIs often return a value indicating an error. It may be more Pythonic
for this to be an exception. To accomplish this, CLIF supports the concept of
post-processing return value filters. This saves you from needing to create
Python wrapper libraries for everything to make common C++ API idioms Pythonic.

Imagine this C++ API:

```cpp
// Returns False on error such as no such user.
bool get_names(uint64_t user_id, std::vector<absl::string_view>* names);
```

Rather than get a tuple in Python, you just want the list or an exception. Use a
Python post processor function to accomplish this in your .clif file via this
syntax:

```python
from clif.python.postproc import ValueErrorOnFalse

from "users.h":
  def get_names(user_id: int) -> (status: bool, names: list<str>):
    return ValueErrorOnFalse(...)
```

Now it returns a `List[str]` or raises an exception. Pythonic!

Remember that `.clif` files are not actual code, the `return` "statement" and
`...` are syntactic sugar to tell clif to invoke a given result post-processor.
CLIF will import the Python name and call it as a post-processor passing it all
of the return values as positional arguments. Whatever it returns becomes the
actual return value.

Some commonly needed post-processors have been provided in the above imported
library with CLIF. You can also
provide your own Python post-processor library.

## Naming Rules in CLIF Files {#naming_rules}

We have seen in previous sections that CLIF enables one to wrap named C++
constructs and expose them into Python as named Python constructs. Every C++
construct wrapped is exposed with a Python name. There are a few rules to follow
when declaring and using such Python names within a single CLIF file, and across
multiple CLIF files.

1. A Python name defining a construct should be unique to the scope in which the
construct is being defined. In CLIF, there are only two scopes: _module scope_
and _class scope_. Module scope is the top-level scope of a CLIF file, while
class scope is the scope within a class definition in a CLIF file.

2. A Python name, say to name a function argument type, can only be used after
a construct with that name has been previously defined. It could either be
defined in the same CLIF file where it is used, or in another CLIF wrapping
imported by the CLIF file.

3. Ambiguous names are resolved with full scope qualification using the '.'
(dot) notation. For example, if a class named `MyClass` is defined within
classes `OuterOne` and `OuterTwo`, then to specify the one in class `OuterOne`,
use the name `OuterOne.MyClass`.

4. Ambiguous names between different CLIF files are resolved with the help of
_import renaming_. The usual way to _import_ constructs wrapped in other CLIF
files is to list a `from <path_to_generated_header> import *` at the top of the
CLIF file. If the imported names clash with names in the current CLIF file, then
the imported _module_ should be renamed using this syntax:
`from <path_to_generated_header> import * as <renamed>`. Then, the imported
constructs can be used within the current file after prepending the scope
qualification prefix `<renamed>.`.

The above naming rules are illustrated in the declarations of the following
example CLIF file:

```python
from `/a/different/wrapping_clif.h` import * as other

from `/my/header/file.h`:
  namespace `my::header::file`:
    class OuterOne:
      class MyClass:
        pass

    class OuterTwo:
      class MyClass:
        pass

    # The two argument types are scope qualified. Likewise, the return type is
    # scope qualified with the renamed imported module.
    def MyFunction(c1: OuterOne.MyClass, c2: OuterTwo.MyClass) -> other.MyClass
```

## Wrapping Methods {#wrapmethod}

NOTE: The example, `wrapmethod`, used in this section lives in
[clif/examples/wrapmethod/](
../../examples/wrapmethod/).

Wrapping methods is very similar to wrapping functions but with one difference:
the method to be wrapped should take `self` as the first argument. Let us wrap
the class `ClassWithMethods` and its methods defined in `wrapmethod.h`.

Look in the examples/wrapmethod/wrapmethod.h [file](../../examples/wrapmethod/wrapmethod.h).

The CLIF wrapping for the above class and its methods is as follows:

Look in the examples/wrapmethod/python/wrapmethod.clif [file](../../examples/wrapmethod/python/wrapmethod.clif).

As can be seen above, the method wrappings are listed under the class
definition. Also, since they are methods, their first argument is `self` without
the type specified.

Notice that the C++ `Size` method is wrapped in two
different flavors, one exposing it as a method with name `Size` in Python as
well, and the other exposing it as a method with name `__len__` in Python. This
was done

1. to demonstrate that, as with functions, one can wrap methods also in multiple
flavors to expose them in Python with different names.

2. to show that C++ methods can be wrapped into special Python methods.

In the above CLIF example, the alternative wrapping of the C++ `Size` method
wraps it into the special method `__len__` in Python. This make the wrapping
more Pythonic as one can now get the size of the object using the Python built-
in function `len`:

```python
obj = wrapmethod.ClassWithMethods(10)
assert len(obj) == 10
```

See [this][specialmethods] for information more about wrapping C++ methods into
special Python methods.

### Wrapping Constructors

The above CLIF example also wraps one of the constructors for the C++ class
`ClassWithMethods` into a constructor in Python as well. As Python does not have
name overloading, we can have only one constructor for the wrapped Python class.
However, since the wrapped C++ class can have multiple constructors, CLIF
provides a way to wrap such constructors as well, but into static methods of the
containing class (**and not into class methods!**). The additional
_constructors_ are declared in CLIF with the `@add__init__` decorator. For
example, the other constructor of the class `ClassWithMethods` can be wrapped in
CLIF as follows:

```python
from "clif/examples/wrapmethod/wrapmethod.h":
  namespace `clif_example::wrapmethod`:
    class ClassWithMethods:
      ...
      # Wrapper for the constructor ClassWithMethods::ClassWithMethods(int, int)
      @add__init__
      def ConstructWithInitVal(self, s: int, v: int)
```

Notice that, even though the C++ constructor is wrapped into a static method of
the containing class, it still needs to be declared with `self` as the
first argument. The rest of the arguments should match the C++ constructor that
is being wrapped (the name of this static method need not match that of the C++
constructor however). Since this _constructor_ is wrapped into a static method,
one will have to call it in Python code as follows:

```python
obj = ClassWithMethods.ConstructWithInitVal(100, 2)
```

By Google
[convention](https://google.github.io/styleguide/cppguide.html#Implicit_Conversions)
, constructors that can be called with a single argument, except for copy and
move constructors, must be marked `explicit` in the class definition to avoid
unexpected implicit conversions. In the above example, C++ class
`ClassWithMethods` contains a constructor with a single argument and should be
marked as explicit in C++ class definition.

```c++
class ClassWithMethods {
  public:
    // Single argument constructors must be marked explicit.
    explicit ClassWithMethods(int size) : data_(size) { }
    ...
};
```

Without `explicit`, there could be implicit type conversions from `int` to
`ClassWithMethods` with the above single argument constructor. The C++ compiler
will always declare a copy constructor as a non-explicit public member of the
class if there is no user-defined copy/move constructor. Then CLIF would treat
`ClassWithMethods`'s implicitly-declared copy constructor as a valid candidate
while it's not, and report a multi match error. The same process could also
happen to move constructors if there exist.

#### Default Constructor

If a wrapped C++ class has a default constructor, and if one wants to expose it
on the Python side as a constructor, it need not be listed in the CLIF
file. CLIF _wraps_ it implicitly. The default C++ constructor gets invoked when
one instantiates a wrapped class as follows:

```python
obj = wrapped_module.WrappedClass() # Constructor with no args
```

even when the CLIF file does not list the default constructor (and, since this
is Python, CLIF should not define an `__init__` method at all).

NOTE: One _can_ list a wrapper for the default constructor in the CLIF file. It
is not an error, but is redundant.

### Wrapping Static Methods

A static method of a C++ class can be wrapped in two different ways:

1. Wrap as a function in the Python module scope.
2. Wrap as a class method of the Python class.

NOTE: Wrapping C++ static methods as functions in the module scope should be
preferred unless there is a good reason (for example, to avoid name collision,
or to wrap factory methods) to keep them in the class scope and expose them as
class methods.

#### Wrapping as Functions in the Module Scope

Wrapping a static C++ method can be done with the `staticmethods` statement.
The following snippet illustrates this
for the static method `GetStaticNumber` of the C++ class `ClassWithMethods` of
the above example:

```python
  staticmethods from `ClassWithMethods`:
    def GetStaticNumber() -> int
```

#### Wrapping as Class Methods

The syntax to wrap a static method of a C++ class as a class method of the
Python class is very similar to wrapping an instance method, except that,
instead of the `self` argument, the class method needs `cls` as the first
argument. Also, a class method declaration should be decorated with the
`@classmethod` decorator. The CLIF declaration which wraps the static method
`GetStaticNumber` of the above C++ class `ClassWithMethods` as class method is
as follows:

```python
    ...
    class ClassWithMethods:
      ...
      # Wrapper for static method ClassWithMethods::GetStaticNumber
      @classmethod
      def GetStaticNumber(cls) -> int
    ...
```

### Wrapping C++ Methods into Special Methods in Python {#specialmethods}

We have seen an example above wherein wrapping a C++ method into the special
method `__len__` on the Python side enables one to use the `len` built-in
function on the object. Similarly, CLIF provides a way to wrap getters and
setters into other special methods on the Python side so that one can use the
wrapped objects as sequences (this enables one to use the subscript operator
`[]` on the wrapped object). To wrap a class into one supporting the sequence
protocol on the Python side, one has to wrap the C++ element access getter and
setter methods with Python names `__getitem__` and `__setitem__` respectively.
Python uses the same `[item]` syntax for accessing sequences (eg. lists, tuples)
with the index as `item` and mappings (dicts) with a key as `item`. We need to
decorate the definitions of these methods with `@sequential` to indicate that
these methods are for using an index.

The CLIF declaration which wraps the C++ methods `Get` and `Set`
(of class `ClassWithMethods` from above) into the sequence protocol is as
follows:

```python
from "clif/examples/wrapmethod/wrapmethod.h":
  namespace `clif_example::wrapmethod`:
    class ClassWithMethods:
      ...

      # Wrap ClassWithMethods::Get as __getitem__ with sequence protocol
      @sequential
      def `Get` as __getitem__(self, i: int) -> int

      # Wrap ClassWithMethods::Set as __setitem__ with sequence protocol
      @sequential
      def `Set` as __setitem__(self, i: int, v: int)
```

Similar to `__getitem__` and `__setitem__`, one can also wrap a C++ method into
the special method `__delitem__` under the sequential protocol as follows:

```python
from "clif/examples/wrapmethod/wrapmethod.h":
  namespace `clif_example::wrapmethod`:
    class ClassWithMethods:
      ...

      # Wrap ClassWithMethods::Delete as __delitem__ with sequence protocol
      @sequential
      def `Delete` as __delitem__(self, i: int)
```

This will enable one to call the `del` built-in function on the sequences
elements as follows:

```python
obj = ClassWithMethods(10)
del obj[5]
assert len(obj) == 9
```

NOTE: `__setitem__` and `__delitem__` occupy the same slot, so defining only one
of them prevents calling the other from a base class. Just repeat the "missing"
definition in the derived class (as shown in
[clif/testing/python/slots.clif](
../testing/python/slots.clif)).

CLIF protects the C++ side from invalid indices. That is, if Python code
uses a bad index to access a sequence element (from an instance whose class
satisfies the sequence protocol), then an `IndexError` is raised even if the
backing C++ code does not provide such a protection. [This is not to imply that
C++ should/need not have checks. That should depend wholly on the C++ usage
contract.]

### Sequences are Iterable

When a CLIF wrapped class contains the special methods `__getitem__` under
the sequence protocol (i.e. using the `@sequential` decorator), and also the
method `__len__`, then instances of such a class are iterable in Python. That
is, with the wrappings for `__getitem__` and `__len__` added as above for
the class `ClassWithMethods`, one can now iterate over the elements of its
instance, for example in a `for` loop, as follows:

```python
obj = ClassWithMethods(10)
...
for i in obj:
  # do something
```

### Exposing Getter/Setter Methods as Properties

NOTE: The example used in this section lives in
[clif/examples/property/](
../../examples/property/).

We have previously seen CLIF's [unproperty][unproperty] feature where in data
members of a C++ class are exposed via setter/getter methods on the wrapped
class. CLIF also provides a way to do its inverse: expose C++ getter/setter
methods via a property (or attribute) of the wrapped class. This enables one to
expose C++ classes with a concise Pythonic API. Consider the following C++ class
definition:

Look in the examples/property/myoptions.h [file](../../examples/property/myoptions.h).

One can wrap the getter and setter methods of the class `MyClass` into instance
properties in Python as shown in the following CLIF file:

Look in the examples/property/python/myoptions.clif [file](../../examples/property/python/myoptions.clif).

The general syntax to list a class property (as a replacement for its C++ getter
and setter) is as follows:

```
<PROPERTY_NAME>: <PYTHON_TYPE> = property(<CPP_GETTER_NAME>[, <CPP_SETTER_NAME>])
```

- `PROPERTY_NAME` is the exposed name of the class property.
- `PYTHON_TYPE` is the name of the Python type of the property.
- `CPP_GETTER_NAME` is the name of the C++ getter method. It has to be quoted in
backticks.
- `CPP_SETTER_NAME` is the name of the C++ setter method. It has to be quoted in
backticks.

Providing a setter for a property is optional. If a setter is not specified
in the property declaration, then the property is not writable in Python. The
code snippet below illustrates the usage of the Python class wrapped in the
above CLIF file.

```python
opts = MyOptions('options')
opts.path = 'my/options/path'
opts.count = 10
opts_name = opts.name
opts.name = 'new_name' # This line will raise AttributeError as the attribute
                       # 'name' is not writable.
```

NOTE: Like the normal [fields][fields] exposed in to Python, the properties
exposed in the above fashion are also _returned_ by value.

## Inheritance

NOTE: The example used in this section lives in
[clif/examples/inheritance/](
../../examples/inheritance/).

### Wrapping Without Exposing Inheritance into Python

In many cases C++ inheritance is an implementation detail and should not be
visible to Python users.

If exposing the C++ inheritance hierarchy into Python is
not required, one can wrap only the relevant classes using CLIF and ignore
linking them with an inheritance relationship in Python. For example, consider
the following C++ class hierarchy:

Look in the examples/inheritance/hidden_base.h [file](../../examples/inheritance/hidden_base.h).

If exposing the class `Base` into Python is not necessary, one can wrap only the
derived class `Derived` as follows:

Look in the examples/inheritance/python/hidden_base.clif [file](../../examples/inheritance/python/hidden_base.clif).

Notice that, since the Python class `Derived` is not inherited from the class
`Base` (in fact, Python is not aware of the existence of a base class), one will
have to list the wrappings for the base class methods under the derived class
wrapping (if they should be made available in Python at all).

### Exposing Inheritance Relationship into Python

Wrapping C++ class inheritance hierarchy into Python class hierarchy using CLIF
is straightforward.

NOTE: CLIF does not support multiple inheritance on the Python side. The C++
side can use multiple inheritance as suitable (and as allowed).

Let us wrap the following C++ class hierarchy:

Look in the examples/inheritance/inheritance.h [file](../../examples/inheritance/inheritance.h).

The CLIF-wrapping for the above class hierarchy is as follows:

Look in the examples/inheritance/python/inheritance.clif [file](../../examples/inheritance/python/inheritance.clif).

The wrapping for the base class `Base` is like wrapping any other class (as
described [here][wrappod] and [here][wrapmethod]). The wrapping for the
derived classes `Derived1` and `Derived2` uses the general Python syntax of
specifying a base class in the class definition header:

```
class <DERIVED_CLASS_NAME>(<BASE_CLASS_NAME>):
```

Both, `DERIVED_CLASS_NAME` and `BASE_CLASS_NAME`, can be specified with
different Python names as well (as described in [renaming][renaming]).

Following the class declaration header are the method declarations as usual.
Declaring a class as inheriting another class in CLIF guarantees that all the
methods declared in the CLIF wrapping of the base class are inherited by the
derived class. Notice that, for the class `Derived2`, we did not list any
methods, but just used the `pass` statement. This was done to illustrate that,
when appropriate, one can make the derived class _empty_ (as in, at the syntax
level) and make only the inherited members available.

## Overriding Virtual Methods in Python

A very useful feature that CLIF provides is overriding virtual methods in
Python. This enables one to provide implementations for abstract C++ classes in
Python and pass them over to C++ for further computation.

Note: The example `operation` used in this section lives in
[clif/examples/inheritance/](
../../examples/inheritance/).

We will use a fairly simple example to illustrate this feature of overriding
virtual methods. Consider the following abstract C++ class, and a function which
takes a pointer to an instance of that class as argument:

Look in the examples/inheritance/operation.h [file](../../examples/inheritance/operation.h).

The CLIF wrapping for the above class is as follows:

Look in the examples/inheritance/python/operation.clif [file](../../examples/inheritance/python/operation.clif).

Most of the CLIF wrapping above looks like any normal CLIF wrapping of a C++
class and function. The key difference however is the decorator `@virtual` used
to decorate the virtual method `Run`. This is a directive to CLIF informing it
that a concrete class derived from class `Operation` in Python will override it.
For example, one can override the `Run` method in a derived Python class as
follows:

```python
class Add(operation.Operation):
  def __init__(self, a, b):
    operation.Operation.__init__(self)
    self.a = a
    self.b = b

  def Run(self):
    return self.a + self.b
```

An instance of the class `Add` can be passed to the wrapped function `Perform`,
which in turn calls into the C++ function `Perform`. When the C++ `Perform`
invokes the `Run` method on the input object, its Python implementation is
invoked. This is illustrated in the following snippet:

```python
a = Add(120, 3)
r = operation.Perform(a)
assert r == 123
```

NOTE: It is an error to decorate the CLIF declaration of a non-virtual method
with `@virtual`.

NOTE: Do not decorate C++ virtual methods with `@virtual` unless you need to
(re)implement them in Python.

NOTE: When a virtual function returns an object from Python, it follows the
usual Python convention and returns a new reference.

## Wrapping C++ Templates

NOTE: The example, `templates`, used in this section lives in
[clif/examples/templates/](
../../examples/templates/).

NOTE: CLIF only supports wrapping template instantiations. This does not mean
that the C++ code should have explicit instantiations declared. Rather that,
CLIF does not provide a way to define classes in a templatized manner.

### Wrapping Template Classes

Wrapping a template instantiation should be done using the normal way of
wrapping classes and methods. The C++ name in the CLIF declaration should
include all the non-default template parameters of the C++ template. The Python
name _must_ be provided. Consider the following C++ template definition:

Look in the examples/templates/templates.h [file](../../examples/templates/templates.h).

The CLIF wrapping for the above class in two different flavors is as follows:

Look in the examples/templates/python/templates.clif [file](../../examples/templates/python/templates.clif).

The first flavor in the above CLIF file wraps the template instantiation
`MyClass<int, string>`, and the second flavor wraps the template instantiation
`MyClass<string, string>`. Notice that, one will need to declare the
methods, attributes and properties that they want to expose into Python
explicitly and separately for each flavor.

### Wrapping Template Functions

NOTE: CLIF only supports wrapping template functions whose template arguments
can be deduced from the function's argument types.

When wrapping template functions, unlike with wrapping template classes, one
should __not__ list the template arguments in the C++ name. Apart from that, it
is very similar to wrapping any normal function. This is illustrated in the
above CLIF file which wraps the C++ template function `MyAdd` into two flavors
`MyAddInt` and `MyAddFloat`.

## Wrapping Protocol Buffers {#protos}

NOTE: The example `wrap_protos` used in this section lives in
[clif/examples/wrap_protos/](
../../examples/wrap_protos/).

Wrapping protocol buffers with CLIF requires setting up certain build rules and
targets following a certain pattern. There are no constructs to wrap them
explicitly in a CLIF file. Consider an example proto definition as follows:

Look in the examples/wrap_protos/protos/sample.proto [file](../../examples/wrap_protos/protos/sample.proto).

NOTE: Only proto2 (and `cc_api_version=2`) is currently supported by CLIF.
If the proto file or build rule
has `cc_api_version=1`, then protoc generates a `.pb.h` file incompatible with
CLIF (nested message typedefs are not generated). Under certain conditions,
the `proto_library` rule falls back to proto1 even if `cc_api_version=2` is
specified in the rule. Such cases are also not supported by CLIF.

To see how the CLIF wrappings for the above proto definitions can be used along
with CLIF-wrapped Python code, let us consider C++ code which operates with the
proto `MyMessage` as follows:

Look in the examples/wrap_protos/wrap_protos.h [file](../../examples/wrap_protos/wrap_protos.h).

Make special note of two constructs from the above C++ header: The function
`DefaultInitMyMessage` which takes a pointer to the proto `MyMessage` as
argument, and the method `GetMyMessage` which returns a pointer to the proto
`MyMessage`. With these in mind, let us look at the following CLIF file which
wraps the C++ class `ProtoManager` and the function `DefaultInitMyMessage` as
follows:

Look in the examples/wrap_protos/python/wrap_protos.clif [file](../../examples/wrap_protos/python/wrap_protos.clif).

Since we are using the CLIF wrapped protobuf types in our CLIF file, we have to
_import_ them using the `from` statement in a manner similar to importing CLIF
wrapped constructs from other CLIF modules. As before, the name of the header
file (without the `.h` extension), from which the CLIF wrappings should be
imported, should match the name of the build target which builds the CLIF
wrappings. This import statement makes the protobuf message names available for
use in the CLIF file. Nested messages and enums should be specified using the
'`.`' notation.

NOTE: If a protobuf message name conflicts with another name used or defined in
a CLIF file, then the protobuf wrapping should be imported using the
`from <proto_wrapping_header_file> import * as <local_name>` syntax. The message
name can then be used in the CLIF file with the `<local_name>.` prefix.

### Passing protobufs by value

A very important point to keep in mind is that, unlike instances of wrapped
class/struct types, when protobuf messages cross the language boundary (C++ to
Python, or Python to C++), the receiving side receives the language-native
version of the message. Since C++ and Python representation of the protos
differ, changes made to a message are local to the language the changes are made
from. Hence, in the above example, even though the wrapped
`DefaultInitMyMessage` takes a pointer to the proto `MyMessage`, changes made to
it on the C++ side do not get reflected on the Python side. Similarly, even
though the method `GetMyMessage` returns a non-const pointer, changes made to
the returned protobuf on the Python side do not get reflected on the C++ side.
This is illustrated by the following test:

Look in the examples/wrap_protos/python/wrap_protos_test.py [file](../../examples/wrap_protos/python/wrap_protos_test.py).

## Providing a Python Wrapper Layer

(More details coming ...)

The raw CLIF wrappings might not be Pythonic enough. For example, a C++ method
could be silent or just crash on invalid input arguments. When such a method is
wrapped into Python, instead of making this raw CLIF wrapping as a user facing
API, a good approach would be to provide a different layer which is actually the
user facing API instead of the raw CLIF wrapping. This helps in two ways:

1. Isolate Python users from C++ API changes.
2. Provide a more Pythonic API, instead of possibly a non-Pythonic one.

[wrappod]: #wrapping_pod_data_types
[wrapmethod]: #wrapping_methods
[specialmethods]: #wrapping_c_methods_into_special_methods_in_python
[unproperty]: #unproperty_exposing_c_fields_via_settersgetters_in_python
[renaming]: #renaming_a_c_api_for_use_in_python
[protos]: #Wrapping_Protocol_Buffers
[naming_rules]: #Naming_Rules_in_Clif_Files

[^1]: "plain old data", i.e. [passive data
    structures](https://en.wikipedia.org/wiki/Passive_data_structure) like
    records.
