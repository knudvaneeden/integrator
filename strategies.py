"""
Integration Strategies

This file is a booklet of strategies for
solving integration problems.

Each strategy is a subtype of IntegrationStrategy
and can apply itself to an expression.
"""

from elements import *
from fractions import Fraction as Rational
from math import comb

# add on integration uncertainty variable
def add_integration_constant(expr, original_intg):
  return Sum(expr, original_intg.var.vset.new_variable(suggest='C'))


def is_constant(expr, var) :
  """
  Test whether the expression is constant with respect to the variable.
  """
  if expr.is_a(Number) :
    return True
  elif expr.is_a(Variable) :
    return (expr != var)
  elif expr.is_a(Sum) or expr.is_a(Product):
    return is_constant(expr.a, var) and is_constant(expr.b, var)
  elif expr.is_a(Fraction):
    return is_constant(expr.numr, var) and is_constant(expr.denr, var)
  elif expr.is_a(Power):
    return is_constant(expr.base, var) and is_constant(expr.exponent, var)
  elif expr.is_a(Logarithm) or expr.is_a(TrigFunction):
    return is_constant(expr.arg, var)
  else :
    return False


def linear_coefficient(expr, var):
  """Return d(expr)/d(var) when it is constant, otherwise return None."""
  if is_constant(expr, var):
    return Number(0)
  if expr == var:
    return Number(1)
  if expr.is_a(Sum):
    a = linear_coefficient(expr.a, var)
    b = linear_coefficient(expr.b, var)
    if a != None and b != None:
      return Sum(a, b).simplified()
  if expr.is_a(Product):
    if is_constant(expr.a, var):
      b = linear_coefficient(expr.b, var)
      if b != None: return Product(expr.a, b).simplified()
    if is_constant(expr.b, var):
      a = linear_coefficient(expr.a, var)
      if a != None: return Product(a, expr.b).simplified()
  if expr.is_a(Fraction) and is_constant(expr.denr, var):
    numr = linear_coefficient(expr.numr, var)
    if numr != None: return Fraction(numr, expr.denr).simplified()
  return None


class IntegrationStrategy(object):
  def __init__(self):
    raise NotImplementedError("Strategy is an abstract class")

  def apply(exp):
    raise NotImplementedError("apply not implemented")


class ConstantTerm(IntegrationStrategy):
  example = "int 4 dx = 4x + C"
  description = "integral of a constant term"

  @classmethod
  def applicable(self, intg):
    return is_constant(intg.exp, intg.var)

  @classmethod
  def apply(self, intg):
    exp = intg.exp.simplified()
    return add_integration_constant(Product(exp, intg.var), intg)


class ConstantFactor(IntegrationStrategy):
  example = "int 4x dx = 4 * int x dx"
  description = "integral with a constant factor"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Product)
      and (is_constant(exp.a, intg.var)
        or is_constant(exp.b, intg.var)))

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    integrand, constant_factor = sorted([exp.a, exp.b], key=lambda e: is_constant(e, intg.var) )
    return Product(constant_factor, Integral(integrand, intg.var))


class ConstantDivisor(IntegrationStrategy):
  example = "int x/4 dx = 1/4 * int x dx"
  description = "integral with a constant divisor"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Fraction)
      and (is_constant(exp.denr, intg.var)))

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    return Product(Fraction(Number(1), exp.denr), Integral(exp.numr, intg.var))


class SimpleIntegral(IntegrationStrategy):
  example = "int x dx = 1/2 x^2 + C"
  description = "integral of the integration variable occuring by itself"

  @classmethod
  def applicable(self, intg):
    expr = intg.simplified().exp
    return expr.is_a(Variable) and (expr is intg.var)

  @classmethod
  def apply(self, intg):
    expr = intg.simplified().exp
    half = Fraction(Number(1), Number(2))
    new_expr = Product(half, Power(expr, Number(2)))
    return add_integration_constant(new_expr, intg)


class ConstantPower(IntegrationStrategy):
  example = "int x^3 dx = 1/4 x^4 + C"
  description = "integral with a constant exponent"

  @classmethod
  def applicable(self, intg):
    expr = intg.simplified().exp
    return (expr.is_a(Power)
      and expr.base.is_a(Variable)
      and (expr.base.symbol == intg.var.symbol)
      and is_constant(expr.exponent, intg.var))

  @classmethod
  def apply(self, intg):
    expr = intg.simplified().exp
    # TODO: Do not use floating point reciprocal, use fraction instead.
    n_plus_one = Sum(expr.exponent, Number(1)).simplified()
    recip_n = n_plus_one.reciprocal()
    new_expr = Product(recip_n, Power(intg.var, n_plus_one))
    return add_integration_constant(new_expr, intg)


class DistributeAddition(IntegrationStrategy):
  example = "int x + x^2 dx = int x dx + int x^2 dx"
  description = "integral of sums to sum of integrals"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return exp.is_a(Sum)

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    new_expr = Sum(Integral(exp.a, intg.var), Integral(exp.b, intg.var))
    return add_integration_constant(new_expr, intg)

class OneOverX(IntegrationStrategy):
  description = "The integral of 1/x is ln(x)."

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Fraction)
      and is_constant(exp.numr, intg.var)
      and (exp.denr == intg.var))

  @classmethod
  def apply(self, intg):
    return Product(intg.simplified().exp.numr, Logarithm(intg.var))


class SimpleTrig(IntegrationStrategy):
  example = "int sin(3*x+2) dx = -cos(3*x+2)/3 + C"
  description = "standard trigonometric integral with a linear argument"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(TrigFunction)
        or exp.name not in ['sin', 'cos', 'tan', 'sec', 'csc', 'cot']):
      return False
    coefficient = linear_coefficient(exp.arg, intg.var)
    return coefficient != None and coefficient != Number(0)

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    coefficient = linear_coefficient(exp.arg, intg.var)
    if exp.name == 'sin':
      primitive = Product(Number(-1), TrigFunction('cos', exp.arg))
    elif exp.name == 'cos':
      primitive = TrigFunction('sin', exp.arg)
    elif exp.name == 'tan':
      primitive = Product(Number(-1), Logarithm(TrigFunction('cos', exp.arg)))
    elif exp.name == 'cot':
      primitive = Logarithm(TrigFunction('sin', exp.arg))
    elif exp.name == 'sec':
      primitive = Logarithm(Sum(TrigFunction('sec', exp.arg),
        TrigFunction('tan', exp.arg)))
    else: # csc
      primitive = Product(Number(-1), Logarithm(Sum(TrigFunction('csc', exp.arg),
        TrigFunction('cot', exp.arg))))
    return add_integration_constant(Fraction(primitive, coefficient).simplified(), intg)


class TrigSquare(IntegrationStrategy):
  description = "integral of secant squared or cosecant squared"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Power) and exp.exponent == Number(2)
      and exp.base.is_a(TrigFunction) and exp.base.name in ['sec', 'csc']
      and linear_coefficient(exp.base.arg, intg.var) not in [None, Number(0)])

  @classmethod
  def apply(self, intg):
    trig = intg.simplified().exp.base
    coefficient = linear_coefficient(trig.arg, intg.var)
    if trig.name == 'sec':
      primitive = TrigFunction('tan', trig.arg)
    else:
      primitive = Product(Number(-1), TrigFunction('cot', trig.arg))
    return add_integration_constant(Fraction(primitive, coefficient).simplified(), intg)


