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
FIND_CPP_CHAR_LITERAL = re.compile(r"'(\\(?:"
                                   '[0-7]{1,3}|'  # octal escapes
                                   'x[0-9A-Fa-f]{2}|'  # hexadecimal escapes
                                   'u[0-9]{4}|'  # short unicode escapes
                                   'U[0-9]{8}|'  # long unicode escapes
                                   r"[abfnrtv'\"\\]"  # ASCII escapes
                                   r")|.)'")


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

  def GenConverters(self, wrapper_namespace):
    del wrapper_namespace  # unused
    raise NotImplementedError()


class ClassType(TypeDef):
  """C++ class as Python type."""

  def __init__(self, cpp_name, pypath, wclass, wtype, wnamespace,
               can_copy, can_move, can_destruct, virtual, ns=None):
    """Register a new class.

    Args:
      cpp_name: C++ FQ class name (module::ns::FooCpp)
      pypath: Python qualified name (Nested.Foo)
      wclass: wrapper class (module_wrap::pyFoo::wrapper)
      wtype: wrapper type (...+_Type)
      wnamespace: wrapper ns (module_wrap::pyFoo::)
      can_copy: True if can copy the non-abstract C++ class
      can_move: True if can move the non-abstract C++ class
      can_destruct: True if C++ class has a public dtor
      virtual: True if class has @virtual method(s) and needs a redirector
      ns: namespace where class defined
    """
    TypeDef.__init__(self, cpp_name, pypath, ns)
    self.wrapper_obj = wclass
    self.wrapper_type = wtype
    self.wrapper_ns = wnamespace
    self.can_move = can_move
    self.virtual = virtual
    # Argument list for Clif_PyObjFrom().
    # Generate the conversion function for movable but uncopyable classes
    # in the form of:
    #   a. PyObject* Clif_PyObjFrom(UncopyableButMovableClass&& c,
    #                            py::PostConv unused);
    # Keep the conversion function for copyable classes in the form of:
    #   b. PyObject* Clif_PyObjFrom(const CopyableClass& c,
    #                             py::PostConv unused);
    #
    # 1. For movable but uncopyable C++ objects, conversion
    # function (b) is marked as delete in the generated code to avoid
    # copying an uncopyable object. C++ does not need to keep a copy of the
    # returned object. We support this condition by moving the object and
    # shifting object ownership to Python.
    #
    # 2. For copyable and movable C++ objects, we would generate both conversion
    # function (a) and (b) and let the compiler choose the rigth one to invoke.
    #
    # 3. Uncopyable and unmovable C++ objects are prohibited.
    self._from = []  # [C++ Argument, Can get NULL, Init expression]
    if not virtual:
      self._from = [
          ('%s*', True, '::clif::Instance<%s>(c, ::clif::UnOwnedResource());'),
          ('std::shared_ptr<%s>', True, '::clif::Instance<%s>(c);')]
      if can_destruct:
        self._from.append((
            'std::unique_ptr<%s>', True, '::clif::Instance<%s>(std::move(c));'))
        if can_move: self._from.append(
            ('%s&&', False, '::clif::MakeShared<%s>(std::move(c));'))
      if can_copy:
        self._from.extend([
            ('const %s&', False, '::clif::MakeShared<%s>(c);'),
            ('const %s*', True, '::clif::MakeShared<%s>(*c);')])
      else:
        # Explicitly delete signatures that do pass-by-value (set ptr to None).
        self._from.extend([
            ('const %s*', None, ''),
            ('const %s&', None, '')])
    # Argument list for Clif_PyObjAs().
    self._as = [  # [C++ Argument, ptr_deref]
        ('%s*', ''),
        ('std::shared_ptr<%s>', '',)]
    if can_destruct:
      self._as.append(('std::unique_ptr<%s>', ''))
    if can_copy and not virtual:
      self._as.append(('%s', '*'))

  def GenHeader(self):
    yield _ClifUse(self.cname, self.pyname)
    for arg, _ in self._as:
      yield 'bool Clif_PyObjAs(PyObject* input, %s* output);' % (
          arg % self.cname if '%s' in arg else arg)
    for arg, ptr, _ in self._from:
      if ptr is None:
        yield 'template<typename T>'
        yield ('typename std::enable_if<std::is_same<T, %s>::value>::type'
               ' Clif_PyObjFrom(%s, py::PostConv) = delete;'
              ) % (self.cname, arg % self.cname)
      else:
        yield 'PyObject* Clif_PyObjFrom(%s, py::PostConv);' % (arg % self.cname)

  def GenConverters(self, ns):
    """Generate Clif_PyObjAs() and Clif_PyObjFrom() definitions."""
    pytype = ns+'::'+self.wrapper_type
    yield ''
    yield '// %s to/from %s conversion' % (self.pyname, self.cname)
    pyname = ns+'::'+self.wrapper_obj
    shared = 'reinterpret_cast<%s*>(py)->cpp' % pyname
    # Python -> C++
    for arg, ptr in self._as:
      yield ''
      if '%s' in arg:
        yield 'bool Clif_PyObjAs(PyObject* py, %s* c) {' % (arg % self.cname)
        yield I+'CHECK(c != nullptr);'
        if arg.endswith('*'):  # raw ptr
          yield I+'if (Py_None == py) {'
          yield I+I+'*c = nullptr;'
          yield I+I+'return true;'
          yield I+'}'
        yield I+'%s* cpp = %s::%sThisPtr(py);' % (self.cname,
                                                  ns, self.wrapper_ns)
        yield I+'if (cpp == nullptr) return false;'
        if arg == 'std::unique_ptr<%s>':
          if not self.virtual:
            yield I+'if (!%s.Detach()) {' % shared
          else:
            yield I+'auto* py_obj_ref = dynamic_cast<::clif::PyObjRef*>(cpp);'
            yield I+('auto& shared = %s;'
                     '  // Potentially IMPROPER reinterpret_cast.' % shared)
            # Catch before we renounce ownership. After that the cpp pointer
            # is no good.
            yield I+'if (py_obj_ref != nullptr) py_obj_ref->HoldPyObj(py);'
            yield I+'if (!shared.Detach()) {'
            # If renouncing cpp ownership failed, renounce py ownership.
            yield I+I+'if (py_obj_ref != nullptr) py_obj_ref->DropPyObj();'
          yield I+I+('PyErr_SetString(PyExc_ValueError, '
                     '"Cannot convert %s instance to std::unique_ptr.");' %
                     self.pyname)
          yield I+I+'return false;'
          yield I+'}'
          yield I+'c->reset(cpp);'
        elif arg == 'std::shared_ptr<%s>':
          if self.virtual:
            yield I+'auto& shared = %s;' % shared
            yield I+('*c = ::clif::MakeSharedVirtual<%s>(shared, py);'
                     % self.cname)
          else:
            yield I+'*c = ::clif::MakeStdShared(%s, cpp);' % shared
        else:
          yield I+'*c = ' + ptr + 'cpp;'
        yield I+'return true;'
      else:
        yield 'bool Clif_PyObjAs(PyObject* py, %s* c) {' % arg
        yield I+'DCHECK(c != nullptr);'
        yield I+'return Clif_PyObjAs(py, static_cast<%s*>(c));' % self.cname
      yield '}'
    # C++ -> Python
    for arg, ptr, init in self._from:
      if ptr is None: continue  # The overload =deleted in header file.
      yield ''
      yield 'PyObject* Clif_PyObjFrom(%s c, py::PostConv unused) {' % (
          arg % self.cname)
      yield I+'CHECK(%s != nullptr) <<' % pytype  # See cl/307519921.
      yield I+I+'"---> Function Clif_PyObjFrom(%s) called before " <<' % (
          self.cname)
      yield I+I+'%s::ThisModuleName  <<' % ns
      yield I+I+'" was imported from Python.";'
      if ptr:
        yield I+'if (c == nullptr) Py_RETURN_NONE;'
      yield I+'PyObject* py = PyType_GenericNew(%s, NULL, NULL);' % pytype
      cname = ns+'::'+self.virtual if self.virtual else self.cname
      init %= (cname,) * init.count('%s')
      yield I+shared+' = '+init
      if self.virtual:
        yield I+shared+'->::clif::PyObjRef::Init(py);'
      yield I+'return py;'
      yield '}'


