import unittest

from elements import *
from strategies import *

class TestStrategies(unittest.TestCase):

  def _trig_integral(self, name, coefficient=1):
    vset = VariableSet()
    var = vset.variable('x')
    arg = var if coefficient == 1 else Product(Number(coefficient), var)
    return Integral(TrigFunction(name, arg), var)

  def test_IntegrationStrategy(self):
    try:
      IntegrationStrategy()
    except:
      pass
    else:
      self.assertEqual('abstract class', 'instantiable')


  def test_ConstantTerm(self):
    vset = VariableSet()
    var = vset.variable()
    exp = Number(4)
    intg = Integral(exp, var)
    self.assertEqual(ConstantTerm.applicable(intg), True)
    res = ConstantTerm.apply(intg)
    self.assertEqual(res.a.a.n, 4)
    self.assertEqual(res.a.b, intg.var)
    self.assertEqual(isinstance(res.b, Variable), True)

    vset = VariableSet()
    var = vset.variable()
    exp = Product(Number(3), Number(4))
    intg = Integral(exp, var)
    self.assertEqual(ConstantTerm.applicable(intg), True)
    res = ConstantTerm.apply(intg).simplified()
    self.assertEqual(res.a.a.n, 12)
    self.assertEqual(res.a.b, intg.var)
    self.assertEqual(isinstance(res.b, Variable), True)

    vset = VariableSet()
    var = vset.variable()
    exp = Product(vset.variable(), Number(4))
    intg = Integral(exp, var)
    self.assertEqual(ConstantTerm.applicable(intg), False)


  def test_DistributeAddition(self):
    vset = VariableSet()
    var = vset.variable()
    exp = Sum(Number(4), vset.variable('y'))
    intg = Integral(exp, var)
    self.assertEqual(DistributeAddition.applicable(intg), True)
    res = DistributeAddition.apply(intg)
    self.assertEqual(isinstance(res, Sum), True)
    self.assertEqual(res.a.a.exp.n, 4)
    self.assertEqual(res.a.a.var.symbol(), 'A')
    self.assertEqual(res.a.b.exp.symbol(), 'y')
    self.assertEqual(res.a.b.var.symbol(), 'A')


  def test_ConstantPower(self):
    vset = VariableSet()
    var = vset.variable()
    var2 = vset.variable()
    exp = Power(var, Number(2))
    intg = Integral(exp, var2)
    self.assertEqual(ConstantPower.applicable(intg), False)

    vset = VariableSet()
    var = vset.variable()
    exp = Power(var, Number(2))
    intg = Integral(exp, var)
    self.assertEqual(ConstantPower.applicable(intg), True)
    res = ConstantPower.apply(intg).simplified()
    self.assertEqual(isinstance(res.a, Product), True)
    self.assertEqual(isinstance(res.a.a, Fraction), True)
    self.assertEqual(res.a.a.numr, 1)
    self.assertEqual(res.a.a.denr, 3)
    self.assertEqual(res.a.b.base, var)
    self.assertEqual(res.a.b.exponent.n, 3)

  def test_SimpleTrig(self):
    intg = self._trig_integral('sin', 3)
    self.assertEqual(SimpleTrig.applicable(intg), True)
    res = SimpleTrig.apply(intg)
    self.assertEqual(isinstance(res.a, Fraction), True)
    self.assertEqual(res.a.denr, Number(3))

    intg = self._trig_integral('cos')
    self.assertEqual(SimpleTrig.applicable(intg), True)
    self.assertEqual(SimpleTrig.apply(intg).a, TrigFunction('sin', intg.var))

  def test_TrigSquare(self):
    intg = self._trig_integral('sec', 2)
    intg.exp = Power(intg.exp, Number(2))
    self.assertEqual(TrigSquare.applicable(intg), True)

  def test_TrigProduct(self):
    intg = self._trig_integral('sec', 4)
    intg.exp = Product(intg.exp, TrigFunction('tan', intg.exp.arg))
    self.assertEqual(TrigProduct.applicable(intg), True)

  def test_WinstonSlagleExample(self):
    from parseintg import parse
    intg = parse('int x^4/(1-x^2)^(5/2) dx')
    self.assertEqual(WinstonSlagleExample.applicable(intg), True)
    result = WinstonSlagleExample.apply(intg)
    self.assertEqual(isinstance(result, Sum), True)
    self.assertEqual('asin(x)' in repr(result), True)

  def test_ScreenshotExamples(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problems = [
      'int 1/(1+x^4)^2 dx',
      'int cos(x)/(1+sin(x)^2)^2 dx',
      'int x^4/(1-x^2)^(5/2) dx',
      'int x^2/sqrt(1-x^2) dx',
      'int x*ln(x) dx',
      'int tan(x)^5*sec(x)^2 dx',
      'int exp(2*x)/(1+exp(x)) dx',
      'int 1/(x*sqrt(1+x^2)) dx',
      'int sin(x)^2*cos(x)^4 dx',
      'int 2^x dx',
      'int 1/(1+x^2) dx',
      'int 1/sqrt(1-x^2) dx',
      'int sin(x)^3 dx',
      'int 1/(x^2-1) dx',
      'int cos(3*x+5) dx',
      'int x*sqrt(1+x) dx',
      'int cos(sqrt(x)) dx']
    for problem in problems:
      result = attempt_integral(parse(problem), SubLogger('test'))
      self.assertEqual('int[' in repr(result), False, problem)


if __name__ == "__main__":
  unittest.main()