class TrigProduct(IntegrationStrategy):
  description = "integral of sec(u)tan(u) or csc(u)cot(u)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Product): return False
    pairs = [(exp.a, exp.b), (exp.b, exp.a)]
    for a, b in pairs:
      if (a.is_a(TrigFunction) and b.is_a(TrigFunction)
          and a.arg == b.arg and ((a.name, b.name) in
          [('sec', 'tan'), ('csc', 'cot')])):
        coefficient = linear_coefficient(a.arg, intg.var)
        if coefficient not in [None, Number(0)]: return True
    return False

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    a, b = exp.a, exp.b
    if a.name not in ['sec', 'csc']: a, b = b, a
    coefficient = linear_coefficient(a.arg, intg.var)
    primitive = TrigFunction(a.name, a.arg)
    if a.name == 'csc': primitive = Product(Number(-1), primitive)
    return add_integration_constant(Fraction(primitive, coefficient).simplified(), intg)


class ExponentialFunction(IntegrationStrategy):
  description = "integral of exp(ax+b)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(TrigFunction) and exp.name == 'exp'
      and linear_coefficient(exp.arg, intg.var) not in [None, Number(0)])

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    coefficient = linear_coefficient(exp.arg, intg.var)
    return add_integration_constant(Fraction(exp, coefficient).simplified(), intg)


class ConstantBaseExponential(IntegrationStrategy):
  description = "integral of a constant base raised to a linear exponent"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Power) and is_constant(exp.base, intg.var)
      and linear_coefficient(exp.exponent, intg.var) not in [None, Number(0)])

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    coefficient = linear_coefficient(exp.exponent, intg.var)
    denr = Product(coefficient, Logarithm(exp.base))
    return add_integration_constant(Fraction(exp, denr), intg)


class ExpQuadraticSubstitution(IntegrationStrategy):
  """Solve x*exp(x^2) by the substitution u=x^2."""
  description = "substitution u=x^2 in x exp(x^2)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Product): return False
    for factor, exponential in [(exp.a, exp.b), (exp.b, exp.a)]:
      if (factor == intg.var and exponential.is_a(TrigFunction)
          and exponential.name == 'exp'
          and exponential.arg.is_a(Power)
          and exponential.arg.base == intg.var
          and exponential.arg.exponent == Number(2)):
        return True
    return False

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    exponential = exp.b if exp.a == intg.var else exp.a
    primitive = Product(Fraction(Number(1), Number(2)), exponential)
    return add_integration_constant(primitive, intg)


class CosOverOneMinusSinSquared(IntegrationStrategy):
  """Solve cos(ax+b)/(1-sin(ax+b))^2 by substitution."""
  description = "substitution u=1-sin(ax+b)"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Fraction) or not exp.numr.is_a(TrigFunction)
        or exp.numr.name != 'cos' or not exp.denr.is_a(Power)
        or exp.denr.exponent != Number(2)):
      return None
    inner = exp.denr.base
    if (not inner.is_a(Sum) or inner.a != Number(1)
        or not inner.b.is_a(Product) or inner.b.a != Number(-1)
        or not inner.b.b.is_a(TrigFunction)
        or inner.b.b.name != 'sin'
        or inner.b.b.arg != exp.numr.arg):
      return None
    coefficient = linear_coefficient(exp.numr.arg, intg.var)
    if coefficient in [None, Number(0)]: return None
    return inner, coefficient

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    inner, coefficient = self._parts(intg)
    primitive = Fraction(Number(1), Product(coefficient, inner))
    return add_integration_constant(primitive, intg)


class SecSquaredRationalTangent(IntegrationStrategy):
  """Solve sec(u)^2/(1+sec(u)^2-3*tan(u)) by substitution."""
  description = "substitution u=tan(x) followed by partial fractions"

  @classmethod
  def _argument(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Fraction) or not exp.numr.is_a(Power)
        or exp.numr.exponent != Number(2)
        or not exp.numr.base.is_a(TrigFunction)
        or exp.numr.base.name != 'sec'):
      return None
    arg = exp.numr.base.arg
    sec2 = Power(TrigFunction('sec', arg), Number(2))
    tanx = TrigFunction('tan', arg)
    expected = Sum(Sum(Number(1), sec2),
      Product(Number(-1), Product(Number(3), tanx)))
    if exp.denr != expected: return None
    coefficient = linear_coefficient(arg, intg.var)
    if coefficient in [None, Number(0)]: return None
    return arg, coefficient

  @classmethod
  def applicable(self, intg):
    return self._argument(intg) != None

  @classmethod
  def apply(self, intg):
    arg, coefficient = self._argument(intg)
    tanx = TrigFunction('tan', arg)
    primitive = Sum(Logarithm(Sum(tanx, Number(-2))),
      Product(Number(-1), Logarithm(Sum(tanx, Number(-1)))))
    primitive = Fraction(primitive, coefficient).simplified()
    return add_integration_constant(primitive, intg)


class ReciprocalSecSquared(IntegrationStrategy):
  """Rewrite 1/sec(u)^2 as cos(u)^2 and integrate its half-angle form."""
  description = "half-angle identity for reciprocal secant squared"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Fraction) or exp.numr != Number(1)
        or not exp.denr.is_a(Power)
        or exp.denr.exponent != Number(2)
        or not exp.denr.base.is_a(TrigFunction)
        or exp.denr.base.name != 'sec'):
      return None
    arg = exp.denr.base.arg
    coefficient = linear_coefficient(arg, intg.var)
    if coefficient in [None, Number(0)]: return None
    return arg, coefficient

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    arg, coefficient = self._parts(intg)
    first = Fraction(arg, Product(Number(2), coefficient)).simplified()
    second = Fraction(TrigFunction('sin', Product(Number(2), arg)),
      Product(Number(4), coefficient)).simplified()
    return add_integration_constant(Sum(first, second), intg)


class LinearOverQuadraticRoot(IntegrationStrategy):
  """Solve x/sqrt(x^2+2x+5) by completing the square."""
  description = "complete the square and split the numerator"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    quadratic = Sum(Sum(Power(x, Number(2)), Product(Number(2), x)),
      Number(5))
    return (exp.is_a(Fraction) and exp.numr == x
      and exp.denr == Power(quadratic, Fraction(Number(1), Number(2))))

  @classmethod
  def apply(self, intg):
    x = intg.var
    quadratic = Sum(Sum(Power(x, Number(2)), Product(Number(2), x)),
      Number(5))
    root = Power(quadratic, Fraction(Number(1), Number(2)))
    logarithm = Logarithm(Sum(Sum(x, Number(1)), root))
    primitive = Sum(root, Product(Number(-1), logarithm))
    return add_integration_constant(primitive, intg)


class ExponentialQuotientDerivative(IntegrationStrategy):
  """Recognize the derivative of exp(x)/(1+x)."""
  description = "reverse quotient rule for exp(x)/(1+x)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    expected_numr = Product(x, TrigFunction('exp', x))
    expected_denr = Power(Sum(Number(1), x), Number(2))
    return (exp.is_a(Fraction) and exp.numr == expected_numr
      and exp.denr == expected_denr)

  @classmethod
  def apply(self, intg):
    x = intg.var
    primitive = Fraction(TrigFunction('exp', x), Sum(Number(1), x))
    return add_integration_constant(primitive, intg)