class EnumType(TypeDef):
  """C++ enum and enum class as Python enum-derived object."""
  _genclifuse = True

  def __init__(self, cpp_name, pyname, pytype, wname, ns=None):
    # args like (ns::FooCpp, X.Y.Foo, Enum/IntEnum, X::Y::_Foo)
    TypeDef.__init__(self, cpp_name, pyname, ns)
    self.wrapper_type = pytype
    self.wrapper_name = wname

  def CreateEnum(self, wname, varname, items):
    """Generate a function to create Enum-derived class and a cache var."""
    yield '// Create Python Enum object (cached in %s) for %s' % (varname,
                                                                  self.cname)
    yield 'static PyObject* %s() {' % wname
    yield I+'PyObject *py_enum_class = nullptr;'
    yield I+'PyObject *modname = nullptr;'
    yield I+'PyObject *py = nullptr;'
    yield I+'PyObject *names = PyTuple_New(%d);' % len(items)
    yield I+'if (names == nullptr) return nullptr;'
    for i, pair in enumerate(items):
      yield I+'if ((py = Py_BuildValue("(NN)", %s, %s)' % pair
      yield I+I+I+') == nullptr) goto err;'
      yield I+'PyTuple_SET_ITEM(names, %d, py);' % i
    yield I+'py = PyUnicode_FromString("%s");' % self.pyname
    yield I+'if (py == nullptr) {'
    yield I+'  goto err;'
    yield I+'}'
    yield I+'modname = PyUnicode_FromString(ThisModuleName);'
    yield I+'if (modname == nullptr) {'
    yield I+'  goto err;'
    yield I+'}'
    yield I+('py_enum_class = PyObject_CallFunctionObjArgs(_%s, py, names, '
             'nullptr);' % self.wrapper_type)
    yield I+'if (py_enum_class != nullptr) {'
    yield I+I+'PyObject_SetAttrString(py_enum_class, "__module__", modname);'
    yield I+'}'
    yield 'err:'
    yield I+'Py_XDECREF(modname);'
    yield I+'Py_XDECREF(py);'
    yield I+'Py_XDECREF(names);'
    yield I+'return py_enum_class;'
    yield '}'
    yield ''
    yield 'static PyObject* %s{};  // set by above func in Init()' % varname

  def GenConverters(self, ns):
    """Generate Clif_PyObjAs() and Clif_PyObjFrom() definitions."""
    wname = ns + '::' + self.wrapper_name
    yield ''
    yield '// %s:%s to/from enum %s conversion' % (
        self.pyname, self.wrapper_type, self.cname)
    yield ''
    yield 'bool Clif_PyObjAs(PyObject* py, %s* c) {' % self.cname
    yield I+'CHECK(c != nullptr);'
    yield I+'if (!PyObject_IsInstance(py, %s)) {' % wname
    yield I+I+('PyErr_Format(PyExc_TypeError, "expecting enum {}, got %s %s", '
               'ClassName(py), ClassType(py));').format(self.pyname)
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
    yield I+'return PyObject_CallFunctionObjArgs(%s, PyLong_FromLong(' % wname
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
    yield ('PyObject* Clif_PyObjFrom(std::unique_ptr<const %s>, py::PostConv);'
           % self.cname)
    yield ('PyObject* Clif_PyObjFrom(std::shared_ptr<const %s>, py::PostConv);'
           % self.cname)

  def GenConverters(self, unused_ns=''):
    """Create convertors for C++ proto to/from Python protobuf."""
    top_name, _, el_name = self.pyname.partition('.')
    import_name = self.module + '.' + top_name
    third_party_path = 'py.'
    if import_name.startswith(third_party_path):
      import_name = import_name[len(third_party_path):]
    ctype = self.cname
    yield ''
    yield '// %s to/from %s conversion' % (self.pyname, ctype)
    yield ''
    yield 'bool Clif_PyObjAs(PyObject* py, %s* c) {' % ctype
    yield I+'CHECK(c != nullptr);'
    yield I+'PyObject* type = ImportFQName("%s");' % import_name
    yield I+('if (!::clif::proto::TypeCheck(py, type, "%s", "%s") ) {'
             % (el_name, self.pyname))
    yield I+I+'return ::clif::proto::InGeneratedPool(py, c);'
    yield I+'}'
    # Use underlying C++ protocol message pointer if available.
    yield I+'if (const proto2::Message* cpb = ::clif::proto::GetCProto(py)) {'
    yield I+I+'c->CopyFrom(*cpb);'
    yield I+I+'return true;'
    yield I+'}'
    yield I+'PyObject* ser = ::clif::proto::Serialize(py);'
    yield I+'if (ser == nullptr) return false;'
    yield I + (
        'bool ok = c->ParsePartialFromArray('
        'PyBytes_AS_STRING(ser), static_cast<int>(PyBytes_GET_SIZE(ser)));')
    yield I+'Py_DECREF(ser);'
    yield I+('if (!ok) PyErr_SetString(PyExc_ValueError, "Serialized bytes '
             'can\'t be parsed into C++ proto");')
    yield I+'return ok;'
    yield '}'
    yield ''
    yield 'bool Clif_PyObjAs(PyObject* py, std::unique_ptr<%s>* c) {' % ctype
    yield I+'CHECK(c != nullptr);'
    yield I+'if (!*c) c->reset(new %s);' % ctype
    yield I+'return Clif_PyObjAs(py, c->get());'
    yield '}'
    yield ''
    yield 'PyObject* Clif_PyObjFrom(const %s& c, py::PostConv) {' % ctype
    yield I+'PyObject* type = ImportFQName("%s");' % import_name
    yield I+'return ::clif::proto::PyProtoFrom(&c, type, "%s");' % el_name
    yield '}'
    for smp in ('std::unique_ptr', 'std::shared_ptr'):
      yield ''
      yield 'PyObject* Clif_PyObjFrom(%s<const %s> c, py::PostConv) {' % (
          smp, ctype)
      yield I+'if (!c) Py_RETURN_NONE;'
      yield I+'PyObject* type = ImportFQName("%s");' % import_name
      yield I+('return ::clif::proto::PyProtoFrom(c.get(), type, "%s");'
               % el_name)
      yield '}'


