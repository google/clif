"""Tests for imported_capsule."""

from absl.testing import absltest

from clif.testing.python import imported_capsule


class ImportedCapsuleTest(absltest.TestCase):

  def test_capsule_round_trip(self):
    c = imported_capsule.CreatePythonCapsule()
    self.assertEqual(imported_capsule.ConsumePythonCapsule(c), 10)


if __name__ == '__main__':
  absltest.main()