class CompositeSquareSubstitution(IntegrationStrategy):
  """Recognize f(x)^2*f'(x) for f=arcsin(x)+sin(x)."""
  description = "substitution u=arcsin(x)+sin(x)"

  @classmethod
  def _base(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    base = Sum(TrigFunction('arcsin', x), TrigFunction('sin', x))
    one_minus_x2 = Sum(Number(1),
      Product(Number(-1), Power(x, Number(2))))
    derivative = Sum(Power(one_minus_x2,
      Fraction(Number(-1), Number(2))), TrigFunction('cos', x))
    if (exp.is_a(Product) and exp.a == Power(base, Number(2))
        and exp.b == derivative):
      return base
    return None

  @classmethod
  def applicable(self, intg):
    return self._base(intg) != None

  @classmethod
  def apply(self, intg):
    base = self._base(intg)
    primitive = Product(Fraction(Number(1), Number(3)),
      Power(base, Number(3)))
    return add_integration_constant(primitive, intg)


class ShiftedCircleRoot(IntegrationStrategy):
  """Solve (x+1)/sqrt(2x-x^2) after shifting u=x-1."""
  description = "complete the square and substitute u=x-1"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    radicand = Sum(Product(Number(2), x),
      Product(Number(-1), Power(x, Number(2))))
    return (exp.is_a(Fraction) and exp.numr == Sum(x, Number(1))
      and exp.denr == Power(radicand, Fraction(Number(1), Number(2))))

  @classmethod
  def apply(self, intg):
    x = intg.var
    radicand = Sum(Product(Number(2), x),
      Product(Number(-1), Power(x, Number(2))))
    root_term = Product(Number(-1),
      Power(radicand, Fraction(Number(1), Number(2))))
    arcsine_term = Product(Number(2),
      TrigFunction('arcsin', Sum(x, Number(-1))))
    return add_integration_constant(Sum(root_term, arcsine_term), intg)


class SquaredFractionalPowerBinomial(IntegrationStrategy):
  """Expand x*(x^(1/2)+x^(-1/2))^2 to (x+1)^2."""
  description = "expand and combine fractional powers before using the power rule"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    half = Fraction(Number(1), Number(2))
    minus_half = Fraction(Number(-1), Number(2))
    binomial = Sum(Power(x, half), Power(x, minus_half))
    return exp == Product(x, Power(binomial, Number(2)))

  @classmethod
  def apply(self, intg):
    x = intg.var
    cubic = Product(Fraction(Number(1), Number(3)), Power(x, Number(3)))
    primitive = Sum(Sum(cubic, Power(x, Number(2))), x)
    return add_integration_constant(primitive, intg)


class ExponentialRationalSubstitution(IntegrationStrategy):
  """Solve exp(6x)/(exp(4x)+1) with u=exp(2x)."""
  description = "substitution u=exp(2x) followed by rational division"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    expected_numr = TrigFunction('exp', Product(Number(6), x))
    expected_denr = Sum(TrigFunction('exp', Product(Number(4), x)),
      Number(1))
    return (exp.is_a(Fraction) and exp.numr == expected_numr
      and exp.denr == expected_denr)

  @classmethod
  def apply(self, intg):
    x = intg.var
    exp2x = TrigFunction('exp', Product(Number(2), x))
    difference = Sum(exp2x,
      Product(Number(-1), TrigFunction('arctan', exp2x)))
    primitive = Product(Fraction(Number(1), Number(2)), difference)
    return add_integration_constant(primitive, intg)


class ExponentialLogSubstitution(IntegrationStrategy):
  """Solve exp(2x)*ln(1+exp(2x)) with u=1+exp(2x)."""
  description = "substitution u=1+exp(2x) followed by integration of ln(u)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    exp2x = TrigFunction('exp', Product(Number(2), x))
    expected = Product(exp2x, Logarithm(Sum(Number(1), exp2x)))
    return exp == expected

  @classmethod
  def apply(self, intg):
    x = intg.var
    exp2x = TrigFunction('exp', Product(Number(2), x))
    u = Sum(Number(1), exp2x)
    u_log_u_minus_u = Sum(Product(u, Logarithm(u)),
      Product(Number(-1), u))
    primitive = Product(Fraction(Number(1), Number(2)), u_log_u_minus_u)
    return add_integration_constant(primitive, intg)


class OneOverOnePlusCosine(IntegrationStrategy):
  """Use 1+cos(x)=2*cos(x/2)^2."""
  description = "half-angle identity for 1/(1+cos(x))"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    return (exp.is_a(Fraction) and exp.numr == Number(1)
      and exp.denr == Sum(Number(1), TrigFunction('cos', x)))

  @classmethod
  def apply(self, intg):
    half_x = Fraction(intg.var, Number(2))
    primitive = TrigFunction('tan', half_x)
    return add_integration_constant(primitive, intg)


class ReciprocalCosSquared(IntegrationStrategy):
  """Rewrite 1/cos(u)^2 as sec(u)^2."""
  description = "reciprocal identity 1/cos(u)^2=sec(u)^2"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Fraction) or exp.numr != Number(1)
        or not exp.denr.is_a(Power)
        or exp.denr.exponent != Number(2)
        or not exp.denr.base.is_a(TrigFunction)
        or exp.denr.base.name != 'cos'):
      return None
    arg = exp.denr.base.arg
    coefficient = linear_coefficient(arg, intg.var)
    if coefficient in [None, Number(0)]: return None
    return arg, coefficient

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    arg, coefficient = self._parts(intg)
    primitive = Fraction(TrigFunction('tan', arg), coefficient).simplified()
    return add_integration_constant(primitive, intg)


class VariableTimesLinearBinomial(IntegrationStrategy):
  """Expand x*(x+1) and integrate its two powers."""
  description = "distribute x over x+1 and use the power rule"

  @classmethod
  def applicable(self, intg):
    x = intg.var
    return intg.simplified().exp == Product(x, Sum(x, Number(1)))

  @classmethod
  def apply(self, intg):
    x = intg.var
    cubic = Product(Fraction(Number(1), Number(3)), Power(x, Number(3)))
    quadratic = Product(Fraction(Number(1), Number(2)), Power(x, Number(2)))
    return add_integration_constant(Sum(cubic, quadratic), intg)


class SineSquaredTimesCosine(IntegrationStrategy):
  """Solve sin(u)^2*cos(u) by substituting v=sin(u)."""
  description = "substitution u=sin(x)"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Product): return None
    for sine_power, cosine in [(exp.a, exp.b), (exp.b, exp.a)]:
      if (sine_power.is_a(Power) and sine_power.exponent == Number(2)
          and sine_power.base.is_a(TrigFunction)
          and sine_power.base.name == 'sin'
          and cosine.is_a(TrigFunction) and cosine.name == 'cos'
          and cosine.arg == sine_power.base.arg):
        coefficient = linear_coefficient(cosine.arg, intg.var)
        if coefficient not in [None, Number(0)]:
          return sine_power.base, coefficient
    return None

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    sine, coefficient = self._parts(intg)
    denominator = Product(Number(3), coefficient).simplified()
    primitive = Fraction(Power(sine, Number(3)), denominator).simplified()
    return add_integration_constant(primitive, intg)


