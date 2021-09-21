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

"""Generate Python extension module source files from CLIF description.

Uses FLAGS defined below to produces 3 output files:
-c"base.cc" with the bulk of wrapped code
-i"init.cc" with .so initmodule function
-h"module.h" with type conversion declarations to wrapped types

Pass compiler flags (-f"copts") to Clang compiler in --matcher_bin executable.
Loads CLIF configuration headers with [multiple] -p"types.h" to scan for types.

If invoked with --dump_dir, no output files flags are needed: It
dumps all output to the given dir.
"""

import argparse
import os
import stat
import subprocess
import sys

from clif.protos import ast_pb2
from clif.python import gen, pyext, pytd2proto  # pylint: disable=g-multiple-import
import google.protobuf.text_format

FLAGS = None
PIPE = subprocess.PIPE


def _ParseCommandline(doc, argv):
  """Define command-line flags and return parsed argv."""
  parser = argparse.ArgumentParser(description=doc)
  parser.add_argument('--matcher_bin',
                      default=(os.getenv('CLIF_MATCHER') or
                               sys.prefix+'/clang/bin/clif-matcher'),
                      help='Matcher executable')
  parser.add_argument('--nc_test', default=False, action='store_true',
                      help='Negative compilation test')
  parser.add_argument('--dump_dir',
                      help='Dump intermediate files to this dir')
  parser.add_argument('--binary_dump', default=False, action='store_true',
                      help='Dump protos in binary format.')
  parser.add_argument('--modname',
                      help='Generated module name')
  parser.add_argument('--prepend', '-p', action='append',
                      default=[],
                      help=('Prepend header file to scan default '
                            'C++ types from "// CLIF use..." comments'))
  parser.add_argument('--include_paths', '-I', default=['.'], action='append',
                      help='Try those dirs to open include "files"')
  parser.add_argument('--ccdeps_out', '-c', metavar='MODNAME.cc',
                      help='output filename for base .cc')
  parser.add_argument('--ccinit_out', '-i', metavar='MODNAME_init.cc',
                      help='output filename for init .cc')
  parser.add_argument('--header_out', '-g', metavar='MODNAME.h',
                      help='output filename for .h')
  parser.add_argument('--cc_flags', '-f', default='',
                      help='C++ compiler flags')
  parser.add_argument('--indent', default='  ',
                      help='Indentation token')
  parser.add_argument('input_filename', nargs=1,
                      help='CLIF input definition')
  args = parser.parse_args(argv[1:])
  if not args.prepend:
    args.prepend.append(sys.prefix+'/python/types.h')
  return args


class _ParseError(Exception):
  pass


class _BackendError(Exception):
  pass


def Err(ex):
  return ex.__class__.__name__+': '+str(ex)


def StripExt(filename):
  return os.path.splitext(filename)[0]


def GenerateFrom(ast):
  """Traverse ast and generate output files."""
  inc_headers = list(ast.usertype_includes)
  api_header = _GetHeaders(ast)
  modname = FLAGS.modname or StripExt(os.path.basename(ast.source
                                                      )).replace('-', '_')
  m = pyext.Module(
      modname,
      ast.typemaps,
      ast.namemaps,
      indent=FLAGS.indent)
  inc_headers.append(os.path.basename(FLAGS.header_out))
  # Order of generators is important.
  with open(FLAGS.ccdeps_out, 'w') as cout:
    gen.WriteTo(cout, m.GenerateBase(ast, inc_headers))
  with open(FLAGS.ccinit_out, 'w') as iout:
    gen.WriteTo(iout, m.GenerateInit(ast.source))
  with open(FLAGS.header_out, 'w') as hout:
    gen.WriteTo(hout, m.GenerateHeader(ast.source, api_header, ast.macros))


def _GetHeaders(ast):
  """Scan AST for header files."""
  # It's not moved to astutils yet because of asserts.
  included = set(d.cpp_file for d in ast.decls if d.cpp_file)
  if not included:
    return None
  if len(included) != 1:
    raise argparse.ArgumentError(
        'input_filename',
        'must have exactly one <<from "header":>> statement')
  wrap_header = included.pop()
  return wrap_header


