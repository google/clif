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

"""Convert "pyparsed" CLIF PYTD IR to CLIF AST proto.

Use
  p = Postprocessor()
  p.Translate(file_object) to get CLIF AST proto generated from CLIF PYTD text.

In case of errors it will raise an exception. Possible exceptions are:
  pyparsing.ParseFatalException - grammar error in input text
  NameError - wrong naming (usually duplicate names)
  SyntaxError - wrong construct or statement usage
"""

from __future__ import print_function
import os
import pickle
import re
import sys
from clif.protos import ast_pb2
from clif.python import pytd_parser

CLIF_USE = re.compile(r'// *CLIF:? +use'
                      r' +`(?P<cname>.+)` +as +(?P<pyname>[\w.]+)')
CLIF_INIT = re.compile(r'// *CLIF:? +init_module +(?P<cpp_statement>.+)')
CLIF_MACRO = re.compile(r'// *CLIF:? +macro +(?P<name>.+) +(?P<def>.+)$')
CLIF_INCLUDE = re.compile(r'// *CLIF:? +include +"(?P<path>[^"]+)"')


def _read_include(input_stream, fname, prefix, typetable, capsules, interfaces,
                  extra_init):
  for s in input_stream:
    use = CLIF_USE.match(s)
    if use:
      cname = use.group('cname')
      pyname = use.group('pyname')
      if not (cname and pyname):
        raise SyntaxError('Invalid "use" pragma in "%s": %s' % (fname, s))
      pyname = prefix + pyname
      if pyname in capsules:
        raise NameError('C++ type "%s" already wrapped as capsule by name %s'
                        % (cname, pyname))
      if pyname in typetable and cname.endswith('*'):
        raise NameError('C++ type "%s" already wrapped by name %s'
                        % (cname, pyname))
      for known_name in typetable.items():
        if cname in known_name[1]:
          raise NameError('C++ type "%s" already wrapped by name %s'
                          % (cname, known_name[0]))
      if cname.endswith('*'):
        capsules[pyname] = cname
      else:
        typetable.setdefault(pyname, []).append(cname)
      continue
    init = CLIF_INIT.match(s)
    if init:
      extra_init.append(init.group('cpp_statement'))
      continue
    include = CLIF_INCLUDE.match(s)
    if include:
      yield include.group('path')
      continue
    macro = CLIF_MACRO.match(s)
    if macro:
      name = macro.group('name')
      s = macro.group('def').replace(r'\n', '\n')
      try:
        sysver, ppver, src = pickle.loads(s)
      except Exception:  # pylint: disable=broad-except
        raise ImportError('Macro %s loading error' % name)
      if sysver != sys.hexversion or ppver != pytd_parser.version:
        raise ValueError('Interface name "%s" from file %s is from '
                         'incompatible version (%s, %s)'
                         % (name, fname, sysver, ppver))
      if name in interfaces:
        raise NameError('Interface name "%s" from file %s already used'
                        % (name, fname))
      interfaces[name] = src
      continue