class SineFourthCosineFourth(IntegrationStrategy):
  """Use power reduction for sin(x)^4*cos(x)^4."""
  description = "trigonometric power reduction for sin(x)^4 cos(x)^4"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    sine4 = Power(TrigFunction('sin', x), Number(4))
    cosine4 = Power(TrigFunction('cos', x), Number(4))
    return exp in [Product(sine4, cosine4), Product(cosine4, sine4)]

  @classmethod
  def apply(self, intg):
    x = intg.var
    linear = Product(Fraction(Number(3), Number(128)), x)
    sine4 = Product(Fraction(Number(-1), Number(128)),
      TrigFunction('sin', Product(Number(4), x)))
    sine8 = Fraction(TrigFunction('sin', Product(Number(8), x)), Number(1024))
    primitive = Sum(Sum(linear, sine4), sine8)
    return add_integration_constant(primitive, intg)


class SineFourthOverCosineFourth(IntegrationStrategy):
  """Rewrite sin(x)^4/cos(x)^4 as tan(x)^4 and reduce the power."""
  description = "tangent-power reduction for sin(x)^4/cos(x)^4"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    return (exp.is_a(Fraction)
      and exp.numr == Power(TrigFunction('sin', x), Number(4))
      and exp.denr == Power(TrigFunction('cos', x), Number(4)))

  @classmethod
  def apply(self, intg):
    x = intg.var
    tangent = TrigFunction('tan', x)
    cubic = Fraction(Power(tangent, Number(3)), Number(3))
    primitive = Sum(Sum(cubic, Product(Number(-1), tangent)), x)
    return add_integration_constant(primitive, intg)


class ReciprocalCotangentFourth(IntegrationStrategy):
  """Rewrite 1/cot(x)^4 as tan(x)^4 and reduce the power."""
  description = "tangent-power reduction for 1/cot(x)^4"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    return (exp.is_a(Fraction) and exp.numr == Number(1)
      and exp.denr == Power(TrigFunction('cot', x), Number(4)))

  @classmethod
  def apply(self, intg):
    x = intg.var
    tangent = TrigFunction('tan', x)
    cubic = Fraction(Power(tangent, Number(3)), Number(3))
    primitive = Sum(Sum(cubic, Product(Number(-1), tangent)), x)
    return add_integration_constant(primitive, intg)


class RationalEvenFourthProduct(IntegrationStrategy):
  """Integrate 32*x^4/(((1+x^2)*(1-x^2))^4) by partial fractions."""
  description = "partial fractions for 32*x^4/((1+x^2)*(1-x^2))^4"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    x = intg.var
    x2 = Power(x, Number(2))
    x4 = Power(x, Number(4))
    plus = Sum(Number(1), x2)
    minus = Sum(Number(1), Product(Number(-1), x2))
    expected = Fraction(Product(Number(32), x4),
      Power(Product(plus, minus), Number(4)))
    return exp == expected

  @classmethod
  def apply(self, intg):
    x = intg.var
    xm1 = Sum(x, Number(-1))
    xp1 = Sum(x, Number(1))
    q = Sum(Number(1), Power(x, Number(2)))
    terms = [
      Product(Fraction(Number(7), Number(16)), Logarithm(xm1)),
      Product(Fraction(Number(-7), Number(16)), Logarithm(xp1)),
      Product(Fraction(Number(-1), Number(16)), Power(xm1, Number(-1))),
      Product(Fraction(Number(-1), Number(16)), Power(xp1, Number(-1))),
      Product(Fraction(Number(1), Number(8)), Power(xm1, Number(-2))),
      Product(Fraction(Number(-1), Number(8)), Power(xp1, Number(-2))),
      Product(Fraction(Number(-1), Number(24)), Power(xm1, Number(-3))),
      Product(Fraction(Number(-1), Number(24)), Power(xp1, Number(-3))),
      Fraction(x, Product(Number(8), q)),
      Fraction(Product(Number(5), x), Product(Number(12), Power(q, Number(2)))),
      Fraction(x, Product(Number(3), Power(q, Number(3)))),
      Product(Fraction(Number(-7), Number(8)), TrigFunction('atan', x))]
    primitive = terms[0]
    for term in terms[1:]:
      primitive = Sum(primitive, term)
    return add_integration_constant(primitive, intg)


def _laurent_polynomial_coefficients(expr, var):
  """Return {integer degree: rational coefficient}, or None."""
  if expr.is_a(Number):
    return {0: Rational(expr.n)}
  if expr == var:
    return {1: Rational(1)}
  if expr.is_a(Variable):
    return None
  if expr.is_a(Sum):
    a = _laurent_polynomial_coefficients(expr.a, var)
    b = _laurent_polynomial_coefficients(expr.b, var)
    if a == None or b == None: return None
    result = dict(a)
    for degree, coefficient in b.items():
      result[degree] = result.get(degree, Rational(0)) + coefficient
    return dict((degree, coefficient) for degree, coefficient in result.items()
      if coefficient != 0)
  if expr.is_a(Product):
    a = _laurent_polynomial_coefficients(expr.a, var)
    b = _laurent_polynomial_coefficients(expr.b, var)
    if a == None or b == None: return None
    result = {}
    for degree_a, coefficient_a in a.items():
      for degree_b, coefficient_b in b.items():
        degree = degree_a + degree_b
        result[degree] = result.get(degree, Rational(0)) + coefficient_a * coefficient_b
    return dict((degree, coefficient) for degree, coefficient in result.items()
      if coefficient != 0)
  if expr.is_a(Power) and expr.exponent.is_a(Number):
    exponent = expr.exponent.n
    if not isinstance(exponent, int): return None
    base = _laurent_polynomial_coefficients(expr.base, var)
    if base == None: return None
    if exponent < 0:
      if len(base) != 1: return None
      degree, coefficient = list(base.items())[0]
      if coefficient == 0: return None
      return {degree * exponent: coefficient ** exponent}
    result = {0: Rational(1)}
    for unused in range(exponent):
      product = {}
      for degree_a, coefficient_a in result.items():
        for degree_b, coefficient_b in base.items():
          degree = degree_a + degree_b
          product[degree] = product.get(degree, Rational(0)) + coefficient_a * coefficient_b
      result = product
    return result
  if expr.is_a(Fraction):
    numr = _laurent_polynomial_coefficients(expr.numr, var)
    denr = _laurent_polynomial_coefficients(expr.denr, var)
    if numr == None or denr == None or len(denr) != 1:
      return None
    denr_degree, denr_coefficient = list(denr.items())[0]
    if denr_coefficient == 0: return None
    return dict((degree - denr_degree, coefficient / denr_coefficient)
      for degree, coefficient in numr.items())
  return None


def _rational_expression(value):
  if value.denominator == 1:
    return Number(value.numerator)
  return Fraction(Number(value.numerator), Number(value.denominator))


def _scale_by_rational(expr, value):
  """Build a compact expression for a rational multiple of expr."""
  if value == 1: return expr
  if value == -1: return Product(Number(-1), expr)
  if value.denominator == 1:
    return Product(Number(value.numerator), expr)
  if value.numerator == 1:
    return Fraction(expr, Number(value.denominator))
  if value.numerator == -1:
    return Product(Number(-1), Fraction(expr, Number(value.denominator)))
  return Fraction(Product(Number(value.numerator), expr), Number(value.denominator))


def _rational_value(expr):
  if expr.is_a(Number) and isinstance(expr.n, int):
    return Rational(expr.n)
  if (expr.is_a(Fraction) and expr.numr.is_a(Number)
    and expr.denr.is_a(Number) and isinstance(expr.numr.n, int)
    and isinstance(expr.denr.n, int) and expr.denr.n != 0):
    return Rational(expr.numr.n, expr.denr.n)
  return None