def main():
  dump_path = None
  if FLAGS.dump_dir:
    try:
      if not stat.S_ISDIR(os.stat(FLAGS.dump_dir).st_mode):
        raise argparse.ArgumentError('--dump_dir', 'is not a directory')
    except OSError:
      os.mkdir(FLAGS.dump_dir, 0o755)
    iname = StripExt(FLAGS.input_filename[0])
    dump_path = os.path.join(FLAGS.dump_dir, os.path.basename(iname))
    if not FLAGS.ccdeps_out: FLAGS.ccdeps_out = dump_path+'.cc'
    if not FLAGS.ccinit_out: FLAGS.ccinit_out = dump_path+'_init.cc'
    if not FLAGS.header_out: FLAGS.header_out = dump_path+'.h'
  elif not (FLAGS.ccdeps_out and FLAGS.ccinit_out and FLAGS.header_out):
    raise argparse.ArgumentError(
        '', 'All 3 output files (-c, -i, -h) must be present')
  if not stat.S_IXUSR & os.stat(FLAGS.matcher_bin).st_mode:
    raise argparse.ArgumentError('--matcher_bin', 'requires an executable')
  try:
    with open(FLAGS.input_filename[0]) as pytd:
      try:
        bin_pb = _ParseClifSource(pytd, dump_path)
      except Exception as e:  # pylint: disable=broad-except
        print(Err(e))
        return 3
  except OSError as e:
    print(Err(e))
    return 2
  # Invoke backend matcher.
  matcher_cmd = [FLAGS.matcher_bin] + FLAGS.cc_flags.split()
  try:
    ast = _RunMatcher(matcher_cmd, bin_pb)
  except (OSError, _BackendError) as e:
    print(Err(e))
    return 4
  if FLAGS.dump_dir: _DumpProto(dump_path, '.opb', ast)
  # Check matcher output for errors.
  errors = False
  for d in ast.decls:
    if d.not_found:
      errors = True
      print(d.not_found)
  if errors:
    print('CLIF backend failed to compile C++ source headers')
    return 5
  try:
    GenerateFrom(ast)
  except Exception as e:  # pylint: disable=broad-except
    if FLAGS.nc_test:
      e = Err(e) + '\n'
      # pylint: disable=multiple-statements
      with open(FLAGS.ccdeps_out, 'w') as f: f.write(e)
      with open(FLAGS.ccinit_out, 'w') as f: f.write(e)
      with open(FLAGS.header_out, 'w') as f: f.write(e)
      print('A compilation error occurred while negative compilation'
            ' flag --nc-test is set, written to output files')
      return 0
    print(Err(e))
    return 7
  if FLAGS.nc_test:
    print('No compilation error occurred while negative compilation'
          ' flag --nc-test is set')
    return 8


def _ParseClifSource(stream, dump_path):
  """Parse PYTD into serialized protobuf."""
  init = ['type str = `UnicodeFromBytes` as bytes',
          'type unicode = `UnicodeFromBytes` as bytes',
          'from builtins import chr']
  p = pytd2proto.Postprocessor(config_headers=FLAGS.prepend,
                               include_paths=FLAGS.include_paths,
                               preamble='\n'.join(init))
  try:
    pb = p.Translate(stream)
  except Exception as e:  # pylint:disable=broad-except
    stream.seek(0)
    print('\nLine', '.123456789' * 4)
    for i, s in enumerate(stream):
      print('%4d:%s\\n' % (i+1, s.rstrip('\n')))
    stream.close()
    raise _ParseError(e)
  if FLAGS.dump_dir: _DumpProto(dump_path, '.ipb', pb)
  return pb.SerializeToString()


def _RunMatcher(command, data):
  """Spawn backend process to process data and capture output."""
  ast = ast_pb2.AST()  # Matcher output.
  # Debug print(' '.join(command))
  mrun = subprocess.Popen(command, stdin=PIPE, stdout=PIPE)
  astpb, e = mrun.communicate(data)
  rc = mrun.returncode
  if rc:
    raise _BackendError('Matcher failed with status %s' % rc)
  if e:
    raise _BackendError(e)
  if not astpb:
    raise _BackendError('Matcher failed with empty output')
  ast.ParseFromString(astpb)
  return ast


def _DumpProto(dump_path, ext, pb):
  if FLAGS.binary_dump:
    with open(dump_path+ext, 'wb') as f:
      f.write(pb.SerializeToString())
  else:
    with open(dump_path+ext, 'w') as f:
      f.write(google.protobuf.text_format.MessageToString(pb))


def start():  # pylint: disable=invalid-name
  global FLAGS
  FLAGS = _ParseCommandline(__doc__.splitlines()[0], sys.argv)
  sys.exit(main())


if __name__ == '__main__':
  start()
