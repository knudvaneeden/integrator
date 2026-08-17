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
    exp = Product(var, Number(4))
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
    self.assertEqual(res.a.a.include_constant, False)
    self.assertEqual(res.a.b.include_constant, False)

  def test_ExactlyOneIntegrationConstantForSums(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    expected = {
      'int 4 - x^2 dx': '(((4 * x) + (-1 * ((1 / 3) * (x ^ 3)))) + C)',
      'int 2 * x^2 - x^3 dx':
        '(((2 * ((1 / 3) * (x ^ 3))) + (-1 * ((1 / 4) * (x ^ 4)))) + C)',
      'int 1 + x + x^2 + x^3 dx':
        '(((((1 * x) + ((1 / 2) * (x ^ 2))) + '
        '((1 / 3) * (x ^ 3))) + ((1 / 4) * (x ^ 4))) + C)'}
    for problem, result_repr in expected.items():
      result = attempt_integral(parse(problem), SubLogger('test'))
      self.assertEqual(repr(result), result_repr, problem)
      self.assertEqual(sum(repr(result).count(symbol) for symbol in 'ABC'), 1,
        problem)


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

  def test_ReciprocalXSquaredQuadraticSquareRoot(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    cases = [
      'int 1 / ( x^2 * sqrt( x^2 + 4 ) ) dx',
      'int 5 / ( x^2 * sqrt( 3 * x^2 + 7 ) ) dx']
    for problem in cases:
      integral = parse(problem)
      self.assertEqual(
        ReciprocalXSquaredQuadraticSquareRoot.applicable(integral), True,
        problem)
      result = attempt_integral(integral, SubLogger('test'))
      self.assertEqual('int[' in repr(result), False, problem)

  def test_ArcTangentAffineSquareRoot(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    cases = [
      'int arctan( sqrt( x ) ) dx',
      'int arctan( sqrt( 3 * x + 2 ) ) dx']
    for problem in cases:
      integral = parse(problem)
      self.assertEqual(ArcTangentAffineSquareRoot.applicable(integral), True,
        problem)
      result = attempt_integral(integral, SubLogger('test'))
      self.assertEqual('int[' in repr(result), False, problem)

  def test_TrigNonnegativeIntegerPowerReduction(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    requested = attempt_integral(parse('int cos( x )^4 dx'), SubLogger('test'))
    requested_repr = repr(requested)
    self.assertEqual('int[' in requested_repr, False)
    self.assertEqual('(cos(x) ^ 3)' in requested_repr, True)
    self.assertEqual('((3 * (sin(x) * cos(x))) / 8)' in requested_repr, True)
    self.assertEqual('((3 * x) / 8)' in requested_repr, True)
    for problem in ['int sin( 3 * x + 2 )^6 dx',
      'int cos( 5 * x - 1 )^7 dx']:
      result = attempt_integral(parse(problem), SubLogger('test'))
      self.assertEqual('int[' in repr(result), False, problem)

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
      'int cos(x)/(1+sin(x))^2 dx',
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
      'int 1/(1-x^2) dx',
      'int cos(3*x+5) dx',
      'int x*sqrt(1+x) dx',
      'int cos(sqrt(x)) dx']
    for problem in problems:
      result = attempt_integral(parse(problem), SubLogger('test'))
      self.assertEqual('int[' in repr(result), False, problem)
  def test_VersionFiveExamples(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problems = [
      'int x*exp(x)^2 dx', 'int ln(x) dx', 'int log(x) dx',
      'int arcsin(x) dx', 'int arccos(x) dx', 'int arctan(x) dx',
      'int arccot(x) dx', 'int arcsec(x) dx', 'int arccsc(x) dx',
      'int x^c dx', 'int sec(x)*tan(x) dx', 'int csc(x)*cot(x) dx',
      'int sin(m*x)*cos(n*x) dx', 'int sin(m*x)*sin(n*x) dx',
      'int cos(m*x)*cos(n*x) dx', 'int x/(x^2+x) dx']
    for problem in problems:
      result = attempt_integral(parse(problem), SubLogger('test'))
      self.assertEqual('int[' in repr(result), False, problem)

  def test_PolynomialDerivativeExponentialSubstitutionOriginal(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int x exp(x^2) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result), '((exp((x ^ 2)) / 2) + C)')

  def test_PolynomialDerivativeExponentialSubstitutionGeneral(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( 6 * x^2 + 2 ) * exp( 2 * x^3 + 2 * x + 1 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)

  def test_RationalPowerTimesExponentialPowerSubstitution(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    requested = 'int sqrt( x ) * exp( sqrt( x ) ) dx'
    result = attempt_integral(parse(requested), SubLogger('test'))
    self.assertEqual(repr(result),
      '((2 * (exp((x ^ (1 / 2))) * ((x + (-2 * (x ^ (1 / 2)))) + 2))) + C)')

    general_cases = [
      'int x^(5/2) * exp( 3 * sqrt( x ) + 2 ) dx',
      'int x^(-1/3) * exp( 2 * x^(1/3) ) dx',
      'int 4 * x^3 * exp( 2 * x^2 - 1 ) dx']
    for problem in general_cases:
      result = attempt_integral(parse(problem), SubLogger('test'))
      self.assertEqual('int[' in repr(result), False, problem)
    self.assertEqual('exp(' in repr(result), True)

  def test_TrigBinomialPowerSubstitutionOriginal(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int cos( 3 * x ) / ( 1 - sin( 3 * x ))^2 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '((((1 + (-1 * sin((3 * x)))) ^ -1) / 3) + C)')

  def test_TrigBinomialPowerSubstitutionGeneralCosineDerivative(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 5 * cos( 2 * x + 1 ) * ( 3 + 7 * sin( 2 * x + 1 ) )^4 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)

  def test_TrigBinomialPowerSubstitutionGeneralSineDerivative(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int sin( 4 * x ) / ( 2 + 3 * cos( 4 * x ) ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('ln(' in repr(result), True)

  def test_ConstantPlusCosine(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 2 + cos( x ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)

  def test_SecSquaredRationalTangent(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int sec(x)^2 / ( 1 + sec( x )^2 - 3 * tan( x ) ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '((ln((tan(x) + -2)) + (-1 * ln((tan(x) + -1)))) + C)')

  def test_ReciprocalSecSquared(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 1 / sec( x )^2 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '(((x / 2) + (sin((2 * x)) / 4)) + C)')

  def test_LinearOverQuadraticSquareRootPositiveOriginal(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int x / sqrt( x^2 + 2 * x + 5 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '((((((x ^ 2) + (2 * x)) + 5) ^ (1 / 2)) + (-1 * ln((((((x ^ 2) + (2 * x)) + 5) ^ (1 / 2)) + (x + 1))))) + C)')

  def test_LinearOverQuadraticSquareRootPositiveGeneral(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( 3 * x - 2 ) / sqrt( 2 * x^2 + 5 * x + 7 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('ln(' in repr(result), True)

  def test_ExponentialOverLinearQuotientDerivativeOriginal(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int x * exp( x ) / ( 1 + x )^2 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result), '((exp(x) / (1 + x)) + C)')

  def test_ExponentialOverLinearQuotientDerivativeGeneral(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( 6 * x + 1 ) * exp( 3 * x + 2 ) / ( 2 * x + 1 )^2 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)

  def test_CompositeSquareSubstitution(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = ('int (arcsin(x) + sin(x))^2 * '
      '((1 - x^2)^(-1/2) + cos(x)) dx')
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '(((1 / 3) * ((arcsin(x) + sin(x)) ^ 3)) + C)')

  def test_PolynomialTimesAffinePowerReplacesOldSquareRootRule(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( x^2 + x ) / sqrt( x ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '((((2 * (x ^ (5 / 2))) / 5) + ((2 * (x ^ (3 / 2))) / 3)) + C)')

  def test_PolynomialTimesAffinePowerOverSquareRoot(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( x^2 + 1 ) / sqrt( x ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '((((2 * (x ^ (5 / 2))) / 5) + (2 * (x ^ (1 / 2)))) + C)')

  def test_LinearOverQuadraticSquareRootNegativeOriginal(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( x + 1 ) / sqrt( 2 * x - x^2 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '(((-1 * (((2 * x) + (-1 * (x ^ 2))) ^ (1 / 2))) + (2 * arcsin((x + -1)))) + C)')

  def test_PolynomialTimesRationalPowerBinomialExpansion(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    original = 'int x * ( x^(1/2) + x^(-1/2) )^2 dx'
    result = attempt_integral(parse(original), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False, original)
    self.assertEqual(repr(result),
      '(((((x ^ 3) / 3) + (x ^ 2)) + x) + C)')

    requested = 'int x * ( 1 - sqrt( x ) )^2 dx'
    result = attempt_integral(parse(requested), SubLogger('test'))
    self.assertEqual(repr(result),
      '(((((x ^ 3) / 3) + ((-4 * (x ^ (5 / 2))) / 5)) + '
      '((x ^ 2) / 2)) + C)', requested)

    general_cases = [
      'int ( 2 + 3 * x^2 ) * ( 1 - 2 * x^(1/3) )^4 dx',
      'int ( x^(-2) + 1 ) * ( 3 * x^(2/3) + 2 * x^(-1/2) )^3 dx',
      'int x^(-1) * ( 1 + sqrt( x ) )^2 dx']
    for problem in general_cases:
      result = attempt_integral(parse(problem), SubLogger('test'))
      self.assertEqual('int[' in repr(result), False, problem)

  def test_ExponentialRationalSubstitution(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int exp( 6 * x ) / ( exp( 4 * x ) + 1 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '(((1 / 2) * (exp((2 * x)) + (-1 * arctan(exp((2 * x)))))) + C)')

  def test_ExponentialBinomialLogSubstitutionOriginal(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int exp( 2 * x ) * ln( 1 + exp( 2 * x ) ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '(((((1 + exp((2 * x))) * ln((1 + exp((2 * x))))) + (-1 * (1 + exp((2 * x))))) / 2) + C)')

  def test_ExponentialBinomialLogSubstitutionGeneral(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 5 * exp( 3 * x + 1 ) * ln( 2 + 7 * exp( 3 * x + 1 ) ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('ln(' in repr(result), True)

  def test_OneOverOnePlusCosine(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 1 / ( 1 + cos( x ) ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result), '(tan((x / 2)) + C)')

  def test_ReciprocalCosSquared(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 1 / cos( x )^2 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result), '(tan(x) + C)')

  def test_PolynomialTimesAffinePowerReplacesVariableLinearBinomial(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int x * ( x + 1 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '((((x ^ 3) / 3) + ((x ^ 2) / 2)) + C)')

  def test_XSquared(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    result = attempt_integral(parse('int x^2 dx'), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result), '(((1 / 3) * (x ^ 3)) + C)')

  def test_TrigBinomialPowerReplacesSineSquaredTimesCosine(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int sin( x )^2 * cos( x ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result), '(((sin(x) ^ 3) / 3) + C)')

  def test_SineFourthCosineFourth(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int sin( x )^4 * cos( x )^4 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '(((((3 / 128) * x) + ((-1 / 128) * sin((4 * x)))) + (sin((8 * x)) / 1024)) + C)')

  def test_TangentIntegerPowerReductionSineCosineForm(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int sin( x )^4 / cos( x )^4 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '(((((tan(x) ^ 3) / 3) + (-1 * tan(x))) + x) + C)')

  def test_TangentIntegerPowerReductionCotangentForm(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 1 / cot( x )^4 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '(((((tan(x) ^ 3) / 3) + (-1 * tan(x))) + x) + C)')

  def test_TangentIntegerPowerReductionGeneral(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int tan( 3 * x + 1 )^6 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('(tan(((3 * x) + 1)) ^ 5)' in repr(result), True)

  def test_RationalEvenFourthProduct(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 32 * x^4 / ( ( 1 + x^2 ) * ( 1 - x^2 ) )^4 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('ln((x + -1))' in repr(result), True)
    self.assertEqual('atan(x)' in repr(result), True)

  def test_LaurentPolynomialOverOnePlusSquareQuartic(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int x^4 / ( 1 + x^2 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '(((((x ^ 3) / 3) + (-1 * x)) + atan(x)) + C)')

  def test_LaurentPolynomialOverOnePlusSquareGeneral(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( 3 * x^7 - 2 * x^3 + 5 ) / ( 1 + x^2 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    rendered = repr(result)
    self.assertEqual('ln((1 + (x ^ 2)))' in rendered, True)
    self.assertEqual('(5 * atan(x))' in rendered, True)

  def test_LaurentPolynomialOverOnePlusSquareNegativeEven(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( 1 / x^4 / ( 1 + x^2 ) ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '((((-1 * ((x ^ -3) / 3)) + (x ^ -1)) + atan(x)) + C)')

  def test_LaurentPolynomialOverOnePlusSquareNegativeOdd(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int x^(-3) / ( 1 + x^2 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    rendered = repr(result)
    self.assertEqual('ln(x)' in rendered, True)
    self.assertEqual('ln((1 + (x ^ 2)))' in rendered, True)

  def test_QuadraticDerivativePowerSubstitutionSquareRoot(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int x * sqrt( x^2 + 16 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '(((((x ^ 2) + 16) ^ (3 / 2)) / 3) + C)')

    reciprocal_root = 'int x / sqrt( x^2 - 15 ) dx'
    result = attempt_integral(parse(reciprocal_root), SubLogger('test'))
    self.assertEqual(repr(result),
      '((((x ^ 2) + -15) ^ (1 / 2)) + C)', reciprocal_root)

  def test_QuadraticDerivativePowerSubstitutionGeneralPower(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( 6 * x + 2 ) * ( 3 * x^2 + 2 * x + 5 )^4 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('^ 5' in repr(result), True)

  def test_QuadraticDerivativePowerSubstitutionLogarithm(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( 6 * x + 2 ) / ( 3 * x^2 + 2 * x + 5 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('ln(' in repr(result), True)

  def test_PolynomialTimesAffinePowerSubstitutionSquareRoot(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int x * sqrt( 1 + x ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '((((2 * ((1 + x) ^ (5 / 2))) / 5) + ((-2 * ((1 + x) ^ (3 / 2))) / 3)) + C)')

  def test_PolynomialTimesAffinePowerSubstitutionGeneral(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( 2 * x^3 - x + 4 ) * ( 3 * x + 2 )^( 2 / 3 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)

  def test_PolynomialTimesAffinePowerSubstitutionLogarithm(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( x^2 + 1 ) / ( 2 * x + 3 )^3 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('ln(' in repr(result), True)

  def test_AffineSquareRootTrigSubstitutionCosine(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int cos( sqrt( x ) ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '(((2 * ((x ^ (1 / 2)) * sin((x ^ (1 / 2))))) + (2 * cos((x ^ (1 / 2))))) + C)')

  def test_AffineSquareRootTrigSubstitutionShiftedCosine(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int cos( 3 * sqrt( x ) + 2 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('sin(' in repr(result), True)

  def test_AffineSquareRootTrigSubstitutionShiftedSine(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int sin( 2 * sqrt( x ) - 1 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('cos(' in repr(result), True)

  def test_SineCosineLinearCombination(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int sin( x ) + cos( x ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result), '(((-1 * cos(x)) + sin(x)) + C)')

  def test_SineCosineLinearCombinationScaledShifted(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 3 * sin( 2 * x + 1 ) - 5 * cos( 2 * x + 1 ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('cos(' in repr(result), True)
    self.assertEqual('sin(' in repr(result), True)

  def test_SineCosineLinearCombinationReversed(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int cos( 4 * x ) + 2 * sin( 4 * x ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)

  def test_SquaredSineCosineCombination(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( sin( x ) + cos( x ) )^2 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result),
      '((x + (-1 * (cos((2 * x)) / 2))) + C)')

  def test_SquaredSineCosineCombinationScaledShifted(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( 2 * sin( 3 * x + 1 ) - 5 * cos( 3 * x + 1 ) )^2 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('sin(' in repr(result), True)
    self.assertEqual('cos(' in repr(result), True)

  def test_SquaredSineCosineCombinationReversed(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int ( cos( 2 * x ) + 3 * sin( 2 * x ) )^2 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)

  def test_TangentPowerSecantSquaredSubstitution(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int tan( x ) * sec( x )^2 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result), '(((tan(x) ^ 2) / 2) + C)')

  def test_TangentPowerSecantSquaredSubstitutionScaledShifted(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 3 * tan( 2 * x + 1 )^4 * sec( 2 * x + 1 )^2 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('^ 5' in repr(result), True)

  def test_TangentPowerSecantSquaredSubstitutionLogarithm(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int sec( 5 * x )^2 / tan( 5 * x ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('ln(tan((5 * x)))' in repr(result), True)

  def test_ExponentialBinomialPowerSubstitutionLogarithm(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int exp( x) / ( 1 + exp( x ) ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual(repr(result), '(ln((1 + exp(x))) + C)')

  def test_ExponentialBinomialPowerSubstitutionScaledShifted(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 3 * exp( 2 * x + 1 ) / ( 5 + 7 * exp( 2 * x + 1 ) ) dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('ln(' in repr(result), True)

  def test_ExponentialBinomialPowerSubstitutionGeneralPower(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problem = 'int 4 * exp( 3 * x ) * ( 2 + 5 * exp( 3 * x ) )^2 dx'
    result = attempt_integral(parse(problem), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('^ 3' in repr(result), True)

  def test_RequestedExampleChecklistVersion49(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    examples = [
      'int exp( x) / ( 1 + exp( x ) ) dx',
      'int ( sin( x )^2 + 1 )^2 dx',
      'int exp( 2 * x ) / ( 1 + exp( x ) ) dx',
      'int 1 / ( 1 - cos( x ) ) dx',
      'int tan( x ) * sec( x )^2 dx',
      'int x * ln( x ) dx',
      'int ( x + 1 ) / sqrt( 2 * x - x^2 ) dx',
      'int 2 * exp( x ) / ( 2 + 3 * exp( 2 * x ) ) dx',
      'int x^4 / ( 1 - x^2 )^(5/2) dx',
      'int sec( x )^2 / ( 1 + sec( x )^2 - 3 * tan( x ) ) dx',
      'int exp( 6 * x ) / ( exp( 4 * x ) + 1 ) dx',
      'int ( 2 + 3 * x^2 ) dx',
      'int exp( x ) * cos( x ) dx',
      'int exp( x ) * sin( x ) dx',
      'int 2 * exp( x ) * cos( x ) dx',
      'int sec( x )^n dx',
      'int sec( x )^3 dx',
      'int cos( sqrt( x ) ) dx',
      'int 1 / sqrt( x^2 + m^2 + x ) dx',
      'int sec( x )^2 * tan( x ) dx']
    for problem in examples:
      result = attempt_integral(parse(problem), SubLogger('test'))
      self.assertEqual('int[' in repr(result), False, problem)

  def test_TrigSquareBinomialIntegerPower(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    result = attempt_integral(parse('int ( sin( x )^2 + 1 )^2 dx'), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)

  def test_ReciprocalOneMinusCosine(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    result = attempt_integral(parse('int 1 / ( 1 - cos( x ) ) dx'), SubLogger('test'))
    self.assertEqual(repr(result), '((-1 * cot((x / 2))) + C)')

  def test_ExponentialQuadraticDenominatorSubstitution(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    result = attempt_integral(parse(
      'int 2 * exp( x ) / ( 2 + 3 * exp( 2 * x ) ) dx'), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('arctan(' in repr(result), True)

  def test_ExponentialTrigProductBothFunctions(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    for problem in ['int exp( x ) * cos( x ) dx',
                    'int exp( x ) * sin( x ) dx',
                    'int 2 * exp( x ) * cos( x ) dx']:
      self.assertEqual('int[' in repr(attempt_integral(
        parse(problem), SubLogger('test'))), False, problem)

  def test_PolynomialSineCosineProduct(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problems = [
      'int x * sin( x ) * cos( x ) dx',
      'int ( x^2 + 2 * x + 3 ) * sin( 2 * x + 1 ) * cos( 3 * x - 4 ) dx',
      'int x^3 * sin( 2 * x ) * cos( 2 * x ) dx']
    for problem in problems:
      result = attempt_integral(parse(problem), SubLogger('test'))
      self.assertEqual('int[' in repr(result), False, problem)
    requested = attempt_integral(parse(problems[0]), SubLogger('test'))
    self.assertEqual(repr(requested),
      '((((-1 * ((x * cos((x + x))) / 2)) + ((sin((x + x)) / 2) / 2)) / 2) + C)')

  def test_OddSineCosinePowerSubstitution(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    problems = [
      'int sin( x )^3 * cos( x )^3 dx',
      'int sin( x )^(1/3) * cos( x )^3 dx',
      'int sin( x )^(1/3) * cos( x )^3 * tan( x )^2 dx',
      'int sin( 2 * x + 1 )^(2/3) * cos( 2 * x + 1 )^5 dx',
      'int sin( 3 * x - 2 )^5 * cos( 3 * x - 2 )^(4/3) dx',
      'int sin( 2 * x + 1 )^(2/5) * cos( 2 * x + 1 )^5 * tan( 2 * x + 1 )^2 dx',
      'int sin( 3 * x - 2 )^5 * cos( 3 * x - 2 )^(1/2) * tan( 3 * x - 2 )^2 dx']
    for problem in problems:
      result = attempt_integral(parse(problem), SubLogger('test'))
      self.assertEqual('int[' in repr(result), False, problem)

    first = attempt_integral(parse(problems[0]), SubLogger('test'))
    second = attempt_integral(parse(problems[1]), SubLogger('test'))
    third = attempt_integral(parse(problems[2]), SubLogger('test'))
    self.assertEqual(repr(first),
      '((((sin(x) ^ 4) / 4) + (-1 * ((sin(x) ^ 6) / 6))) + C)')
    self.assertEqual(repr(second),
      '((((3 * (sin(x) ^ (4 / 3))) / 4) + '
      '((-3 * (sin(x) ^ (10 / 3))) / 10)) + C)')
    self.assertEqual(repr(third), '(((3 * (sin(x) ^ (10 / 3))) / 10) + C)')

  def test_SecantPowerIntegerAndSymbolic(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    integer_result = attempt_integral(parse('int sec( x )^3 dx'), SubLogger('test'))
    symbolic_result = attempt_integral(parse('int sec( x )^n dx'), SubLogger('test'))
    self.assertEqual('int[' in repr(integer_result), False)
    self.assertEqual('hypergeometric2F1' in repr(symbolic_result), True)

  def test_MonicQuadraticParameterSquareRoot(self):
    from parseintg import parse
    from solver import attempt_integral
    from sublogger import SubLogger
    result = attempt_integral(parse(
      'int 1 / sqrt( x^2 + m^2 + x ) dx'), SubLogger('test'))
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('ln(' in repr(result), True)

  def test_AndOrGraph(self):
    from parseintg import parse
    from solver import attempt_integral, AndOrGraph
    from sublogger import SubLogger
    intg = parse('int x*exp(x)^2 dx')
    graph = AndOrGraph(intg.latex())
    result = attempt_integral(intg, SubLogger('test'), graph)
    graph_text = repr(graph.as_dict())
    self.assertEqual('int[' in repr(result), False)
    self.assertEqual('OR: choose an integration rule' in graph_text, True)
    self.assertEqual('AND: solve both addends' in graph_text, True)
    self.assertEqual('chosen' in graph_text, True)

  def test_AndOrGraphExpressionsAreLatex(self):
    from parseintg import parse
    from solver import attempt_integral, AndOrGraph
    from sublogger import SubLogger
    intg = parse('int x^2 dx')
    graph = AndOrGraph(intg.latex())
    attempt_integral(intg, SubLogger('test'), graph)
    self.assertEqual(graph.root['label'], r'\int{{x}^{2}}\;dx')
    expression_nodes = [node for node in graph.root['children']
                        if node['kind'] == 'expression']
    self.assertEqual(len(expression_nodes) > 0, True)


if __name__ == "__main__":
  unittest.main()