class ProtoEnumType(TypeDef):
  """C++ proto Enum as int as Python int."""

  def GenHeader(self):
    yield _ClifUse(self.cname, self.pyname)
    yield 'bool Clif_PyObjAs(PyObject* input, %s* output);' % self.cname
    yield 'PyObject* Clif_PyObjFrom(%s, py::PostConv);' % self.cname

  def GenConverters(self, unused_ns=''):
    yield ''
    yield '// %s to/from enum %s conversion' % (self.pyname, self.cname)
    yield 'bool Clif_PyObjAs(PyObject* py, %s* c) {' % self.cname
    yield I+'CHECK(c != nullptr);'
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

  def GenConverters(self, ns):
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
    yield _ClifUse(self.cname+'*', self.pyname)
    yield 'bool Clif_PyObjAs(PyObject* input, %s** output);' % self.cname
    yield 'PyObject* Clif_PyObjFrom(const %s*, py::PostConv);' % self.cname

  def GenConverters(self, unused_ns=''):
    """Generate a Clif_PyObjFrom(Foo*) converter."""
    yield ''
    yield '// %s to/from %s conversion' % (self.pyname, self.cname)
    yield ''
    yield 'bool Clif_PyObjAs(PyObject* py, %s** c) {' % self.cname
    yield I+'CHECK(c != nullptr);'
    yield I+'if (Py_None == py) {'
    yield I+I+'*c = nullptr;'
    yield I+I+'return true;'
    yield I+'}'
    yield I+'if (PyCapsule_CheckExact(py)) {'
    yield I+I+'void* p = PyCapsule_GetPointer(py, "%s");' % self.cname
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
    yield I+'return PyCapsule_New((void*)c, "%s", nullptr);' % self.cname
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
  yield I+'if (Py_TYPE(py) == %s) {' % t
  yield I+I+return_this_cpp
  yield I+'}'
  # self.as_Base(), where Base is this class.
  for s in _GenBaseCapsule(cname, retptr=True):
    yield s
  if final:
    _I=''  # pylint: disable=bad-whitespace,invalid-name
  else:
    # as_Base returned an error / wrong capsule
    yield I+'if (PyObject_IsInstance(py, %s)) {' % AsPyObj(t)
    yield I+I+'if (!base) {'  # base set in _GenBaseCapsule
    yield I+I+I+return_this_cpp
    yield I+I+'}'
    yield I+I+('PyErr_Format(PyExc_ValueError, "can\'t convert %s %s to {}*", '
               'ClassName(py), ClassType(py));').format(cname)
    yield I+'} else {'
    _I=I  # pylint: disable=bad-whitespace,invalid-name
  yield _I+I+('PyErr_Format(PyExc_TypeError, "expecting %s instance, got %s %s"'
              ', {}->tp_name, ClassName(py), ClassType(py));'.format(t))
  if not final:
    yield I+'}'
  yield I+'return nullptr;'
  yield '}'


