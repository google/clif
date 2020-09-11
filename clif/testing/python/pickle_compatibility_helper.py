"""Helper module for pickle_compatibility test.

Approach pioneered by cl/282753945 (and reused by cl/282918494).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


def ReduceStoreTwo(obj):
  return (obj.__class__, (obj.Get(0), obj.Get(1)))