class Postprocessor(object):
  """Process parsed IR."""

  def __init__(self, config_headers=None, include_paths=('.',), preamble=''):
    self._names = {}  # Keep name->FQN for all 'from path import' statements.
    self._capsules = {}   # Keep raw pointer names (pytype -> cpptype).
    self._typenames = {}  # Keep typedef aliases (pytype -> type_ir).
    self._typetable = {}  # Keep typetable (pytype -> [cpptype]) defaults.
    self._macros = {}  # Keep interfaces (name -> (num_args, subtree)).
    self._scan_includes = config_headers or []
    self._include_paths = include_paths
    self._preamble = preamble
    self.source = None
    self._macro_values = []  # [actual, param, values] only set in _class that
                             # has implements MACRO<actual, param, values>
    self.need_threads = False  # Add call to PyEval_InitThreads to Init.

  def is_pyname_known(self, name):
    return (name in self._capsules or
            name in self._typetable or
            name in self._typenames)

  def check_known_name(self, name):
    if name in self._capsules:
      raise NameError('Name "%s" already defined as capsule name.' % name)
    if name in self._typetable:
      raise NameError('Name "%s" already defined as type.' % name)
    if name in self._typenames:
      raise NameError('Name "%s" already defined as type alias.' % name)
    if name in self._macros:
      raise NameError('Name "%s" already defined as interface name.' % name)

  def line(self, loc):
    return pytd_parser.LineNum(loc, self.source)

  def Translate(self, pytd_file):  # pylint: disable=invalid-name
    """Given an open .pytd file, return a CLIF AST ast_pb2.AST protobuffer."""
    pb = ast_pb2.AST()
    pb.source = pytd_file.name
    for hdr in self._scan_includes:
      pb.usertype_includes.append(hdr)
      self._include(0, [hdr], pb, scan_only=True)
    if self._preamble:
      self._Parse(self._preamble, pb)
    self._Parse(pytd_file.read(), pb)
    if self.need_threads:
      pb.extra_init.append('PyEval_InitThreads();')
    # Assumed we always want a deterministic output proto. Since dict/set order
    # is not, do sorted() order traversal.
    order = sorted
    for t in order(self._typetable):
      tm = pb.typemaps.add()
      tm.lang_type = t
      for ct in order(set(self._typetable[t])):
        tm.cpp_type.append(ct)
    for t in order(self._capsules):
      tm = pb.typemaps.add()
      tm.lang_type = t
      tm.cpp_type.append(self._capsules[t])
    for name, src in order(self._macros.items()):
      m = pb.macros.add()
      m.name = name
      # Use protocol 0 to keep version independence.
      m.definition = pickle.dumps((sys.hexversion, pytd_parser.version, src), 0)
    return pb

  def _Parse(self, text, pb):  # pylint: disable=invalid-name
    self.source = text  # save for line number calculation
    for ir in pytd_parser.Clif.parseString(text, parseAll=True):
      if ir:
        # IR is specific to the parser.
        # IR[0] is a statement name.
        getattr(self, '_'+ir[0])(self.line(ir[1]), ir[2:], pb)
    self.source = None

  # statement
  #
  # Args:
  #   ln: line number in the .clif file
  #   p: IR subtree (with statement keyword removed)
  #   pb: AST proto for this statement to fill

  def _interface(self, ln, p, unused_pb=None):
    """'Macro definition' stores a subtree with var placeholders (%0, %1...)."""
    assert len(p) > 2, p
    nargs = len(p) - 2  # 0-name, -1-block, [1:-1]-args
    name = p[0]
    self.check_known_name(name)
    args = {name: pos for pos, name in enumerate(p[:-1])}
    if len(args) != nargs+1:
      raise NameError('all interface args must be different '
                      'at line %d, got %s<%s>' % (ln, name, ', '.join(p[1:-1])))
    src = p[-1]
    if nargs:
      for ast in src:
        if ast[0] == 'func':
          for p in ast.params:
            _subst_type_formal(p, args)
          for p in ast.returns:
            _subst_type_formal(p, args)
        elif ast[0] == 'var':
          _subst_type_formal(ast, args)
        else:
          raise NameError('Only def and var allowed in interface,'
                          ' found "%s" at line %d' % (ast[0], ln))
    self._macros[name] = nargs, src

  def _from(self, unused_ln, p, pb):
    """from "full/project/path/cheader.h": BLOCK."""
    assert len(p) == 2, str(p)
    hdr = p[0]
    for s in p[1]:
      if s[0] == 'namespace':
        self._namespace(None, s, pb, hdr)
      elif s[0] == 'staticmethods':
        self._staticmethods(None, s, pb, hdr)
      else:
        decl = pb.decls.add()
        decl.cpp_file = hdr
        getattr(self, '_'+s[0])(self.line(s[1]), s, decl)

  def _namespace(self, unused_ln, p, pb, hdr):
    assert len(p) == 4, str(p)
    ns = 'clif' if p[2] == 'std' else p[2]
    for s in p[-1]:
      if s[0] == 'interface':
        self._interface(self.line(s[1]), s[2:])
      elif s[0] == 'staticmethods':
        self._staticmethods(self.line(s[1]), s, pb, hdr, ns=ns)
      else:
        decl = pb.decls.add()
        decl.cpp_file = hdr
        decl.namespace_ = ns
        getattr(self, '_'+s[0])(self.line(s[1]), s, decl, ns=ns)

  def _staticmethods(self, ln, p, pb, hdr, ns=''):
    assert len(p) == 4, str(p)
    assert hdr
    if ns and p[2].startswith(':'):
      raise NameError('Invalid reference to global class %s inside namespace %s'
                      ' at line %d' % (p[2], ns, ln))
    cns = ns +  '::' + p[2]
    for s in p[-1]:
      decl = pb.decls.add()
      decl.cpp_file = hdr
      if ns:
        decl.namespace_ = ns
      getattr(self, '_'+s[0])(self.line(s[1]), s, decl, ns=cns)

  def _include(self, unused_ln, p, pb, scan_only=False):
    """from "full/project/path/cheader.h" import *."""
    assert len(p) in (1, 2), p.dump()
    hdr = p[0]
    if not scan_only:
      pb.usertype_includes.append(hdr)
    # Scan hdr for new types
    namespace = p[1]+'.' if len(p) > 1 else ''
    for root in self._include_paths:
      try:
        with open(os.path.join(root, hdr)) as include_file:
          pb.usertype_includes.extend(
              _read_include(include_file, hdr, namespace,
                            self._typetable, self._capsules, self._macros,
                            pb.extra_init))
        break
      except IOError:
        pass
    else:
      raise NameError('include "%s" not found' % hdr)

  def _import(self, unused_ln, p, unused_pb):
    """from full.python.path import postprocessor."""
    assert len(p) == 2, str(p)
    n = p[1]
    if n in self._names:
      raise NameError('Name %r already defined' % n)
    self._names[n] = '.'.join(p)

  def _type(self, unused_ln, p, pb):
    """type T = [`postconversion` as] pytype."""
    # typedef alias name(p[0]) = type(p[1])
    assert len(p) == 2, p.dump()
    if p[0] in self._typenames:
      raise NameError('Type %r already defined' % p[0])
    pytype = p[1].name[-1]
    if pytype not in self._typetable:
      raise NameError('Type %r not defined' % pytype)
    self._typenames[p[0]] = p[1]
    if len(p[1].name) > 1:
      # Save postconversion.
      tm = pb.typemaps.add()
      tm.lang_type = p[0]
      tm.postconversion = p[1].name[0]

  def _use(self, ln, p, unused_pb):
    """use `ctype` as pytype."""
    assert len(p) == 2, p.dump()
    if p[0].endswith('*'):
      raise NameError('Wrap type %s before use' % p[0][:-1])
    if not self.is_pyname_known(p[1]):
      raise NameError('Type %s should be defined before use at line %s'
                      % (p[1], ln))
    self._typetable.setdefault(p[1], []).append(p[0])

  # decl

  def _capsule(self, ln, ast, pb, ns=None):
    assert isinstance(pb, ast_pb2.Decl), repr(pb)
    assert len(ast) == 3, ast.dump()
    pb.line_number = ln
    pb.decltype = pb.TYPE
    p = pb.fdecl
    _set_name(p.name, ast.name, ns)
    self.check_known_name(p.name.native)
    self._capsules[p.name.native] = p.name.cpp_name + ' *'
    return p.name.native

  def _class(self, ln, ast, pb, ns=None):
    """Translate PYTD class IR ast to AST Decl protobuf."""
    assert isinstance(pb, ast_pb2.Decl), repr(pb)
    atln = ' at line %d' % ln
    pb.line_number = ln
    pb.decltype = pb.CLASS
    p = pb.class_
    cpp_name = ast.name[0]  # Save C++ name without FQ.
    _set_name(p.name, ast.name, ns)
    pyname = p.name.native
    self.check_known_name(pyname)
    self._typetable[pyname] = [p.name.cpp_name]
    decorators = ast.decorators.asList()
    if 'final' in decorators:
      p.final = True
      decorators.remove('final')
    if 'async__del__' in decorators:
      p.async_dtor = True
      decorators.remove('async__del__')
      self.need_threads = True
    if decorators:
      raise NameError('Unknown class decorator(s)%s: %s'
                      % (atln, ', '.join(decorators)))
    _set_bases(p.bases, ast.bases, self._names, self._typetable)
    local_names = set()
    for decl in ast[-1]:
      if decl[0] == 'pass':
        # Pass is a special case as we don't want to add() to the proto.
        if len(ast[-1]) != 1:
          raise SyntaxError('pass must be the only class statement' + atln)
        if not ast.bases:
          raise SyntaxError('only derived class allowed to be empty' + atln)
        continue
      line_number = self.line(decl[1])
      if decl[0] == 'implements':
        name = decl[2]
        self._macro_values = [pyname] + decl[3:]
        try:
          nargs, src = self._macros[name]
        except KeyError:
          raise NameError('interface %s not defined' % name + atln)
        if len(self._macro_values) != nargs+1:
          raise NameError('interface %s needs %d args (%d given)'
                          % (name, len(self._macro_values)-1, nargs) + atln)
        for d in src:
          ln = self.line(d[1])
          if d[0] == 'func':
            if not self.unproperty(ln, d, pyname, p.members, local_names):
              _add_uniq(pyname, local_names, self._func(ln, d, p.members.add()))
          elif d[0] == 'var':
            _add_uniq(pyname, local_names, self._var(ln, d, p.members.add()))
          else:
            assert 0, 'implements %s contains unallowed %s'%(name, d[0]) + atln
        self._macro_values = []
        continue
      if (decl[0] == 'func' and
          self.unproperty(line_number, decl, pyname, p.members, local_names)):
        continue
      name = getattr(self, '_'+decl[0])(line_number, decl, p.members.add())
      _add_uniq(pyname, local_names, name)
    # Fix ctor name to be the class name.
    for m in p.members:
      if m.decltype != m.FUNC:
        continue
      if m.func.name.native == '__init__':
        if (m.func.name.cpp_name and
            m.func.name.cpp_name not in [cpp_name, '__init__']):
          print('Arbitrary names (like "{0}") for {1} ctor not allowed.'
                ' Set to {1}'.format(m.func.name.cpp_name, cpp_name),
                file=sys.stderr)
        m.func.name.cpp_name = cpp_name
        m.func.constructor = True
      elif m.func.name.native == cpp_name:
        raise NameError('Use __init__ to wrap a "%s" constructor'%pyname + atln)
      elif m.func.name.cpp_name == cpp_name:
        # @add__init__ will reset cpp_name to be empty.
        raise NameError('Use @add__init__ to wrap additional "%s" constructor'
                        '(s).' % pyname + atln)
      elif not m.func.name.cpp_name:  # An additional ctor.
        m.func.name.cpp_name = cpp_name
        m.func.constructor = True
      elif m.func.name.native in _RIGHT_OPS:
        if len(m.func.params) != 1:
          raise ValueError('%s must have only 1 input parameter'
                           % m.func.name.native + atln)
        m.func.cpp_opfunction = True  # Special case C++ operator function.
        this = m.func.params.add()
        this.name.native = 'self'
        this.name.cpp_name = 'this'
        this.type.lang_type = cpp_name
        this.type.cpp_type = cpp_name
    _move_local_types(p.members, pyname+'.', cpp_name+'::', self._typetable)
    return pyname

  def unproperty(self, ln, ast, class_name, members, known_names):
    """Translate PYTD func IR into VAR getter / setter protobuf.

    Args:
      ln: .clif line number
      ast: func IR
      class_name: Python name of the wrapped C++ class
      members: wrapped C++ class memebers
      known_names: names already defined in a C++ class wrapper
    Returns:
      True if ast is a @getter/@setter func that describes 'unproperty' C++ var.
    Raises:
      ValueError: if @getter or @setter refers to exising var with =property().
    """
    assert ast[0] == 'func', repr(ast)
    getset = ast.decorators.asList()
    if getset not in (['getter'], ['setter']): return False
    # Convert func to var.
    f = ast_pb2.Decl()
    self._func(ln, ast, f)
    f = f.func
    cname = f.name.cpp_name
    pyname = f.name.native
    for m in members:
      if m.decltype == m.VAR and m.var.name.cpp_name == cname:
        if m.var.cpp_get.name.cpp_name:
          raise ValueError("property var can't have @getter / @setter func")
        if m.var.name.native == pyname:
          known_names.discard(m.var.name.native)
        break
    else:
      m = members.add()
      m.line_number = ln
      m.decltype = m.VAR
      m.var.name.cpp_name = cname
    _add_uniq(class_name, known_names, pyname)
    p = m.var
    if getset == ['getter']:
      if len(f.returns) != 1 or f.params:
        raise TypeError('@getter signature must be (self)->T')
      p.type.CopyFrom(f.returns[0].type)
      p.cpp_get.name.native = pyname
    else:
      assert getset == ['setter']
      if len(f.params) != 1 or f.returns:
        raise TypeError('@setter signature must be (self, _:T)')
      p.type.CopyFrom(f.params[0].type)
      p.cpp_set.name.native = pyname
      if not p.cpp_get.name.native:
        # Provide default getter as VARNAME().
        p.cpp_get.name.native = cname
      # Preserve func param varname for the error message (not useful otherwise)
      p.name.native = f.params[0].name.native
    return True

  def _enum(self, ln, ast, pb, ns=None):
    """Translate PYTD enum IR ast to AST Decl protobuf."""
    assert isinstance(pb, ast_pb2.Decl), repr(pb)
    pb.line_number = ln
    pb.decltype = pb.ENUM
    e = pb.enum
    _set_name(e.name, ast.name, ns)
    pyname = e.name.native
    self.check_known_name(pyname)
    self._typetable[pyname] = [e.name.cpp_name]
    if len(ast) > 3:
      for rename in ast[-1]:
        _set_name(e.members.add(), rename)
    return pyname

  def _var(self, ln, ast, pb):
    """Translate PYTD var IR ast to AST Decl protobuf."""
    assert isinstance(pb, ast_pb2.Decl), repr(pb)
    pb.line_number = ln
    pb.decltype = pb.VAR
    p = pb.var
    _set_name(p.name, ast.name)
    self.set_type(p.type, ast)
    if ast.getter:
      f = p.cpp_get
      f.name.cpp_name = ast.getter
      self.set_type(f.returns.add().type, ast)
    if ast.setter:
      f = p.cpp_set
      f.name.cpp_name = ast.setter
      self.set_type(f.params.add().type, ast)
      f.ignore_return_value = True
    return p.name.native

  def _const(self, ln, ast, pb, ns=None):
    """Translate PYTD const IR ast to AST Decl protobuf."""
    assert isinstance(pb, ast_pb2.Decl), repr(pb)
    pb.line_number = ln
    pb.decltype = pb.CONST
    p = pb.const
    _set_name(p.name, ast.name, ns)
    if self.set_type(p.type, ast) == 'str':
      p.type.cpp_type = 'const char *'  # Special case for b/27458244.
    return p.name.native

  def _func(self, ln, ast, pb, ns=None):
    """Translate PYTD def IR ast to AST Decl protobuf."""
    assert isinstance(pb, ast_pb2.Decl), repr(pb)
    pb.line_number = ln
    pb.decltype = pb.FUNC
    f = pb.func
    _set_name(f.name, _fix_special_names(ast.name), ns, allow_fqcppname=True)
    self.set_func(f, ast)
    decorators = ast.decorators.asList()
    if ast.self == 'cls':
      if 'classmethod' not in decorators:
        raise ValueError('Method %s with the first arg cls should be '
                         '@classmethod' % f.name.native)
      if 'virtual' in decorators:
        raise ValueError("Classmethods can't be @virtual")
      f.classmethod = True
    elif 'classmethod' in decorators:
      raise ValueError('Method %s with the first arg self should not be '
                       '@classmethod' % f.name.native)
    elif 'virtual' in decorators:
      if ast.self != 'self':
        raise ValueError('@virual method first arg must be self')
      f.virtual = True
    if 'async' in decorators:
      f.async = True
      self.need_threads = True
    if 'add__init__' in decorators:
      f.name.cpp_name = ''  # A hack to flag an extra ctor.
    if 'sequential' in decorators:
      if f.name.native not in ('__getitem__', '__setitem__', '__delitem__'):
        raise NameError('Only __{get/set/del}item__ can be @sequential')
      f.name.native += '#'  # A hack to flag a sq_* slot.
    if '__enter__' in decorators:
      f.name.native = '__enter__@'  # A hack to flag a ctx mgr.
    elif f.name.native == '__enter__':
      if f.postproc or f.params or len(f.returns) != 1:
        raise NameError('Use @__enter__ decorator for %s instead of rename'
                        % f.name.cpp_name)
    if '__exit__' in decorators:
      f.name.native = '__exit__@'  # A hack to flag a ctx mgr.
    elif f.name.native == '__exit__':
      if (len(f.params) != 3
          or len(f.returns) > 1
          or any(p.type.lang_type != 'object' for p in f.params)):
        raise NameError('Use @__exit__ decorator for %s instead of rename'
                        % f.name.cpp_name)
    elif f.name.native in _IGNORE_RETURN_VALUE:
      f.ignore_return_value = True
    if ast.postproc:
      name = ast.postproc[0][0][0]
      try:
        f.postproc = self._names[name]
      except KeyError:
        raise NameError('Should import name "%s" before use.' % name)
    return f.name.native.rstrip('@#')

  # helpers

  def set_type(self, pb, ast):
    """Fill AST Type protobuf from PYTD IR ast."""
    assert isinstance(pb, ast_pb2.Type), repr(pb)
    if ast.callable:
      self.need_threads = True
      self.set_func(pb.callable, ast.callable)
      inputs = (a.name.native+':'+a.type.lang_type for a in pb.callable.params)
      inputs = '(%s)' % ', '.join(inputs)
      if len(pb.callable.returns) > 1:
        outputs = (':'+r.type.lang_type for r in pb.callable.returns)
        outputs = '(%s)' % ', '.join(outputs)
      elif pb.callable.returns:
        outputs = pb.callable.returns[0].type.lang_type or 'None'
      else:
        outputs = 'None'
      pb.lang_type = inputs + '->' + outputs
      if pb.lang_type == '()->None':
        # Set any field inside to avoid empty callable message.
        pb.callable.cpp_opfunction = True
      if len(ast.callable) == 3:  # Has an explicit C++ type.
        pb.cpp_type = ast.callable[0]
      # Else fill it after matcher finds the types.
    if ast.named:
      self.set_typename(pb, ast.named)
      if len(ast.named) > 1:
        pb.lang_type += '<%s>' % ', '.join(
            self.set_type(pb.params.add(), t) for t in ast.named[1:])
        if len(ast.named.name) > 1:  # Has an explicit C++ type.
          pb.cpp_type = ast.named.name[0]
    assert pb.lang_type, 'Parameter AST is not "named" or "callable":\n%r' % ast
    return pb.lang_type

  def set_typename(self, pb, ast):
    """Substitute C++ type based on pytype name."""
    assert isinstance(pb, ast_pb2.Type), repr(pb)
    pytype = ast.name[-1]
    if pytype.startswith('%'):
      assert self._macro_values
      pytype = self._macro_values[int(pytype[1:])]
    if not self.is_pyname_known(pytype):
      raise NameError('Type %s should be defined before use' % pytype)
    pb.lang_type = pytype
    if len(ast.name) > 1:  # Has an explicit C++ type.
      pb.cpp_type = ast.name[0]
    else:
      ctype = self._capsules.get(pytype)
      if ctype:
        pb.cpp_raw_pointer = True
      elif pytype in self._typetable:
        ctype = self._typetable[pytype][-1]
      else:
        alias_ir = self._typenames.get(pytype)
        if alias_ir:
          pytype = alias_ir.name[-1]
          assert pytype in self._typetable, 'alias %s not in typetable' % pytype
          ctype = self._typetable[pytype][-1]
      assert ctype, 'C++ type for %s not found' % pytype
      pb.cpp_type = ctype

  def set_func(self, pb, ast):
    """Fill AST FuncDecl protobuf from PYTD IR ast."""
    assert isinstance(pb, ast_pb2.FuncDecl), repr(pb)
    arg_names = set()
    must_be_optional = False
    for arg in ast.params:
      pyname = arg.name[-1]
      if pyname in arg_names:
        raise NameError('Name "%s" already used in args.' % pyname)
      arg_names.add(pyname)
      p = pb.params.add()
      _set_name(p.name, arg.name)
      self.set_type(p.type, arg)
      if len(arg) > 2:
        p.default_value = arg[2]
        must_be_optional = True
      elif must_be_optional:
        raise ValueError('Arg "%s" (and all after) must be optional bacause '
                         'arg(s) before it marked optional.')
    for t in ast.returns:
      p = pb.returns.add()
      self.set_type(p.type, t)
      if t.name:
        pyname = t.name[-1]
        if pyname in arg_names:
          raise NameError('Name "%s" already used in args.' % pyname)
        arg_names.add(pyname)
        _set_name(p.name, t.name)


