"""Decorator for adding attributes (incl. methods) into extension classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


class _EmptyFromClass(object):
  pass

_EMPTY_FROM_CLASS_DICT_KEYS = frozenset(_EmptyFromClass.__dict__)


def _base_of_base_other_than_object(base):
  for bb in base.__bases__:
    if bb is not object:
      return bb
  return None


def _extend_from_dict(target_class, from_dict):
  for attr, value in from_dict.items():
    if attr not in _EMPTY_FROM_CLASS_DICT_KEYS:
      setattr(target_class, attr, value)


def extend(target_class):
  """Test & recommended use in ../testing/python/extend_methods_test.py."""
  def _(from_class):
    """Decorator implementation."""
    if not issubclass(from_class, object):
      # Must be new-style for Python 2 property setter to work.
      raise TypeError('extend from_class must be a new-style class.')
    for base in reversed(from_class.__bases__):
      if base is object:
        continue
      if not issubclass(base, object):
        raise TypeError(
            'extend base must be a new-style class (base %s is not).' %
            repr(base))
      if '__getattribute__' in base.__dict__:
        # Using builtin types like tuple, list, dict as bases leads to errors
        # such as
        # TypeError: descriptor '__getattribute__' for 'tuple' objects doesn't apply to '...' object  # pylint: disable=line-too-long
        # but only later when the target_class is instantiated or the objects
        # are used in certain ways.
        # Using __getattribute__ here as a signal to preempt such issues
        # immediately when a type is extended.
        # It is possible but seems highly unlikely that there are valid reasons
        # for adding __getattribute__ into extension types. If such cases
        # are encountered, this safety guard here can be modified accordingly.
        raise TypeError(
            'extend base must not have a __getattribute__ attribute'
            ' (base %s does).' % repr(base))
      bb = _base_of_base_other_than_object(base)
      if bb is not None:
        raise TypeError(
            'extend from_class base %s must not have bases themselves'
            ' (found base %s).' % (repr(base), repr(bb)))
      _extend_from_dict(target_class, base.__dict__)
    _extend_from_dict(target_class, from_class.__dict__)
    value = getattr(from_class, '__doc__')
    if value:
      setattr(target_class, '__doc__', value)
    # To ensure pickle.load() imports the module that extends target_class.
    # Important REQUIREMENT: target_class must be imported into
    # the from_class.__module__ with its unqualified name.
    target_class.__module__ = from_class.__module__
    return from_class
  return _