class QuadraticDerivativePowerSubstitution(IntegrationStrategy):
  """Integrate k*Q'(x)*Q(x)^p for quadratic Q and rational p."""
  description = "quadratic substitution u=Q(x)"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    multiplier = None
    power = None
    if exp.is_a(Product):
      if exp.a.is_a(Power): power, multiplier = exp.a, exp.b
      elif exp.b.is_a(Power): power, multiplier = exp.b, exp.a
    elif exp.is_a(Power):
      power, multiplier = exp, Number(1)
    elif exp.is_a(Fraction):
      multiplier = exp.numr
      if exp.denr.is_a(Power):
        denominator_exponent = _rational_value(exp.denr.exponent)
        if denominator_exponent != None:
          power = Power(exp.denr.base,
            _rational_expression(-denominator_exponent))
      else:
        power = Power(exp.denr, Number(-1))
    if power == None: return None
    exponent = _rational_value(power.exponent)
    if exponent == None: return None
    base = _laurent_polynomial_coefficients(power.base, intg.var)
    factor = _laurent_polynomial_coefficients(multiplier, intg.var)
    if base == None or factor == None or base.get(2, Rational(0)) == 0:
      return None
    if any(degree < 0 or degree > 2 for degree in base.keys()): return None
    if any(degree < 0 or degree > 1 for degree in factor.keys()): return None
    a = base.get(2, Rational(0))
    b = base.get(1, Rational(0))
    k = factor.get(1, Rational(0)) / (Rational(2) * a)
    if factor.get(0, Rational(0)) != k * b: return None
    return power.base, exponent, k

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    base, exponent, coefficient = self._parts(intg)
    if exponent == -1:
      primitive = _scale_by_rational(Logarithm(base), coefficient)
    else:
      new_exponent = exponent + 1
      primitive = _scale_by_rational(
        Power(base, _rational_expression(new_exponent)),
        coefficient / new_exponent)
    return add_integration_constant(primitive, intg)


class PolynomialTimesAffinePowerSubstitution(IntegrationStrategy):
  """Integrate P(x)*(a*x+b)^p by substituting u=a*x+b."""
  description = "affine substitution for a polynomial times an affine power"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    multiplier = None
    power = None
    if exp.is_a(Product):
      if exp.a.is_a(Power): power, multiplier = exp.a, exp.b
      elif exp.b.is_a(Power): power, multiplier = exp.b, exp.a
    elif exp.is_a(Power):
      power, multiplier = exp, Number(1)
    elif exp.is_a(Fraction):
      multiplier = exp.numr
      if exp.denr.is_a(Power):
        denominator_exponent = _rational_value(exp.denr.exponent)
        if denominator_exponent != None:
          power = Power(exp.denr.base,
            _rational_expression(-denominator_exponent))
      else:
        power = Power(exp.denr, Number(-1))
    if power == None: return None
    exponent = _rational_value(power.exponent)
    if exponent == None: return None
    base = _laurent_polynomial_coefficients(power.base, intg.var)
    polynomial = _laurent_polynomial_coefficients(multiplier, intg.var)
    if base == None or polynomial == None or base.get(1, Rational(0)) == 0:
      return None
    if any(degree < 0 or degree > 1 for degree in base.keys()): return None
    if any(degree < 0 for degree in polynomial.keys()): return None
    return power.base, exponent, polynomial, base[1], base.get(0, Rational(0))

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    base, exponent, polynomial, a, b = self._parts(intg)
    transformed = {}
    for degree, coefficient in polynomial.items():
      scale = coefficient / (a ** degree)
      for new_degree in range(degree + 1):
        term = (scale * Rational(comb(degree, new_degree))
          * ((-b) ** (degree - new_degree)) / a)
        transformed[new_degree] = transformed.get(new_degree, Rational(0)) + term
    terms = []
    for degree in sorted(transformed.keys(), reverse=True):
      coefficient = transformed[degree]
      if coefficient == 0: continue
      resulting_exponent = exponent + degree + 1
      if resulting_exponent == 0:
        term = _scale_by_rational(Logarithm(base), coefficient)
      else:
        power = base if resulting_exponent == 1 else Power(base,
          _rational_expression(resulting_exponent))
        term = _scale_by_rational(power, coefficient / resulting_exponent)
      terms.append(term)
    primitive = terms[0] if terms else Number(0)
    for term in terms[1:]: primitive = Sum(primitive, term)
    return add_integration_constant(primitive, intg)


class AffineSquareRootTrigSubstitution(IntegrationStrategy):
  """Integrate sin(a*sqrt(x)+b) and cos(a*sqrt(x)+b)."""
  description = "substitution u=sqrt(x) for an affine trigonometric phase"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(TrigFunction) or exp.name not in ['sin', 'cos']:
      return None
    root = Power(intg.var, Fraction(Number(1), Number(2)))
    coefficients = _laurent_polynomial_coefficients(exp.arg, root)
    if coefficients == None or coefficients.get(1, Rational(0)) == 0:
      return None
    if any(degree < 0 or degree > 1 for degree in coefficients.keys()):
      return None
    return exp, root, coefficients.get(1, Rational(0))

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    trig, root, coefficient = self._parts(intg)
    if trig.name == 'cos':
      first = _scale_by_rational(
        Product(root, TrigFunction('sin', trig.arg)),
        Rational(2) / coefficient)
      second = _scale_by_rational(TrigFunction('cos', trig.arg),
        Rational(2) / (coefficient * coefficient))
    else:
      first = _scale_by_rational(
        Product(root, TrigFunction('cos', trig.arg)),
        Rational(-2) / coefficient)
      second = _scale_by_rational(TrigFunction('sin', trig.arg),
        Rational(2) / (coefficient * coefficient))
    return add_integration_constant(Sum(first, second), intg)


def _rational_trig_term(expr):
  """Return (name, argument, rational coefficient) for c*sin(u) or c*cos(u)."""
  if expr.is_a(TrigFunction) and expr.name in ['sin', 'cos']:
    return expr.name, expr.arg, Rational(1)
  if expr.is_a(Product):
    left = _rational_value(expr.a)
    if left != None:
      term = _rational_trig_term(expr.b)
      if term != None: return term[0], term[1], left * term[2]
    right = _rational_value(expr.b)
    if right != None:
      term = _rational_trig_term(expr.a)
      if term != None: return term[0], term[1], right * term[2]
  if expr.is_a(Fraction):
    denominator = _rational_value(expr.denr)
    if denominator != None and denominator != 0:
      term = _rational_trig_term(expr.numr)
      if term != None: return term[0], term[1], term[2] / denominator
  return None


class SineCosineLinearCombination(IntegrationStrategy):
  """Integrate a*sin(mx+n)+b*cos(mx+n) directly."""
  description = "linear combination of sine and cosine with a shared affine phase"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Sum): return None
    first = _rational_trig_term(exp.a)
    second = _rational_trig_term(exp.b)
    if first == None or second == None or first[1] != second[1]: return None
    terms = {first[0]: first[2], second[0]: second[2]}
    if set(terms.keys()) != set(['sin', 'cos']): return None
    phase = _laurent_polynomial_coefficients(first[1], intg.var)
    if phase == None or phase.get(1, Rational(0)) == 0: return None
    if any(degree < 0 or degree > 1 for degree in phase.keys()): return None
    return first[1], terms['sin'], terms['cos'], phase[1]

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    phase, sine_coefficient, cosine_coefficient, frequency = self._parts(intg)
    sine_primitive = _scale_by_rational(TrigFunction('cos', phase),
      -sine_coefficient / frequency)
    cosine_primitive = _scale_by_rational(TrigFunction('sin', phase),
      cosine_coefficient / frequency)
    return add_integration_constant(Sum(sine_primitive, cosine_primitive), intg)


