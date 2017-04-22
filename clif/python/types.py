# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Declare various CLIF-generated types.

Each type describes a C++ API for that type and generates a C++
header (GenHeader) and implementation (GenConverters) for that API.
"""
import re

I = '  '


def _ClifUse(cname, pyname):
  return '// CLIF use `%s` as %s' % (cname, pyname)


# Export sort key function for easy access.
def Order(typedef):
  return Namespace(typedef) + '.' + typedef.pyname


def Namespace(typedef):
  return typedef.namespace or ''  # Collapse None -> ''.


class TypeDef(object):
  """C++ class as some Python object."""
  _genclifuse = False  # Generate '// CLIF use' in the header file.

  def __init__(self, c, py='', ns=''):
    self.cname = c
    self.pyname = py
    self.namespace = ns

  def GenHeader(self):
    if self._genclifuse:
      yield _ClifUse(self.cname, self.pyname)
    else:
      yield '// '+(self.pyname or self.cname)
    yield 'bool Clif_PyObjAs(PyObject* input, %s* output);' % self.cname
    yield 'PyObject* Clif_PyObjFrom(const %s&, py::PostConv);' % self.cname

  def GenConverters(self, wrapper_namespace, py3output):  # pylint: disable=unused-argument
    raise NotImplementedError()


class ClassType(TypeDef):
  """C++ class as Python type."""

  def __init__(self, cpp_name, pypath, wclass, wtype, wnamespace,
               can_copy, can_destruct, down_cast, virtual, ns=None):
    """Register a new class.

    Args:
      cpp_name: C++ FQ class name (module::ns::FooCpp)
      pypath: Python qualified name (Nested.Foo)
      wclass: wrapper class (module_wrap::pyFoo::wrapper)
      wtype: wrapper type (...+_Type)
      wnamespace: wrapper ns (module_wrap::pyFoo::)
      can_copy: True if can copy C++ class
      can_destruct: True if C++ class has a public dtor
      down_cast: None of FQ C++ [replacement] class (another:FooCpp)
      virtual: True if class has @virtual method(s) and needs a redirector
      ns: namespace where class defined
    """
    TypeDef.__init__(self, cpp_name, pypath, ns)
    self.wrapper_obj = wclass
    self.wrapper_type = wtype
    self.wrapper_ns = wnamespace
    self.down_cast = down_cast
    self.virtual = virtual
    # Argument list for Clif_PyObjFrom().
    self._from = []  # [C++ Argument, Can get NULL, Init expression]
    if not virtual:
      self._from = [
          ('%s*', True, '::clif::SharedPtr<%s>(c, ::clif::UnOwnedResource());')]
      if can_destruct:
        self._from.extend([
          # pylint: disable=bad-continuation
          ('std::unique_ptr<%s>', True, '::clif::SharedPtr<%s>(std::move(c));'),
          ('std::shared_ptr<%s>', True, '::clif::SharedPtr<%s>(c);')])
      if can_copy:
        self._from.append(
            ('const %s&', False, '::clif::MakeShared<%s>(c);'))
      else:
        # Explicitly delete signatures that do pass-by-value (set ptr to None).
        self._from.extend([
            ('const %s*', None, ''),
            ('const %s&', None, '')])
    # Argument list for Clif_PyObjAs().
    self._as = [  # [C++ Argument, prefix, postfix]
        ('%s*', '', ''),
        ('std::shared_ptr<%s>', '::clif::MakeStdShared(', ', cpp)')]
    if can_destruct:
      self._as.append(('std::unique_ptr<%s>', '', ''))
    if can_copy and not virtual:
      self._as.extend([
          ('%s', '*', ''),
          ('::gtl::optional<%s>', '*', '')])
    if down_cast:
      self._as.append((down_cast, '', ''))

  def GenHeader(self):
    yield _ClifUse(self.cname, self.pyname)
    for arg, _, _ in self._as:
      yield 'bool Clif_PyObjAs(PyObject* input, %s* output);' % (
          arg % self.cname if '%s' in arg else arg)
    for arg, ptr, _ in self._from:
      yield 'PyObject* Clif_PyObjFrom(%s, py::PostConv)%s;' % (
          arg % self.cname, ' = delete' if ptr is None else '')
    if self.down_cast:
      yield 'PyObject* Clif_PyObjFrom(%s&&, py::PostConv);' % self.down_cast

  def GenConverters(self, ns, unused_py3=False):
    """Generate Clif_PyObjAs() and Clif_PyObjFrom() definitions."""
    pytype = ns+'::'+self.wrapper_type
    yield ''
    yield '// %s to/from %s conversion' % (self.pyname, self.cname)
    pyname = ns+'::'+self.wrapper_obj
    shared = 'reinterpret_cast<%s*>(py)->cpp' % pyname
    # Python -> C++
    for arg, ptr, get in self._as:
      yield ''
      if '%s' in arg:
        yield 'bool Clif_PyObjAs(PyObject* py, %s* c) {' % (arg % self.cname)
        yield I+'assert(c != nullptr);'
        if arg.endswith('*'):
          yield I+'if (Py_None == py) {'
          yield I+I+'*c = nullptr;'
          yield I+I+'return true;'
          yield I+'}'
        yield I+'%s* cpp = %s::%sThisPtr(py);' % (self.cname,
                                                  ns, self.wrapper_ns)
        yield I+'if (cpp == nullptr) return false;'
        if '%s' in ptr: ptr %= self.cname
        if arg == 'std::unique_ptr<%s>':
          yield I+'if (!%s.Detach()) {' % shared
          yield I+I+('PyErr_SetString(PyExc_ValueError, '
                     '"Cannot convert %s instance to std::unique_ptr.");' %
                     self.pyname)
          yield I+I+'return false;'
          yield I+'}'
          yield I+'c->reset(cpp);'
        else:
          c = shared if arg == 'std::shared_ptr<%s>' else 'cpp'
          yield I+'*c = %s%s%s;' % (ptr, c, get)
        yield I+'return true;'
      else:
        yield 'bool Clif_PyObjAs(PyObject* py, %s* c) {' % arg
        yield I+'assert(c != nullptr);'
        yield I+'return Clif_PyObjAs(py, static_cast<%s*>(c));' % self.cname
      yield '}'
    # C++ -> Python
    for arg, ptr, init in self._from:
      if ptr is None: continue  # The overload =deleted in header file.
      yield ''
      yield 'PyObject* Clif_PyObjFrom(%s c, py::PostConv unused) {' % (
          arg % self.cname)
      if ptr:
        yield I+'if (c == nullptr) Py_RETURN_NONE;'
      yield I+'PyObject* py = PyType_GenericNew(&%s, NULL, NULL);' % pytype
      cname = ns+'::'+self.virtual if self.virtual else self.cname
      init %= (cname,) * init.count('%s')
      yield I+shared+' = '+init
      if self.virtual:
        yield I+shared+'->::clif::PyObj::Init(py);'
      yield I+'return py;'
      yield '}'
    if self.down_cast:
      yield ''
      yield ('PyObject* Clif_PyObjFrom(%s&& c, py::PostConv pc) {'
             % self.down_cast)
      yield I+('return Clif_PyObjFrom(std::move(static_cast<%s&&>(c)), pc);'
               % self.cname)
      yield '}'


class EnumType(TypeDef):
  """C++ enum and enum class as Python enum-derived object."""
  _genclifuse = True

  def __init__(self, cpp_name, pyname, pytype, wname, ns=None):
    # args like (ns::FooCpp, X.Y.Foo, Enum/IntEnum, X::Y::_Foo)
    TypeDef.__init__(self, cpp_name, pyname, ns)
    self.wrapper_type = pytype
    self.wrapper_name = wname

  def CreateEnum(self, ns, wname, varname, items, py3=False):
    """Generate a function to create Enum-derived class and a cache var."""
    yield '// Create Python Enum object (cached in %s) for %s' % (varname,
                                                                  self.cname)
    yield 'static PyObject* %s() {' % wname
    yield I+('PyObject *py, *py_enum_class{}, *names = PyTuple_New(%d);'
             % len(items))
    yield I+'if (names == nullptr) return nullptr;'
    for i, pair in enumerate(items):
      yield I+'if ((py = Py_BuildValue("(NN)", %s, %s)' % pair
      yield I+I+I+') == nullptr) goto err;'
      yield I+'PyTuple_SET_ITEM(names, %d, py);' % i
    if py3:
      yield I+'py = PyUnicode_FromString("%s");' % self.pyname
    else:
      yield I+'py = PyString_FromString("%s");' % self.pyname
    yield I+('py_enum_class = PyObject_CallFunctionObjArgs(%s::_%s, py, names, '
             'nullptr);' % (ns, self.wrapper_type))
    yield I+'Py_DECREF(py);'
    yield 'err:'
    yield I+'Py_DECREF(names);'
    yield I+'return py_enum_class;'
    yield '}'
    yield 'static PyObject* %s{};  // set by above func in Init()' % varname

  def GenConverters(self, ns, unused_py3=False):
    """Generate Clif_PyObjAs() and Clif_PyObjFrom() definitions."""
    wname = ns + '::' + self.wrapper_name
    yield ''
    yield '// %s:%s to/from enum %s conversion' % (
        self.pyname, self.wrapper_type, self.cname)
    yield ''
    yield 'bool Clif_PyObjAs(PyObject* py, %s* c) {' % self.cname
    yield I+'assert(c != nullptr);'
    yield I+'if (!PyObject_IsInstance(py, %s)) {' % wname
    yield I+I+('PyErr_Format(PyExc_TypeError, "expecting enum {}, got %s", '
               'ClassName(py));').format(self.pyname)
    yield I+I+'return false;'
    yield I+'}'
    yield I+EnumIntType(self.cname)+' v;'
    yield I+'PyObject* value = PyObject_GetAttrString(py, "value");'
    yield I+'if (value == nullptr || !Clif_PyObjAs(value, &v)) return false;'
    yield I+'Py_DECREF(value);'
    yield I+'*c = %s;' % AsType(self.cname, 'v')
    yield I+'return true;'
    yield '}'
    yield ''
    yield 'PyObject* Clif_PyObjFrom(const %s& c, py::PostConv) {' % self.cname
    yield I+'return PyObject_CallFunctionObjArgs(%s, PyInt_FromLong(' % wname
    yield I+I+I+AsType(EnumIntType(self.cname), 'c')+'), nullptr);'
    yield '}'


class ProtoType(TypeDef):
  """C++ proto2 Message as Python proto."""
  _genclifuse = True
  # TODO: Consider removing generated proto conversions in favor of
  # generic template using protodb.

  def __init__(self, cpp_name, pyname, pymodule, ns=None):
    # cname       c::MessageName
    # pyname      Possibly.Nested.MessageName
    # pymodule    full.path.to.proto_pb2
    TypeDef.__init__(self, cpp_name, pyname, ns)
    self.module = pymodule

  def GenHeader(self):
    for s in TypeDef.GenHeader(self): yield s  # pylint: disable=multiple-statements
    yield 'bool Clif_PyObjAs(PyObject*, std::unique_ptr<%s>*);' % self.cname
    # TODO: Add As(self.cname+'**', ...) to avoid proto copying.

  def GenConverters(self, unused_ns='', unused_py3=False):
    """Create convertors for C++ proto to/from Python protobuf."""
    top_name, _, el_name = self.pyname.partition('.')
    import_name = self.module + '.' + top_name
    ctype = self.cname
    yield ''
    yield '// %s to/from %s conversion' % (self.pyname, ctype)
    yield ''
    yield 'bool Clif_PyObjAs(PyObject* py, %s* c) {' % ctype
    yield I+'assert(c != nullptr);'
    yield I+'PyObject* type = ImportFQName("%s");' % import_name
    yield I+('if (!::clif::proto::TypeCheck(py, type, "%s", "%s"))'
             ' return false;' % (el_name, self.pyname))
    # Use underlying C++ protocol message pointer if available.
    yield I+'if (const proto2::Message* cpb = ::clif::proto::GetCProto(py)) {'
    yield I+I+'c->CopyFrom(*cpb);'
    yield I+I+'return true;'
    yield I+'}'
    yield I+'PyObject* ser = ::clif::proto::Serialize(py);'
    yield I+'if (ser == nullptr) return false;'
    yield I+('bool ok = c->ParsePartialFromArray('
             'PyBytes_AS_STRING(ser), PyBytes_GET_SIZE(ser));')
    yield I+'Py_DECREF(ser);'
    yield I+('if (!ok) PyErr_SetString(PyExc_ValueError, "Serialized bytes '
             'can\'t be parsed into C++ proto");')
    yield I+'return ok;'
    yield '}'
    yield ''
    yield 'bool Clif_PyObjAs(PyObject* py, std::unique_ptr<%s>* c) {' % ctype
    yield I+'assert(c != nullptr);'
    yield I+'if (!*c) c->reset(new %s);' % ctype
    yield I+'return Clif_PyObjAs(py, c->get());'
    yield '}'
    yield ''
    yield 'PyObject* Clif_PyObjFrom(const %s& c, py::PostConv) {' % ctype
    yield I+'PyObject* type = ImportFQName("%s");' % import_name
    yield I+'return ::clif::proto::PyProtoFrom(&c, type, "%s");' % el_name
    yield '}'


class ProtoEnumType(TypeDef):
  """C++ proto Enum as int as Python int."""

  def GenHeader(self):
    yield _ClifUse(self.cname, self.pyname)
    yield 'bool Clif_PyObjAs(PyObject* input, %s* output);' % self.cname
    yield 'PyObject* Clif_PyObjFrom(%s, py::PostConv);' % self.cname

  def GenConverters(self, unused_ns='', unused_py3=False):
    yield ''
    yield '// %s to/from enum %s conversion' % (self.pyname, self.cname)
    yield 'bool Clif_PyObjAs(PyObject* py, %s* c) {' % self.cname
    yield I+'assert(c != nullptr);'
    yield I+'int v;'
    yield I+'if (!Clif_PyObjAs(py, &v)) return false;'
    yield I+'*c = static_cast<%s>(v);' % self.cname
    yield I+'return true;'
    yield '}'
    yield 'PyObject* Clif_PyObjFrom(%s c, py::PostConv pc) {' % self.cname
    yield I+'return Clif_PyObjFrom(static_cast<int>(c), pc);'
    yield '}'


class CallableType(TypeDef):
  """C++ std::function<> as Python lambda."""

  def __init__(self, ctype, pytype, defname, ns=None):
    # args like (func<int ()>, lambda()->int, X::Y::cfunc_def)
    TypeDef.__init__(self, ctype, pytype, ns)
    self.funcdef = defname

  def GenHeader(self):
    yield '// '+(self.pyname or self.cname)
    yield 'PyObject* Clif_PyObjFrom(%s, py::PostConv);' % self.cname

  def GenConverters(self, ns, unused_py3=False):
    """Generate a Clif_PyObjFrom(std::function<>) converter."""
    yield ''
    yield '// Create a Python function that calls %s cfunction.' % self.cname
    yield 'PyObject* Clif_PyObjFrom(%s cfunction, py::PostConv) {' % self.cname
    yield I+'PyObject* f = FunctionCapsule(cfunction);'
    yield I+'if (f == nullptr) return nullptr;'
    yield I+'PyObject* py = PyCFunction_New(&%s::%s, f);' % (ns, self.funcdef)
    yield I+'Py_DECREF(f);'
    yield I+'return py;'
    yield '}'


class CapsuleType(TypeDef):
  """C++ borrowed raw pointer as Python capsule."""

  def GenHeader(self):
    # We're using trailing '*' to distinguish capsule type in included files.
    # Space is needed for matcher to string compare with C++ return type
    yield _ClifUse(self.cname+' *', self.pyname)
    yield 'bool Clif_PyObjAs(PyObject* input, %s** output);' % self.cname
    yield 'PyObject* Clif_PyObjFrom(const %s*, py::PostConv);' % self.cname

  def GenConverters(self, unused_ns='', unused_py3=False):
    """Generate a Clif_PyObjFrom(Foo*) converter."""
    yield ''
    yield '// %s to/from %s conversion' % (self.pyname, self.cname)
    yield ''
    yield 'bool Clif_PyObjAs(PyObject* py, %s** c) {' % self.cname
    yield I+'assert(c != nullptr);'
    yield I+'if (Py_None == py) {'
    yield I+I+'*c = nullptr;'
    yield I+I+'return true;'
    yield I+'}'
    yield I+'if (PyCapsule_CheckExact(py)) {'
    yield I+I+'void* p = PyCapsule_GetPointer(py, C("%s"));' % self.cname
    yield I+I+'bool ok = PyErr_Occurred() == nullptr;'
    yield I+I+'if (ok) *c = %s;' % AsType(self.cname + '*', 'p')
    yield I+I+'return ok;'
    yield I+'}'
    for s in _GenBaseCapsule(self.cname):
      yield s
    yield I+('PyErr_Format(PyExc_TypeError, "expecting {} capsule, got %s %s", '
             'ClassName(py), ClassType(py));').format(self.pyname)
    yield I+'return false;'
    yield '}'
    yield ''
    yield 'PyObject* Clif_PyObjFrom(const %s* c, py::PostConv) {' % self.cname
    yield I+'if (c == nullptr) Py_RETURN_NONE;'
    yield I+'return PyCapsule_New((void*)c, C("%s"), nullptr);' % self.cname
    yield '}'


def GenThisPointerFunc(cname, w='wrapper', final=False):
  """Generate "to this*" conversion (inside wrapper namespace).

  Args:
    cname: FQ class name (::multiday::Metric)
    w: pyext.Context.wrapper_class_name
    final: generate version for a final class wrapper
  Yields:
    ThisPtr() function source
  """
  t = w+'_Type'
  return_this_cpp = ('return ::clif::python::Get(reinterpret_cast<%s*>'
                     '(py)->cpp);' % w)
  yield ''
  yield 'static %s* ThisPtr(PyObject* py) {' % cname
  yield I+'if (Py_TYPE(py) == &%s) {' % t
  yield I+I+return_this_cpp
  yield I+'}'
  if final:
    _I=''  # pylint: disable=bad-whitespace,invalid-name
  else:
    # self is derived, try self.as_Base(), where Base is this class.
    for s in _GenBaseCapsule(cname, retptr=True):
      yield s
    # as_Base returned an error / wrong capsule
    yield I+'if (PyObject_IsInstance(py, %s)) {' % AsPyObj(t)
    yield I+I+'if (!base) {'  # base set in _GenBaseCapsule
    yield I+I+I+'PyErr_Clear();'
    yield I+I+I+return_this_cpp
    yield I+I+'}'
    yield I+I+('PyErr_Format(PyExc_ValueError, "can\'t convert %s %s to {}*", '
               'ClassName(py), ClassType(py));').format(cname)
    yield I+'} else {'
    _I=I  # pylint: disable=bad-whitespace,invalid-name
  yield _I+I+('PyErr_Format(PyExc_TypeError, "expecting %s instance, got %s %s"'
              ', {}.tp_name, ClassName(py), ClassType(py));'.format(t))
  if not final:
    yield I+'}'
  yield I+'return nullptr;'
  yield '}'


def _GenBaseCapsule(cname, retptr=False):
  """Generates snippet for checking as_BASE() call."""
  # Uses var naming convetion:
  # - from CapsuleType.GenConverters to set *c result (unless retptr set),
  # - from -/- and GenThisPointerFunc to use 'py' argument and 'base' object.
  yield I+('PyObject* base = PyObject_CallMethod(py, C("as_%s"), nullptr);'
           % Mangle(cname))
  yield I+'if (base) {'
  yield I+I+'if (PyCapsule_CheckExact(base)) {'
  yield I+I+I+'void* p = PyCapsule_GetPointer(base, C("%s"));' % cname
  yield I+I+I+'if (!PyErr_Occurred()) {'
  yield I+I+I+I+'%s* c = %s;' % (cname if retptr else '',
                                 AsType(cname + '*', 'p'))
  yield I+I+I+I+'Py_DECREF(base);'
  yield I+I+I+I+'return %s;' % ('c' if retptr else 'true')
  yield I+I+I+'}'
  yield I+I+'}'
  yield I+I+'Py_DECREF(base);'
  yield I+'}'


def EnumIntType(enum):
  return 'typename std::underlying_type<%s>::type' % enum


def Mangle(cname):
  """Transorm canonical LLVM type output to a valid Python id."""
  # Mangle does not make unique id, so A::B and A_B are the same.
  # It's intended to be used inside one class/namespace where collisions
  # should not happen.
  c = (cname.strip(' :>')
       .replace('::', '_')
       .replace('<', '_')
       .replace(', ', '_')
       .replace('*', '_ptr')
       .replace('&&', '_rref')
       .replace('&', '_ref')
       .replace(' ', '')
      )
  return '_'.join(re.split(r'[<>, ]', c))


def AsType(t, v):
  return 'static_cast<%s>(%s)' % (t, v)


def AsPyObj(s):
  return 'reinterpret_cast<PyObject*>(&%s)' % s
