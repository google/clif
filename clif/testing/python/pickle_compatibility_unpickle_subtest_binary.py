"""Subtest of pickle_compatibility_test."""

import base64
import pickle
import sys

# NO google3 imports here: pickle.loads() will do the imports.


def unpickle_subtest():
  b64blob = sys.stdin.read()
  serialized = base64.b64decode(b64blob)
  deserialized = pickle.loads(serialized)
  reduced = deserialized.__reduce_ex__(0)  # A method added with @extend.
  print('L=%d N=%s A=%s' % (
      len(reduced), reduced[0].__name__, tuple(reversed(reduced[1]))))


if __name__ == '__main__':
  assert len(sys.argv) == 1
  unpickle_subtest()