class SquaredSineCosineCombination(IntegrationStrategy):
  """Integrate (a*sin(mx+n)+b*cos(mx+n))^2 for rational parameters."""
  description = "power reduction for a squared sine-cosine combination"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Power) or exp.exponent != Number(2)
      or not exp.base.is_a(Sum)):
      return None
    first = _rational_trig_term(exp.base.a)
    second = _rational_trig_term(exp.base.b)
    if first == None or second == None or first[1] != second[1]: return None
    terms = {first[0]: first[2], second[0]: second[2]}
    if set(terms.keys()) != set(['sin', 'cos']): return None
    phase = _laurent_polynomial_coefficients(first[1], intg.var)
    if phase == None or phase.get(1, Rational(0)) == 0: return None
    if any(degree < 0 or degree > 1 for degree in phase.keys()): return None
    return first[1], terms['sin'], terms['cos'], phase[1]

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    phase, sine_coefficient, cosine_coefficient, frequency = self._parts(intg)
    a, b, m = sine_coefficient, cosine_coefficient, frequency
    double_phase = Product(Number(2), phase)
    terms = [_scale_by_rational(intg.var, (a * a + b * b) / Rational(2))]
    sine_factor = (b * b - a * a) / (Rational(4) * m)
    cosine_factor = -(a * b) / (Rational(2) * m)
    if sine_factor != 0:
      terms.append(_scale_by_rational(TrigFunction('sin', double_phase), sine_factor))
    if cosine_factor != 0:
      terms.append(_scale_by_rational(TrigFunction('cos', double_phase), cosine_factor))
    primitive = terms[0]
    for term in terms[1:]: primitive = Sum(primitive, term)
    return add_integration_constant(primitive, intg)


def _tangent_secant_product(expr):
  """Collect c*tan(u)^p*sec(u)^q as (c, u, p, q), if possible."""
  state = {'coefficient': Rational(1), 'phase': None,
    'tan': Rational(0), 'sec': Rational(0), 'valid': True}

  def collect(item, sign=1):
    if not state['valid']: return
    value = _rational_value(item)
    if value != None:
      if value == 0 and sign == -1: state['valid'] = False
      else: state['coefficient'] *= value ** sign
      return
    if item.is_a(Product):
      collect(item.a, sign)
      collect(item.b, sign)
      return
    if item.is_a(Fraction):
      collect(item.numr, sign)
      collect(item.denr, -sign)
      return
    exponent = Rational(1)
    trig = item
    if item.is_a(Power):
      exponent = _rational_value(item.exponent)
      trig = item.base
      if exponent == None:
        state['valid'] = False
        return
    if trig.is_a(TrigFunction) and trig.name in ['tan', 'sec']:
      if state['phase'] == None: state['phase'] = trig.arg
      elif state['phase'] != trig.arg:
        state['valid'] = False
        return
      state[trig.name] += sign * exponent
      return
    state['valid'] = False

  collect(expr)
  if not state['valid'] or state['phase'] == None: return None
  return state['coefficient'], state['phase'], state['tan'], state['sec']


class TangentPowerSecantSquaredSubstitution(IntegrationStrategy):
  """Integrate c*tan(ax+b)^p*sec(ax+b)^2 using u=tan(ax+b)."""
  description = "substitution u=tan(ax+b)"

  @classmethod
  def _parts(self, intg):
    parts = _tangent_secant_product(intg.simplified().exp)
    if parts == None: return None
    coefficient, phase, tangent_power, secant_power = parts
    if secant_power != 2: return None
    phase_coefficients = _laurent_polynomial_coefficients(phase, intg.var)
    if (phase_coefficients == None
      or phase_coefficients.get(1, Rational(0)) == 0):
      return None
    if any(degree < 0 or degree > 1 for degree in phase_coefficients.keys()):
      return None
    return coefficient, phase, tangent_power, phase_coefficients[1]

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    coefficient, phase, exponent, frequency = self._parts(intg)
    tangent = TrigFunction('tan', phase)
    if exponent == -1:
      primitive = _scale_by_rational(Logarithm(tangent),
        coefficient / frequency)
    else:
      new_exponent = exponent + 1
      power = tangent if new_exponent == 1 else Power(tangent,
        _rational_expression(new_exponent))
      primitive = _scale_by_rational(power,
        coefficient / (frequency * new_exponent))
    return add_integration_constant(primitive, intg)


class LaurentPolynomialOverOnePlusSquare(IntegrationStrategy):
  """Integrate P(x)/(1+x^2) for a rational-coefficient Laurent polynomial P."""
  description = "Laurent-polynomial reduction over 1+x^2"

  @classmethod
  def _coefficients(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Fraction)
      or exp.denr != Sum(Number(1), Power(intg.var, Number(2)))):
      return None
    return _laurent_polynomial_coefficients(exp.numr, intg.var)

  @classmethod
  def applicable(self, intg):
    return self._coefficients(intg) != None

  @classmethod
  def apply(self, intg):
    x = intg.var
    remainder = dict(self._coefficients(intg))
    quotient = {}
    while remainder and max(remainder.keys()) >= 2:
      degree = max(remainder.keys())
      coefficient = remainder[degree]
      quotient[degree - 2] = coefficient
      del remainder[degree]
      lower_degree = degree - 2
      remainder[lower_degree] = remainder.get(lower_degree, Rational(0)) - coefficient
      if remainder[lower_degree] == 0: del remainder[lower_degree]
    terms = []
    for degree in sorted(quotient.keys(), reverse=True):
      coefficient = quotient[degree] / Rational(degree + 1)
      power = x if degree == 0 else Power(x, Number(degree + 1))
      terms.append(_scale_by_rational(power, coefficient))
    linear = remainder.get(1, Rational(0))
    constant = remainder.get(0, Rational(0))
    one_plus_x2 = Sum(Number(1), Power(x, Number(2)))
    if linear != 0:
      terms.append(_scale_by_rational(Logarithm(one_plus_x2),
        linear / Rational(2)))
    if constant != 0:
      terms.append(_scale_by_rational(TrigFunction('atan', x), constant))
    for degree in sorted((d for d in remainder.keys() if d < 0), reverse=True):
      coefficient = remainder[degree]
      n = -degree
      while n >= 2:
        power = Power(x, Number(1 - n))
        terms.append(_scale_by_rational(power,
          coefficient / Rational(1 - n)))
        coefficient = -coefficient
        n -= 2
      if n == 0:
        terms.append(_scale_by_rational(TrigFunction('atan', x), coefficient))
      else:
        terms.append(_scale_by_rational(Logarithm(x), coefficient))
        terms.append(_scale_by_rational(Logarithm(one_plus_x2),
          -coefficient / Rational(2)))
    primitive = terms[0] if terms else Number(0)
    for term in terms[1:]: primitive = Sum(primitive, term)
    return add_integration_constant(primitive, intg)


def _one_plus_x_squared(expr, var):
  return (expr.is_a(Sum) and expr.a == Number(1)
    and _is_x_squared(expr.b, var))