def _set_bases(pb, ast_bases, names, typetable):
  """Fill AST.ClassDecl bases pb from IR.bases."""
  for b in ast_bases:
    n = b[-1]
    if n == 'replacement':
      if len(b) != 2:
        raise NameError('Base class replacement must have a C++ name')
      if len(ast_bases) != 1:
        raise NameError('Base class replacement must be the only base class')
    else:
      if len(b) != 1:
        raise NameError('Base class must not have a C++ name')
      try:
        n = names[n]  # Resolve to FQName.
      except KeyError:
        # TODO: Lookup possible 'renames' for bases.
        if n not in typetable:
          raise NameError('Base class %s not defined' % n)
    base = pb.add()
    base.native = n
    if n == 'replacement':
      base.cpp_name = b[0]


def _set_name(pb, ast, namespace=None, allow_fqcppname=False):
  """Fill AST Name protobuf from PYTD IR ast."""
  assert isinstance(pb, ast_pb2.Name), repr(pb)
  assert ast, repr(ast)
  pb.native = ast[-1]
  if not allow_fqcppname and '::' in ast[0]:
    raise NameError(':: not allowed in C++ name for ' + ast[-1])
  if not namespace or ast[0].startswith('::'):  # absolute name
    pb.cpp_name = ast[0]
  else:
    if not namespace.endswith('::'):
      namespace += '::'
    pb.cpp_name = namespace + ast[0]


