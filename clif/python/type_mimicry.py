"""Decorator for native class mimicing uninitializable extension type."""

from typing import Any, Generic, TypeVar

_T = TypeVar("_T", bound=type[Any])


class mimic_uninitializable_type(Generic[_T]):  # pylint: disable=invalid-name

  def __init__(self, uninitializable_type: _T):
    self._uninitializable_type = uninitializable_type

  def __call__(self, mimicing_type: type[Any]) -> _T:
    return mimicing_type