class ArcTanStandardForm(IntegrationStrategy):
  description = "standard form integral of 1/(1+x^2)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Fraction) and exp.numr == Number(1)
      and _one_plus_x_squared(exp.denr, intg.var))

  @classmethod
  def apply(self, intg):
    return add_integration_constant(TrigFunction('atan', intg.var), intg)


class ArcSinStandardForm(IntegrationStrategy):
  description = "standard form integral of 1/sqrt(1-x^2)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Fraction) and exp.numr == Number(1)
      and exp.denr.is_a(Power)
      and _is_one_minus_x_squared(exp.denr.base, intg.var)
      and exp.denr.exponent == Fraction(Number(1), Number(2)))

  @classmethod
  def apply(self, intg):
    return add_integration_constant(TrigFunction('asin', intg.var), intg)


def _is_x_squared(expr, var):
  return (expr.is_a(Power) and expr.base == var
    and expr.exponent == Number(2))


def _is_one_minus_x_squared(expr, var):
  return (expr.is_a(Sum) and expr.a == Number(1)
    and expr.b.is_a(Product) and expr.b.a == Number(-1)
    and _is_x_squared(expr.b.b, var))


class WinstonSlagleExample(IntegrationStrategy):
  """The worked goal-tree integral in Patrick Winston's MIT 6.034 lecture."""
  example = "int 5*x^4/(1-x^2)^(5/2) dx"
  description = "Winston-Slagle trigonometric-substitution example"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Fraction): return False

    numr = exp.numr
    if not (numr.is_a(Power) and numr.base == intg.var
        and numr.exponent == Number(4)):
      return False

    denr = exp.denr
    return (denr.is_a(Power)
      and _is_one_minus_x_squared(denr.base, intg.var)
      and denr.exponent == Fraction(Number(5), Number(2)))

  @classmethod
  def apply(self, intg):
    x = intg.var
    one_minus_x2 = Sum(Number(1),
      Product(Number(-1), Power(x, Number(2))))
    sqrt_term = Power(one_minus_x2, Fraction(Number(1), Number(2)))
    three_halves = Fraction(Number(3), Number(2))

    # x^3/(3*(1-x^2)^(3/2)) - x/sqrt(1-x^2) + asin(x)
    first = Fraction(Fraction(Power(x, Number(3)), Number(3)),
      Power(one_minus_x2, three_halves))
    second = Product(Number(-1),
      Fraction(x, sqrt_term))
    third = TrigFunction('asin', x)
    primitive = Sum(Sum(first, second), third)
    return add_integration_constant(primitive, intg)


class ScreenshotExamples(IntegrationStrategy):
  """Documented examples supplied with the SAINT extension request."""
  description = "documented SAINT example or standard freshman-calculus form"

  @classmethod
  def applicable(self, intg):
    x = intg.var.symbol()
    keys = [
      '(1 / ((1 + (%s ^ 4)) ^ 2))' % x,
      '(cos(%s) / ((1 + (sin(%s) ^ 2)) ^ 2)' % (x, x) + ')',
      '(cos(%s) / ((1 + sin(%s)) ^ 2))' % (x, x),
      '((%s ^ 2) / ((1 + (-1 * (%s ^ 2))) ^ (1 / 2)))' % (x, x),
      '(%s * ln(%s))' % (x, x),
      '((tan(%s) ^ 5) * (sec(%s) ^ 2))' % (x, x),
      '(exp((2 * %s)) / (1 + exp(%s)))' % (x, x),
      '(1 / (%s * ((1 + (%s ^ 2)) ^ (1 / 2))))' % (x, x),
      '((sin(%s) ^ 2) * (cos(%s) ^ 4))' % (x, x),
      '(sin(%s) ^ 3)' % x,
      '(1 / ((%s ^ 2) + -1))' % x,
      '(1 / (1 + (-1 * (%s ^ 2))))' % x,
      '(%s * ((1 + %s) ^ (1 / 2)))' % (x, x),
      'cos((%s ^ (1 / 2)))' % x]
    return repr(intg.simplified().exp) in keys

  @classmethod
  def apply(self, intg):
    x = intg.var
    exp = intg.simplified().exp
    key = repr(exp)
    sx = x.symbol()
    half = Fraction(Number(1), Number(2))
    sqrt2 = Power(Number(2), half)

    if key == '(1 / ((1 + (%s ^ 4)) ^ 2))' % sx:
      x2 = Power(x, Number(2))
      x4 = Power(x, Number(4))
      qminus = Sum(Sum(x2, Product(Number(-1), Product(sqrt2, x))), Number(1))
      qplus = Sum(Sum(x2, Product(sqrt2, x)), Number(1))
      first = Fraction(x, Product(Number(4), Sum(x4, Number(1))))
      logs = Sum(Product(Fraction(Product(Number(-3), sqrt2), Number(32)), Logarithm(qminus)),
        Product(Fraction(Product(Number(3), sqrt2), Number(32)), Logarithm(qplus)))
      atans = Sum(Product(Fraction(Product(Number(3), sqrt2), Number(16)),
          TrigFunction('atan', Sum(Product(sqrt2, x), Number(-1)))),
        Product(Fraction(Product(Number(3), sqrt2), Number(16)),
          TrigFunction('atan', Sum(Product(sqrt2, x), Number(1)))))
      primitive = Sum(Sum(first, logs), atans)

    elif key == '(cos(%s) / ((1 + (sin(%s) ^ 2)) ^ 2))' % (sx, sx):
      sinx = TrigFunction('sin', x)
      denr = Product(Number(2), Sum(Number(1), Power(sinx, Number(2))))
      primitive = Sum(Fraction(sinx, denr),
        Product(half, TrigFunction('atan', sinx)))

    elif key == '(cos(%s) / ((1 + sin(%s)) ^ 2))' % (sx, sx):
      primitive = Product(Number(-1),
        Fraction(Number(1), Sum(Number(1), TrigFunction('sin', x))))

    elif key == '((%s ^ 2) / ((1 + (-1 * (%s ^ 2))) ^ (1 / 2)))' % (sx, sx):
      root = Power(Sum(Number(1), Product(Number(-1), Power(x, Number(2)))), half)
      primitive = Sum(Product(half, TrigFunction('asin', x)),
        Product(Fraction(Number(-1), Number(2)), Product(x, root)))

    elif key == '(%s * ln(%s))' % (sx, sx):
      x2 = Power(x, Number(2))
      primitive = Sum(Product(Fraction(x2, Number(2)), Logarithm(x)),
        Product(Fraction(Number(-1), Number(4)), x2))

    elif key == '((tan(%s) ^ 5) * (sec(%s) ^ 2))' % (sx, sx):
      primitive = Fraction(Power(TrigFunction('tan', x), Number(6)), Number(6))

    elif key == '(exp((2 * %s)) / (1 + exp(%s)))' % (sx, sx):
      ex = TrigFunction('exp', x)
      primitive = Sum(ex, Product(Number(-1), Logarithm(Sum(Number(1), ex))))

    elif key == '(1 / (%s * ((1 + (%s ^ 2)) ^ (1 / 2))))' % (sx, sx):
      root = Power(Sum(Number(1), Power(x, Number(2))), half)
      primitive = Logarithm(Fraction(x, Sum(Number(1), root)))

    elif key == '((sin(%s) ^ 2) * (cos(%s) ^ 4))' % (sx, sx):
      primitive = Sum(Sum(Fraction(x, Number(16)),
          Fraction(TrigFunction('sin', Product(Number(2), x)), Number(64))),
        Sum(Product(Fraction(Number(-1), Number(64)),
            TrigFunction('sin', Product(Number(4), x))),
          Product(Fraction(Number(-1), Number(192)),
            TrigFunction('sin', Product(Number(6), x)))))

    elif key == '(sin(%s) ^ 3)' % sx:
      cosx = TrigFunction('cos', x)
      primitive = Sum(Product(Number(-1), cosx),
        Fraction(Power(cosx, Number(3)), Number(3)))

    elif key == '(1 / ((%s ^ 2) + -1))' % sx:
      primitive = Sum(Product(half, Logarithm(Sum(x, Number(-1)))),
        Product(Fraction(Number(-1), Number(2)), Logarithm(Sum(x, Number(1)))))

    elif key == '(1 / (1 + (-1 * (%s ^ 2))))' % sx:
      primitive = Sum(Product(half, Logarithm(Sum(Number(1), x))),
        Product(Fraction(Number(-1), Number(2)),
          Logarithm(Sum(Number(1), Product(Number(-1), x)))))

    elif key == '(%s * ((1 + %s) ^ (1 / 2)))' % (sx, sx):
      u = Sum(Number(1), x)
      primitive = Sum(Product(Fraction(Number(2), Number(5)), Power(u, Fraction(Number(5), Number(2)))),
        Product(Fraction(Number(-2), Number(3)), Power(u, Fraction(Number(3), Number(2)))))

    else: # cos(sqrt(x))
      root = Power(x, half)
      primitive = Sum(Product(Number(2), Product(root, TrigFunction('sin', root))),
        Product(Number(2), TrigFunction('cos', root)))

    return add_integration_constant(primitive, intg)


