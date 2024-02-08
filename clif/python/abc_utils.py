"""PyCLIF-pybind11 abc compatibility (in particular abc.ABCMeta).

This is for compatibility between the "default pybind11 metaclass"
(which is a custom metaclass) and https://docs.python.org/3/library/abc.html.

For background see:

* Description of https://github.com/pybind/pybind11/pull/5015

* Corresponding tests in clif/testing/python/classes_test.py
"""

import abc
import typing

from clif.python import _meta_ext

PyCLIFMeta = type(_meta_ext.empty)


if typing.TYPE_CHECKING:
  PyCLIFABCMeta = abc.ABCMeta
else:

  class PyCLIFABCMeta(abc.ABCMeta, PyCLIFMeta):
    pass
