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

r"""Generate CLIF extension C++ source for a protobuf.

PROTO -cOUTPATH/CCNAME \
      -hOUTPATH/HNAME  \
      --strip_dir=SYSPATH \
      SYSPATH/PKGPATH/NAME.proto

reads NAME.proto and generates C++ CCNAME source and HNAME header files.
"""
import argparse
import itertools
import sys
from clif.python import gen
from clif.python import types
from clif.python.utils import proto_util
VALID_EXT = ['.proto']

gen.PY3OUTPUT = None  # Generate version-agnostic headers.
FLAGS = None


class _ParseError(Exception):
  pass


def _ParseCommandline(doc, argv):
  """Define command-line flags and return parsed argv."""
  parser = argparse.ArgumentParser(description=doc, add_help=False)
  parser.add_argument('--source_dir', '-s', default='',
                      help=('The base of the source code tree to strip from'
                            ' file names.'))
  parser.add_argument('--strip_dir', '-d', default='',
                      help=('The base of the generated code tree to strip from'
                            ' file names.'))
  parser.add_argument('--ccdeps_out', '-c', help='output filename for base .cc')
  parser.add_argument('--header_out', '-h', help='output filename for .h')
  parser.add_argument('--allow_empty_package', action='store_true',
                      help=('Generate CLIF conversion library in ::clif '
                            'namespace, ADL will not work.'))
  parser.add_argument('protobuf', nargs=1)
  return parser.parse_args(argv[1:])


def _CppName(desc):
  """Return the fully qualified C++ name of the entity in |desc|."""
  return '::'+desc.fqname.replace('.', '::')


def _PyName(desc, pkg):
  """Return the Python name of the entity in |desc| from proto package |pkg|."""
  if not pkg: return desc.fqname
  assert desc.fqname.startswith(pkg)
  return desc.fqname[len(pkg)+1:]  # Add 1 for '.' between pkg and name.


def CreatePyTypeInfo(desc, path,
                     package_required=True, generate_service_info=False):
  """Create the type objects from the proto file descriptor in |desc|."""
  pypath = '' + path.replace('/', '.').replace('-', '_') + '_pb2'
  messages = []  # Proto messages.

  p = desc.PackageName()
  if p:
    n = '::'+p.replace('.', '::') + '::'
  else:
    if package_required:
      raise ValueError('Package statement required')
    n = '::'
  for m in desc.Messages():
    messages.append(types.ProtoType(_CppName(m), _PyName(m, p), pypath, ns=n))
  for e in desc.Enums():
    messages.append(types.ProtoEnumType(_CppName(e), _PyName(e, p), ns=n))
  if generate_service_info:
    for s in desc.Services():
      messages.append(types.CapsuleType(_CppName(s), _PyName(s, p), ns=n))
  return messages


def GenerateFrom(messages, proto_filename, clif_hdr, proto_hdr):
  """Traverse ast and generate output files."""
  with open(FLAGS.header_out, 'w') as hout:
    gen.WriteTo(hout, gen.Headlines(
        proto_filename, [proto_hdr, 'clif/python/postconv.h']))
    gen.WriteTo(hout, _GenHeader(messages))

  with open(FLAGS.ccdeps_out, 'w') as cout:
    gen.WriteTo(cout, gen.Headlines(
        proto_filename, ['clif/python/runtime.h',
                         'clif/python/types.h',
                         clif_hdr]))
    for ns, ts in itertools.groupby(messages, types.Namespace):
      if ns == '::':
        ns = 'clif'
      gen.WriteTo(cout, gen.TypeConverters(ns, ts))


def _GenHeader(messages):
  """Helper function for GenerateFrom."""
  for ns, ts in itertools.groupby(messages, types.Namespace):
    yield ''
    if ns == '::':
      ns = 'clif'
      yield gen.OpenNs(ns)
    else:
      yield gen.OpenNs(ns)
      yield 'using namespace ::clif;'
    yield ''
    for t in ts:
      for s in t.GenHeader():
        yield s
    yield ''
    yield gen.CloseNs(ns)


def main(_):
  assert FLAGS.ccdeps_out and FLAGS.header_out, ('Both output files '
                                                 '(-c, -h) must be specified.')
  assert not FLAGS.strip_dir.endswith('/')
  assert FLAGS.header_out.startswith(FLAGS.strip_dir)
  strip_dir = len(FLAGS.strip_dir)+1  # +1 for '/'
  hdr = FLAGS.header_out[strip_dir:]
  name = src = FLAGS.protobuf[0]
  assert not FLAGS.source_dir.endswith('/')
  if FLAGS.source_dir and name.startswith(FLAGS.source_dir):
    name = name[len(FLAGS.source_dir)+1:]  # +1 for '/'
  for ext in VALID_EXT:
    if name.endswith(ext):
      pypath = name[:-len(ext)]
      break
  else:
    raise NameError('Proto file should have any%s extension' % VALID_EXT)
  desc = proto_util.ProtoFileInfo(src, FLAGS.source_dir)
  if not desc:
    raise _ParseError(desc.ErrorMsg())
  messages = CreatePyTypeInfo(desc, pypath, not FLAGS.allow_empty_package)
  GenerateFrom(messages, name, hdr, pypath+'.pb.h')


def ParseFlags():
  global FLAGS
  FLAGS = _ParseCommandline(__doc__.splitlines()[0], sys.argv)


def Start():
  ParseFlags()
  main(0)


if __name__ == '__main__':
  Start()