def _add_uniq(class_name, names_set, new_name):
  assert new_name, class_name+' has %s' % names_set
  if new_name:
    if new_name in names_set:
      raise NameError('Name "%s" already defined in class %s'
                      % (new_name, class_name))
    names_set.add(new_name)


def _subst_type_formal(ast, from_map):
  """Walk type ast and replace names from_map to %position markers."""
  if ast.callable:
    for p in ast.callable.params:
      _subst_type_formal(p, from_map)
    for p in ast.callable.returns:
      _subst_type_formal(p, from_map)
  if ast.named:
    n = ast.named.name
    if len(ast.named) > 1:
      for t in ast.named[1:]:
        _subst_type_formal(t, from_map)
    else:
      p = n[-1]
      if p in from_map:
        if len(n) > 1:  # Has an explicit C++ type.
          raise NameError('C++ name not allowed in interface parameters (%s)'%p)
        n[-1] = '%' + str(from_map[p])


def  _move_local_types(members, pn, cn, typetable):
  """Move "local" class and enum types to class.name / class::cpp_type."""
  # Prefix is pn = 'class.', cn = 'class::'.
  for m in members:
    if m.decltype == m.ENUM:
      name = m.enum.name.native
    elif m.decltype == m.CLASS:
      name = m.class_.name.native
    else:
      continue
    t = m.WhichOneof('decl')
    assert name in typetable, pn+t+' member '+name+' not in _typetable'
    ns = typetable[name]
    assert len(ns) == 1, 'duplicate local type name '+name
    assert pn + name not in typetable, (
        "can't promote local type %s up to %s, type name taken" % (name, pn))
    typetable[pn + name] = [cn + ns[0]]
    del typetable[name]
    if t == 'class_':  # Check subtypes.
      prefix = name+'.'
      for n in typetable:
        if n.startswith(prefix):
          ns = typetable[n]
          assert len(ns) == 1, 'type name %s misdefined %s' % (n, ns)
          assert pn + n not in typetable, (
              "can't promote local name %s up to %s, name taken" % (n, pn))
          typetable[pn + n] = [cn + ns[0]]
          del typetable[n]