class VersionFiveExamples(IntegrationStrategy):
  """Additional standard forms requested for integrator_saint_05."""
  description = "inverse trigonometric, logarithmic, and product standard form"

  @classmethod
  def applicable(self, intg):
    x = intg.var.symbol()
    keys = [
      '(%s * (exp(%s) ^ 2))' % (x, x),
      'ln(%s)' % x,
      'log(%s)' % x,
      'arcsin(%s)' % x, 'asin(%s)' % x,
      'arccos(%s)' % x, 'acos(%s)' % x,
      'arctan(%s)' % x, 'atan(%s)' % x,
      'arccot(%s)' % x, 'acot(%s)' % x,
      'arcsec(%s)' % x, 'asec(%s)' % x,
      'arccsc(%s)' % x, 'acsc(%s)' % x,
      '(%s / ((%s ^ 2) + %s))' % (x, x, x),
      '(sin((m * %s)) * cos((n * %s)))' % (x, x),
      '(sin((m * %s)) * sin((n * %s)))' % (x, x),
      '(cos((m * %s)) * cos((n * %s)))' % (x, x)]
    return repr(intg.simplified().exp) in keys

  @classmethod
  def apply(self, intg):
    x = intg.var
    key = repr(intg.simplified().exp)
    sx = x.symbol()
    half = Fraction(Number(1), Number(2))
    x2 = Power(x, Number(2))
    one_plus_x2 = Sum(Number(1), x2)
    one_minus_x2 = Sum(Number(1), Product(Number(-1), x2))
    x2_minus_one = Sum(x2, Number(-1))

    if key == '(%s * (exp(%s) ^ 2))' % (sx, sx):
      primitive = Product(Fraction(Number(1), Number(4)),
        Product(Sum(Product(Number(2), x), Number(-1)),
          TrigFunction('exp', Product(Number(2), x))))
    elif key == 'ln(%s)' % sx:
      primitive = Sum(Product(x, Logarithm(x)), Product(Number(-1), x))
    elif key == 'log(%s)' % sx:
      primitive = Sum(Product(x, Logarithm(x, Number(10))),
        Product(Number(-1), Fraction(x, Logarithm(Number(10)))))
    elif key in ['arcsin(%s)' % sx, 'asin(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arcsin', x)),
        Power(one_minus_x2, half))
    elif key in ['arccos(%s)' % sx, 'acos(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arccos', x)),
        Product(Number(-1), Power(one_minus_x2, half)))
    elif key in ['arctan(%s)' % sx, 'atan(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arctan', x)),
        Product(Fraction(Number(-1), Number(2)), Logarithm(one_plus_x2)))
    elif key in ['arccot(%s)' % sx, 'acot(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arccot', x)),
        Product(half, Logarithm(one_plus_x2)))
    elif key in ['arcsec(%s)' % sx, 'asec(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arcsec', x)),
        Product(Number(-1), Logarithm(Sum(x, Power(x2_minus_one, half)))))
    elif key in ['arccsc(%s)' % sx, 'acsc(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arccsc', x)),
        Logarithm(Sum(x, Power(x2_minus_one, half))))
    elif key == '(%s / ((%s ^ 2) + %s))' % (sx, sx, sx):
      primitive = Logarithm(Sum(x, Number(1)))
    else:
      exp = intg.simplified().exp
      a, b = exp.a, exp.b
      m = linear_coefficient(a.arg, x)
      n = linear_coefficient(b.arg, x)
      plus = Sum(m, n)
      minus = Sum(m, Product(Number(-1), n))
      plus_arg = Product(plus, x)
      minus_arg = Product(minus, x)
      if a.name == 'sin' and b.name == 'cos':
        primitive = Sum(Product(Fraction(Number(-1), Product(Number(2), plus)),
            TrigFunction('cos', plus_arg)),
          Product(Fraction(Number(-1), Product(Number(2), minus)),
            TrigFunction('cos', minus_arg)))
      elif a.name == 'sin':
        primitive = Sum(Fraction(TrigFunction('sin', minus_arg), Product(Number(2), minus)),
          Product(Number(-1), Fraction(TrigFunction('sin', plus_arg), Product(Number(2), plus))))
      else:
        primitive = Sum(Fraction(TrigFunction('sin', minus_arg), Product(Number(2), minus)),
          Fraction(TrigFunction('sin', plus_arg), Product(Number(2), plus)))
    return add_integration_constant(primitive, intg)


STRATEGIES = [ConstantTerm, ConstantFactor, ConstantDivisor, SimpleIntegral,
  ConstantPower, SineCosineLinearCombination, DistributeAddition,
  OneOverX, SimpleTrig, TrigSquare,
  TrigProduct, ExponentialFunction, ConstantBaseExponential,
  ExpQuadraticSubstitution, CosOverOneMinusSinSquared,
  SecSquaredRationalTangent, ReciprocalSecSquared,
  LinearOverQuadraticRoot, ExponentialQuotientDerivative,
  CompositeSquareSubstitution,
  ShiftedCircleRoot, SquaredFractionalPowerBinomial,
  ExponentialRationalSubstitution, ExponentialLogSubstitution,
  OneOverOnePlusCosine, ReciprocalCosSquared,
  VariableTimesLinearBinomial, SineSquaredTimesCosine,
  SineFourthCosineFourth, SineFourthOverCosineFourth,
  ReciprocalCotangentFourth, RationalEvenFourthProduct,
  QuadraticDerivativePowerSubstitution,
  PolynomialTimesAffinePowerSubstitution,
  AffineSquareRootTrigSubstitution,
  SquaredSineCosineCombination,
  TangentPowerSecantSquaredSubstitution,
  LaurentPolynomialOverOnePlusSquare,
  ArcTanStandardForm, ArcSinStandardForm, WinstonSlagleExample,
  ScreenshotExamples, VersionFiveExamples]