def _GenBaseCapsule(cname, retptr=False):
  """Generates snippet for checking as_BASE() call."""
  # Uses var naming convetion:
  # - from CapsuleType.GenConverters to set *c result (unless retptr set),
  # - from -/- and GenThisPointerFunc to use 'py' argument and 'base' object.
  yield I+('PyObject* base = PyObject_CallMethod(py, "as_%s", nullptr);'
           % Mangle(cname))
  yield I+'if (base == nullptr) {'
  yield I+I+'PyErr_Clear();'
  yield I+'} else {'
  yield I+I+'if (PyCapsule_CheckExact(base)) {'
  yield I+I+I+'void* p = PyCapsule_GetPointer(base, "%s");' % cname
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


def _MangleCharacterLiteral(char_literal):
  """Escapes a char-valued template parameter."""
  if str is not bytes:
    char_literal = char_literal.encode()

  return 'c{}_'.format(ord(bytes(char_literal).decode('unicode_escape')))


def Mangle(cname):
  """Transform canonical LLVM type output to a valid Python id."""
  # Mangle does not make unique id, so A::B and A_B are the same.
  # It's intended to be used inside one class/namespace where collisions
  # should not happen.
  c = FIND_CPP_CHAR_LITERAL.sub(lambda m: _MangleCharacterLiteral(m.group(1)),
                                cname)
  c = (c
       .strip(' :>')
       .replace('::', '_')
       .replace('<', '_')
       .replace('-', '_')
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
  return 'reinterpret_cast<PyObject*>(%s)' % s