# Python special method name that we can ignore returning C++ value for.
# (Implemented as slot::ignore(...) in slots.py)
_IGNORE_RETURN_VALUE = [
    '__setitem__',
    '__delitem__',
    '__setattr__',
    '__delattr__',
    '__iadd__',
    '__isub__',
    '__imul__',
    '__idiv__',
    '__itruediv__',
    '__imod__',
    '__ilshift__',
    '__irshift__',
    '__iand__',
    '__ixor__',
    '__ior__',
]

# Python special method name -> C++ operator rename table.
_SPECIAL = {
    '__lt__': 'operator<',
    '__le__': 'operator<=',
    '__gt__': 'operator>',
    '__ge__': 'operator>=',
    '__eq__': 'operator==',
    '__ne__': 'operator!=',
    '__pos__': 'operator+',
    '__add__': 'operator+',
    '__radd__': 'operator+',
    '__iadd__': 'operator+=',
    '__neg__': 'operator-',
    '__sub__': 'operator-',
    '__rsub__': 'operator-',
    '__isub__': 'operator-=',
    '__mul__': 'operator*',
    '__rmul__': 'operator*',
    '__imul__': 'operator*=',
    '__div__': 'operator/',
    '__rdiv__': 'operator/',
    '__idiv__': 'operator/=',
    '__truediv__': 'operator/',
    '__rtruediv__': 'operator/',
    '__itruediv__': 'operator/=',
    '__mod__': 'operator%',
    '__rmod__': 'operator%',
    '__imod__': 'operator%=',
    '__lshift__': 'operator<<',
    '__rlshift__': 'operator<<',
    '__ilshift__': 'operator<<=',
    '__rshift__': 'operator>>',
    '__rrshift__': 'operator>>',
    '__irshift__': 'operator>>=',
    '__and__': 'operator&',
    '__rand__': 'operator&',
    '__iand__': 'operator&=',
    '__xor__': 'operator^',
    '__rxor__': 'operator^',
    '__ixor__': 'operator^=',
    '__or__': 'operator|',
    '__ror__': 'operator|',
    '__ior__': 'operator|=',
    '__inv__': 'operator~',
    '__invert__': 'operator~',
    '__call__': 'operator()',
    '__getitem__': 'operator[]',
    '__del__': 'DO_NOT_DECLARE_DTOR'
}
_RIGHT_OPS = frozenset([
    '__radd__',
    '__rsub__',
    '__rmul__',
    '__rdiv__',
    '__rtruediv__',
    '__rfloordiv__',
    '__rmod__',
    '__rlshift__',
    '__rrshift__',
    '__rand__',
    '__ror__',
    '__rxor__',
])
assert _RIGHT_OPS-set(_SPECIAL) == frozenset(['__rfloordiv__'])


def _fix_special_names(ast_name):
  """Fill "cpp_name" for Python special name if empty."""
  if len(ast_name) == 1:
    pyname = ast_name[0]
    op = _SPECIAL.get(pyname)
    if op:
      return [op, pyname]
  return ast_name
