from absl.testing import absltest

from clif.testing.python import final


class FinalTest(absltest.TestCase):

  def testCanUseSwigFinalAsFinal(self):
    swig_object = final.SwigFinal()
    capsule = swig_object.as_clif_testing_final_Final()
    self.assertEqual(type(capsule).__name__, 'PyCapsule')
    final.TakesFinal(swig_object)


if __name__ == '__main__':
  absltest.main()
