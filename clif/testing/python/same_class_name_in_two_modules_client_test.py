from absl.testing import absltest

from clif.testing.python import same_class_name_in_two_modules_alpha as alpha
from clif.testing.python import same_class_name_in_two_modules_bravo as bravo
from clif.testing.python import same_class_name_in_two_modules_client as client


class AlphaTest(absltest.TestCase):

  def testPassAlphaSmith(self):
    obj = client.ReturnAlphaSmith()
    self.assertEqual(obj.WhereIsHome(), 'I live in Alphaville.')
    self.assertIsInstance(obj, alpha.Smith)

  def testPassBravoSmith(self):
    obj = client.ReturnBravoSmith()
    self.assertEqual(obj.WhereIsHome(), 'I live in Bravoville.')
    self.assertIsInstance(obj, bravo.Smith)


if __name__ == '__main__':
  absltest.main()
