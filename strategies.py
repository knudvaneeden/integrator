"""
Integration Strategies

This file is a booklet of strategies for
solving integration problems.

Each strategy is a subtype of IntegrationStrategy
and can apply itself to an expression.
"""

from elements import *
from fractions import Fraction as Rational
from math import comb, factorial, isqrt

# add on integration uncertainty variable
def add_integration_constant(expr, original_intg):
  if not original_intg.include_constant:
    return expr
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
    primitive = Product(constant_factor,
      Integral(integrand, intg.var, include_constant=False))
    return add_integration_constant(primitive, intg)


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
    primitive = Product(Fraction(Number(1), exp.denr),
      Integral(exp.numr, intg.var, include_constant=False))
    return add_integration_constant(primitive, intg)


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
    new_expr = Sum(
      Integral(exp.a, intg.var, include_constant=False),
      Integral(exp.b, intg.var, include_constant=False))
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
    primitive = Product(intg.simplified().exp.numr, Logarithm(intg.var))
    return add_integration_constant(primitive, intg)


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


class TrigNonnegativeIntegerPowerReduction(IntegrationStrategy):
  """Reduce integral sin(u)^n or cos(u)^n for integer n >= 2."""
  description = "integer sine or cosine power reduction"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Power) or not exp.base.is_a(TrigFunction)
      or exp.base.name not in ('sin', 'cos')
      or not exp.exponent.is_a(Number)
      or not isinstance(exp.exponent.n, int) or exp.exponent.n < 2):
      return None
    slope = linear_coefficient(exp.base.arg, intg.var)
    if slope == None or slope == Number(0): return None
    return exp.base, exp.exponent.n, slope

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    trig, exponent, slope = self._parts(intg)
    other_name = 'sin' if trig.name == 'cos' else 'cos'
    other = TrigFunction(other_name, trig.arg)
    terms = []
    multiplier = Rational(1)
    remaining = exponent
    while remaining >= 2:
      boundary_power = (trig if remaining == 2
        else Power(trig, Number(remaining - 1)))
      coefficient = multiplier / Rational(remaining)
      if trig.name == 'sin': coefficient = -coefficient
      term = Fraction(_scale_by_rational(Product(other, boundary_power),
        coefficient), slope).simplified()
      terms.append(term)
      multiplier *= Rational(remaining - 1, remaining)
      remaining -= 2
    if remaining == 0:
      terms.append(_scale_by_rational(intg.var, multiplier))
    else:
      primitive_trig = (TrigFunction('sin', trig.arg) if trig.name == 'cos'
        else Product(Number(-1), TrigFunction('cos', trig.arg)))
      terms.append(Fraction(_scale_by_rational(primitive_trig, multiplier),
        slope).simplified())
    primitive = terms[0]
    for term in terms[1:]: primitive = Sum(primitive, term)
    return add_integration_constant(primitive, intg)


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


class PolynomialSineCosineProduct(IntegrationStrategy):
  """Integrate P(x)*sin(a*x+b)*cos(c*x+d) for rational P, a, b, c, d."""
  description = ("product-to-sum followed by polynomial/trigonometric "
    "integration by parts")

  @classmethod
  def _parts(self, intg):
    factors = []

    def collect(expr):
      if expr.is_a(Product):
        collect(expr.a)
        collect(expr.b)
      else:
        factors.append(expr)

    collect(intg.simplified().exp)
    sines = [factor for factor in factors
      if factor.is_a(TrigFunction) and factor.name == 'sin']
    cosines = [factor for factor in factors
      if factor.is_a(TrigFunction) and factor.name == 'cos']
    if len(sines) != 1 or len(cosines) != 1: return None
    sine, cosine = sines[0], cosines[0]
    sine_phase = _laurent_polynomial_coefficients(sine.arg, intg.var)
    cosine_phase = _laurent_polynomial_coefficients(cosine.arg, intg.var)
    if sine_phase == None or cosine_phase == None: return None
    if any(degree < 0 or degree > 1 for degree in sine_phase): return None
    if any(degree < 0 or degree > 1 for degree in cosine_phase): return None
    if sine_phase.get(1, Rational(0)) == 0: return None
    if cosine_phase.get(1, Rational(0)) == 0: return None

    polynomial_factors = [factor for factor in factors
      if factor is not sine and factor is not cosine]
    polynomial = Number(1)
    for factor in polynomial_factors:
      polynomial = Product(polynomial, factor).simplified()
    coefficients = _laurent_polynomial_coefficients(polynomial, intg.var)
    if coefficients == None or any(degree < 0 for degree in coefficients):
      return None
    return sine.arg, cosine.arg, coefficients

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    sine_phase, cosine_phase, coefficients = self._parts(intg)
    x = intg.var

    def polynomial_primitive():
      terms = []
      for degree, coefficient in sorted(coefficients.items()):
        power = x if degree == 0 else Power(x, Number(degree + 1))
        terms.append(_scale_by_rational(power,
          coefficient / Rational(degree + 1)))
      result = terms[0] if terms else Number(0)
      for term in terms[1:]: result = Sum(result, term)
      return result

    def monomial_trig_primitive(degree, name, phase, frequency):
      trig_name = 'cos' if name == 'sin' else 'sin'
      trig = TrigFunction(trig_name, phase)
      power = x if degree == 1 else Power(x, Number(degree))
      leading_sign = Rational(-1) if name == 'sin' else Rational(1)
      leading_term = trig if degree == 0 else Product(power, trig).simplified()
      leading = _scale_by_rational(leading_term,
        leading_sign / frequency)
      if degree == 0: return leading
      other_name = 'cos' if name == 'sin' else 'sin'
      remainder_sign = Rational(1) if name == 'sin' else Rational(-1)
      remainder = monomial_trig_primitive(degree - 1, other_name,
        phase, frequency)
      return Sum(leading, _scale_by_rational(remainder,
        remainder_sign * Rational(degree) / frequency))

    def polynomial_sine_primitive(phase):
      phase_coefficients = _laurent_polynomial_coefficients(phase, x)
      frequency = phase_coefficients.get(1, Rational(0))
      if frequency == 0:
        return Product(TrigFunction('sin', phase), polynomial_primitive()).simplified()
      terms = [_scale_by_rational(
        monomial_trig_primitive(degree, 'sin', phase, frequency), coefficient)
        for degree, coefficient in sorted(coefficients.items())]
      result = terms[0] if terms else Number(0)
      for term in terms[1:]: result = Sum(result, term)
      return result

    plus_phase = Sum(sine_phase, cosine_phase).simplified()
    if sine_phase == cosine_phase:
      primitive = _scale_by_rational(
        polynomial_sine_primitive(plus_phase), Rational(1, 2))
    else:
      minus_phase = Sum(sine_phase,
        Product(Number(-1), cosine_phase)).simplified()
      primitive = _scale_by_rational(Sum(
        polynomial_sine_primitive(plus_phase),
        polynomial_sine_primitive(minus_phase)), Rational(1, 2))
    return add_integration_constant(primitive, intg)


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


def _rational_power_monomial(expr, var):
  """Return (coefficient, exponent) for c*x^r with rational c and r."""
  value = _rational_value(expr)
  if value != None: return value, Rational(0)
  if expr == var: return Rational(1), Rational(1)
  if expr.is_a(Power) and expr.base == var:
    exponent = _rational_value(expr.exponent)
    if exponent != None: return Rational(1), exponent
  if expr.is_a(Product):
    a = _rational_power_monomial(expr.a, var)
    b = _rational_power_monomial(expr.b, var)
    if a != None and b != None: return a[0] * b[0], a[1] + b[1]
  if expr.is_a(Fraction):
    numr = _rational_power_monomial(expr.numr, var)
    denr = _rational_power_monomial(expr.denr, var)
    if numr != None and denr != None and denr[0] != 0:
      return numr[0] / denr[0], numr[1] - denr[1]
  return None


class PolynomialTimesRationalPowerBinomialExpansion(IntegrationStrategy):
  """Integrate P(x)*(a*x^r+b*x^s)^N by finite binomial expansion."""
  description = ("expand an integer power of a rational-power binomial, "
    "combine powers, and apply the power rule")

  @classmethod
  def _parts(self, intg):
    factors = []

    def collect(expr):
      if expr.is_a(Product):
        collect(expr.a)
        collect(expr.b)
      else:
        factors.append(expr)

    collect(intg.simplified().exp)
    candidate_index = None
    candidate = None
    for index, factor in enumerate(factors):
      if not factor.is_a(Power) or not factor.base.is_a(Sum): continue
      exponent = _rational_value(factor.exponent)
      if (exponent == None or exponent.denominator != 1
          or exponent < 0):
        continue
      first = _rational_power_monomial(factor.base.a, intg.var)
      second = _rational_power_monomial(factor.base.b, intg.var)
      if first != None and second != None and first[1] != second[1]:
        candidate_index = index
        candidate = (first, second, int(exponent))
        break
    if candidate == None: return None

    multiplier = Number(1)
    for index, factor in enumerate(factors):
      if index != candidate_index:
        multiplier = Product(multiplier, factor).simplified()
    polynomial = _laurent_polynomial_coefficients(multiplier, intg.var)
    if polynomial == None: return None
    return candidate[0], candidate[1], candidate[2], polynomial

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    first, second, binomial_exponent, polynomial = self._parts(intg)
    expanded = {}
    for degree, polynomial_coefficient in polynomial.items():
      for j in range(binomial_exponent + 1):
        exponent = (Rational(degree)
          + first[1] * (binomial_exponent - j) + second[1] * j)
        coefficient = (polynomial_coefficient
          * Rational(comb(binomial_exponent, j))
          * first[0] ** (binomial_exponent - j) * second[0] ** j)
        expanded[exponent] = expanded.get(exponent, Rational(0)) + coefficient

    terms = []
    for exponent in sorted(expanded.keys(), reverse=True):
      coefficient = expanded[exponent]
      if coefficient == 0: continue
      integrated_exponent = exponent + 1
      if integrated_exponent == 0:
        term = _scale_by_rational(Logarithm(intg.var), coefficient)
      else:
        power = (intg.var if integrated_exponent == 1 else
          Power(intg.var, _rational_expression(integrated_exponent)))
        term = _scale_by_rational(power, coefficient / integrated_exponent)
      terms.append(term)
    primitive = terms[0] if terms else Number(0)
    for term in terms[1:]: primitive = Sum(primitive, term)
    return add_integration_constant(primitive, intg)


class RationalPowerTimesExponentialPowerSubstitution(IntegrationStrategy):
  """Integrate c*x^p*exp(a*x^r+b) when (p+1)/r is a positive integer."""
  description = ("substitute u=x^r and integrate the resulting integer "
    "power times an exponential")

  @classmethod
  def _affine_power_argument(self, expr, var):
    constant = Rational(0)
    monomial = None
    if expr.is_a(Sum):
      first_value = _rational_value(expr.a)
      second_value = _rational_value(expr.b)
      if first_value != None:
        constant = first_value
        monomial = _rational_power_monomial(expr.b, var)
      elif second_value != None:
        constant = second_value
        monomial = _rational_power_monomial(expr.a, var)
    else:
      monomial = _rational_power_monomial(expr, var)
    if monomial == None or monomial[0] == 0 or monomial[1] == 0:
      return None
    return monomial[0], monomial[1], constant

  @classmethod
  def _parts(self, intg):
    factors = []

    def collect(expr):
      if expr.is_a(Product):
        collect(expr.a)
        collect(expr.b)
      else:
        factors.append(expr)

    collect(intg.simplified().exp)
    exponentials = [factor for factor in factors
      if factor.is_a(TrigFunction) and factor.name == 'exp']
    if len(exponentials) != 1: return None
    exponential = exponentials[0]
    multiplier = Number(1)
    removed = False
    for factor in factors:
      if factor is exponential and not removed:
        removed = True
      else:
        multiplier = Product(multiplier, factor).simplified()
    monomial = _rational_power_monomial(multiplier, intg.var)
    argument = self._affine_power_argument(exponential.arg, intg.var)
    if monomial == None or argument == None: return None
    coefficient, p = monomial
    exponential_coefficient, r, unused_constant = argument
    transformed_power = (p + 1) / r
    if transformed_power.denominator != 1 or transformed_power <= 0:
      return None
    return (coefficient, exponential, exponential_coefficient, r,
      int(transformed_power) - 1)

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    coefficient, exponential, a, r, degree = self._parts(intg)
    terms = []
    for j in range(degree + 1):
      term_degree = degree - j
      term_coefficient = (Rational((-1) ** j * factorial(degree),
        factorial(term_degree)) / (a ** (j + 1)))
      x_exponent = r * term_degree
      if x_exponent == 0:
        power = Number(1)
      elif x_exponent == 1:
        power = intg.var
      else:
        power = Power(intg.var, _rational_expression(x_exponent))
      terms.append(_scale_by_rational(power, term_coefficient))
    polynomial = terms[0]
    for term in terms[1:]: polynomial = Sum(polynomial, term)
    product = (exponential if polynomial == Number(1) else
      Product(exponential, polynomial))
    primitive = _scale_by_rational(product, coefficient / r)
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


class ReciprocalOnePlusOrMinusCosine(IntegrationStrategy):
  """Integrate 1/(1+cos(ax+b)) and 1/(1-cos(ax+b))."""
  description = "half-angle identity for reciprocal one plus or minus cosine"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Fraction) or exp.numr != Number(1)
      or not exp.denr.is_a(Sum)):
      return None
    constant = _rational_value(exp.denr.a)
    trig = _rational_trig_term(exp.denr.b)
    if constant == None or trig == None:
      constant = _rational_value(exp.denr.b)
      trig = _rational_trig_term(exp.denr.a)
    if constant != 1 or trig == None or trig[0] != 'cos' or abs(trig[2]) != 1:
      return None
    phase = _laurent_polynomial_coefficients(trig[1], intg.var)
    if phase == None or phase.get(1, Rational(0)) == 0: return None
    if any(degree < 0 or degree > 1 for degree in phase): return None
    return trig[1], trig[2], phase[1]

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    phase, sign, frequency = self._parts(intg)
    half_phase = Fraction(phase, Number(2))
    if sign == 1:
      primitive = _scale_by_rational(TrigFunction('tan', half_phase),
        Rational(1) / frequency)
    else:
      primitive = _scale_by_rational(TrigFunction('cot', half_phase),
        Rational(-1) / frequency)
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


def _rational_square_root_expression(value):
  numerator_root = isqrt(value.numerator)
  denominator_root = isqrt(value.denominator)
  if (numerator_root * numerator_root == value.numerator
    and denominator_root * denominator_root == value.denominator):
    return _rational_expression(Rational(numerator_root, denominator_root))
  return Power(_rational_expression(value), Fraction(Number(1), Number(2)))


class LinearOverQuadraticSquareRoot(IntegrationStrategy):
  """Integrate (m*x+n)/sqrt(a*x^2+b*x+c) for rational coefficients."""
  description = "linear numerator over a general quadratic square root"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Fraction) or not exp.denr.is_a(Power)
      or exp.denr.exponent != Fraction(Number(1), Number(2))):
      return None
    numerator = _laurent_polynomial_coefficients(exp.numr, intg.var)
    quadratic = _laurent_polynomial_coefficients(exp.denr.base, intg.var)
    if numerator == None or quadratic == None: return None
    if any(degree < 0 or degree > 1 for degree in numerator.keys()): return None
    if any(degree < 0 or degree > 2 for degree in quadratic.keys()): return None
    a = quadratic.get(2, Rational(0))
    if a == 0: return None
    return (exp.denr.base, numerator.get(1, Rational(0)),
      numerator.get(0, Rational(0)), a,
      quadratic.get(1, Rational(0)), quadratic.get(0, Rational(0)))

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    quadratic, m, n, a, b, c = self._parts(intg)
    x = intg.var
    root = Power(quadratic, Fraction(Number(1), Number(2)))
    terms = []
    if m != 0:
      terms.append(_scale_by_rational(root, m / a))
    remainder = n - m * b / (Rational(2) * a)
    if remainder != 0:
      if a > 0:
        sqrt_a = _rational_square_root_expression(a)
        sqrt_a_value = _rational_value(sqrt_a)
        root_part = (_scale_by_rational(root, sqrt_a_value)
          if sqrt_a_value != None else Product(sqrt_a, root))
        log_arg = Sum(root_part,
          Sum(_scale_by_rational(x, a),
            _rational_expression(b / Rational(2))))
        standard = Fraction(Logarithm(log_arg), sqrt_a)
      else:
        discriminant = b * b - Rational(4) * a * c
        if discriminant <= 0: return add_integration_constant(Number(0), intg)
        sqrt_discriminant = _rational_square_root_expression(discriminant)
        sqrt_discriminant_value = _rational_value(sqrt_discriminant)
        if sqrt_discriminant_value != None:
          asin_arg = Sum(_scale_by_rational(x,
              Rational(-2) * a / sqrt_discriminant_value),
            _rational_expression(-b / sqrt_discriminant_value))
        else:
          asin_arg = Fraction(Sum(Product(_rational_expression(Rational(-2) * a), x),
            _rational_expression(-b)), sqrt_discriminant)
        sqrt_minus_a = _rational_square_root_expression(-a)
        standard = Fraction(TrigFunction('arcsin', asin_arg), sqrt_minus_a)
      terms.append(_scale_by_rational(standard, remainder))
    primitive = terms[0] if terms else Number(0)
    for term in terms[1:]: primitive = Sum(primitive, term)
    return add_integration_constant(primitive, intg)


class ReciprocalXSquaredQuadraticSquareRoot(IntegrationStrategy):
  """Integrate k/(x^2*sqrt(a*x^2+c)) for constant k, a, and c."""
  description = "reciprocal x squared times an even quadratic square root"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Fraction) or not is_constant(exp.numr, intg.var):
      return None
    factors = [exp.denr]
    if exp.denr.is_a(Product): factors = [exp.denr.a, exp.denr.b]
    x_squared = Power(intg.var, Number(2))
    x_factor = None
    root = None
    for factor in factors:
      if factor == x_squared: x_factor = factor
      elif (factor.is_a(Power)
        and factor.exponent == Fraction(Number(1), Number(2))):
        root = factor
    if x_factor == None or root == None: return None
    coefficients = _symbolic_polynomial_coefficients(root.base, intg.var)
    if coefficients == None or 1 in coefficients: return None
    if any(degree not in (0, 2) for degree in coefficients): return None
    if 2 not in coefficients or 0 not in coefficients: return None
    constant = coefficients[0].simplified()
    if constant == Number(0): return None
    return exp.numr, root, constant

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    numerator, root, constant = self._parts(intg)
    primitive = Product(Number(-1),
      Fraction(Product(numerator, root), Product(constant, intg.var)))
    return add_integration_constant(primitive.simplified(), intg)


def _symbolic_polynomial_coefficients(expr, var):
  """Small symbolic-coefficient polynomial extractor used for quadratic roots."""
  if expr == var: return {1: Number(1)}
  if expr.is_a(Power) and expr.base == var and expr.exponent == Number(2):
    return {2: Number(1)}
  if is_constant(expr, var): return {0: expr}
  if expr.is_a(Sum):
    a = _symbolic_polynomial_coefficients(expr.a, var)
    b = _symbolic_polynomial_coefficients(expr.b, var)
    if a == None or b == None: return None
    result = dict(a)
    for degree, coefficient in b.items():
      result[degree] = (Sum(result[degree], coefficient).simplified()
        if degree in result else coefficient)
    return result
  if expr.is_a(Product):
    if is_constant(expr.a, var):
      monomial = _symbolic_polynomial_coefficients(expr.b, var)
      if monomial != None and len(monomial) == 1:
        degree, coefficient = list(monomial.items())[0]
        return {degree: Product(expr.a, coefficient).simplified()}
    if is_constant(expr.b, var):
      monomial = _symbolic_polynomial_coefficients(expr.a, var)
      if monomial != None and len(monomial) == 1:
        degree, coefficient = list(monomial.items())[0]
        return {degree: Product(expr.b, coefficient).simplified()}
  return None


class MonicQuadraticParameterSquareRoot(IntegrationStrategy):
  """Integrate 1/sqrt(x^2+B*x+C) with symbolic constants B and C."""
  description = "monic quadratic square-root standard form with symbolic parameters"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Fraction) or exp.numr != Number(1)
      or not exp.denr.is_a(Power)
      or exp.denr.exponent != Fraction(Number(1), Number(2))):
      return None
    coefficients = _symbolic_polynomial_coefficients(exp.denr.base, intg.var)
    if coefficients == None or coefficients.get(2) != Number(1): return None
    if any(degree < 0 or degree > 2 for degree in coefficients): return None
    return exp.denr.base, coefficients.get(1, Number(0))

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    quadratic, linear_coefficient_expr = self._parts(intg)
    root = Power(quadratic, Fraction(Number(1), Number(2)))
    linear_value = _rational_value(linear_coefficient_expr)
    half_linear = (_rational_expression(linear_value / Rational(2))
      if linear_value != None else Product(Fraction(Number(1), Number(2)),
        linear_coefficient_expr).simplified())
    primitive = Logarithm(Sum(root, Sum(intg.var, half_linear)))
    return add_integration_constant(primitive, intg)


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
      else:
        for candidate_base, candidate_multiplier in [(exp.a, exp.b), (exp.b, exp.a)]:
          base_coefficients = _laurent_polynomial_coefficients(candidate_base, intg.var)
          if (base_coefficients != None
            and base_coefficients.get(1, Rational(0)) != 0
            and all(degree in [0, 1] for degree in base_coefficients.keys())):
            power, multiplier = Power(candidate_base, Number(1)), candidate_multiplier
            break
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


def _constant_plus_trig(expr):
  """Return (d, e, trig) for d+e*trig(phase), including d=0."""
  direct = _rational_trig_term(expr)
  if direct != None:
    return Rational(0), direct[2], TrigFunction(direct[0], direct[1])
  if not expr.is_a(Sum): return None
  constant = _rational_value(expr.a)
  trig_term = _rational_trig_term(expr.b)
  if constant == None or trig_term == None:
    constant = _rational_value(expr.b)
    trig_term = _rational_trig_term(expr.a)
  if constant == None or trig_term == None or trig_term[2] == 0: return None
  return constant, trig_term[2], TrigFunction(trig_term[0], trig_term[1])


class TrigBinomialPowerSubstitution(IntegrationStrategy):
  """Integrate c*f'(u)*(d+e*f(u))^p for f=sin or cos and affine u."""
  description = "substitution v=d+e*sin(ax+b) or v=d+e*cos(ax+b)"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    derivative_term = None
    base = None
    exponent = None
    if exp.is_a(Fraction):
      derivative_term = _rational_trig_term(exp.numr)
      if exp.denr.is_a(Power):
        denr_exponent = _rational_value(exp.denr.exponent)
        if denr_exponent != None:
          base, exponent = exp.denr.base, -denr_exponent
      else:
        base, exponent = exp.denr, Rational(-1)
    elif exp.is_a(Product):
      for derivative_candidate, power_candidate in [(exp.a, exp.b), (exp.b, exp.a)]:
        candidate = _rational_trig_term(derivative_candidate)
        if candidate != None:
          derivative_term = candidate
          if power_candidate.is_a(Power):
            power_value = _rational_value(power_candidate.exponent)
            if power_value != None:
              base, exponent = power_candidate.base, power_value
          else:
            base, exponent = power_candidate, Rational(1)
          break
    if derivative_term == None or base == None or exponent == None: return None
    binomial = _constant_plus_trig(base)
    if binomial == None: return None
    unused_constant, inner_coefficient, inner_trig = binomial
    derivative_name, derivative_phase, outer_coefficient = derivative_term
    if inner_trig.arg != derivative_phase: return None
    if inner_trig.name == 'sin' and derivative_name == 'cos': derivative_sign = Rational(1)
    elif inner_trig.name == 'cos' and derivative_name == 'sin': derivative_sign = Rational(-1)
    else: return None
    phase = _laurent_polynomial_coefficients(derivative_phase, intg.var)
    if phase == None or phase.get(1, Rational(0)) == 0: return None
    if any(degree < 0 or degree > 1 for degree in phase.keys()): return None
    substitution_factor = (outer_coefficient /
      (inner_coefficient * derivative_sign * phase[1]))
    return base, exponent, substitution_factor

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    base, exponent, substitution_factor = self._parts(intg)
    if exponent == -1:
      primitive = _scale_by_rational(Logarithm(base), substitution_factor)
    else:
      new_exponent = exponent + 1
      power = base if new_exponent == 1 else Power(base,
        _rational_expression(new_exponent))
      primitive = _scale_by_rational(power, substitution_factor / new_exponent)
    return add_integration_constant(primitive, intg)


class ArcTangentAffineSquareRoot(IntegrationStrategy):
  """Integrate arctan(sqrt(a*x+b)) for constants a and b."""
  description = "arctangent of an affine square root"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(TrigFunction) or exp.name not in ('arctan', 'atan')
      or not exp.arg.is_a(Power)
      or exp.arg.exponent != Fraction(Number(1), Number(2))):
      return None
    affine = exp.arg.base
    coefficient = linear_coefficient(affine, intg.var)
    if coefficient == None or coefficient == Number(0): return None
    return exp, affine, coefficient

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    arctangent, affine, coefficient = self._parts(intg)
    root = arctangent.arg
    numerator = Sum(Product(Sum(affine, Number(1)), arctangent),
      Product(Number(-1), root))
    return add_integration_constant(Fraction(numerator, coefficient).simplified(), intg)


def _rational_trig_square(expr):
  coefficient = Rational(1)
  power = expr
  if expr.is_a(Product):
    left = _rational_value(expr.a)
    right = _rational_value(expr.b)
    if left != None: coefficient, power = left, expr.b
    elif right != None: coefficient, power = right, expr.a
  if (power.is_a(Power) and power.exponent == Number(2)
    and power.base.is_a(TrigFunction) and power.base.name in ['sin', 'cos']):
    return coefficient, power.base
  return None


def _sine_cosine_or_tangent_power(expr):
  """Return (name, phase, rational exponent) for a trigonometric power."""
  if expr.is_a(TrigFunction) and expr.name in ['sin', 'cos', 'tan']:
    return expr.name, expr.arg, Rational(1)
  if (expr.is_a(Power) and expr.base.is_a(TrigFunction)
      and expr.base.name in ['sin', 'cos', 'tan']):
    exponent = _rational_value(expr.exponent)
    if exponent != None:
      return expr.base.name, expr.base.arg, exponent
  return None


class OddSineCosinePowerSubstitution(IntegrationStrategy):
  """Integrate rational powers of sin, cos and tan after power normalization."""
  description = ("normalize tangent powers, then use an odd sine/cosine "
    "power substitution")

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Product): return None
    factors = []

    def collect(item):
      if item.is_a(Product):
        collect(item.a)
        collect(item.b)
      else:
        factors.append(item)

    collect(exp)
    powers = {'sin': Rational(0), 'cos': Rational(0), 'tan': Rational(0)}
    phase_expression = None
    for factor in factors:
      trig_power = _sine_cosine_or_tangent_power(factor)
      if trig_power == None: return None
      name, factor_phase, exponent = trig_power
      if phase_expression == None: phase_expression = factor_phase
      elif phase_expression != factor_phase: return None
      powers[name] += exponent
    if phase_expression == None: return None

    # tan(u)^r = sin(u)^r / cos(u)^r.
    sine_exponent = powers['sin'] + powers['tan']
    cosine_exponent = powers['cos'] - powers['tan']
    phase = _laurent_polynomial_coefficients(phase_expression, intg.var)
    if phase == None or any(degree < 0 or degree > 1 for degree in phase):
      return None
    frequency = phase.get(1, Rational(0))
    if frequency == 0: return None

    sine_odd = (sine_exponent.denominator == 1 and sine_exponent > 0
      and sine_exponent.numerator % 2 == 1)
    cosine_odd = (cosine_exponent.denominator == 1 and cosine_exponent > 0
      and cosine_exponent.numerator % 2 == 1)
    if not sine_odd and not cosine_odd: return None
    # Prefer cosine when both are odd: u=sin(phase) gives the conventional form.
    if cosine_odd:
      return (phase_expression, 'sin', sine_exponent,
        (cosine_exponent.numerator - 1) // 2, frequency, Rational(1))
    return (phase_expression, 'cos', cosine_exponent,
      (sine_exponent.numerator - 1) // 2, frequency, Rational(-1))

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    phase, substitution_name, base_exponent, even_half, frequency, sign = \
      self._parts(intg)
    substitution = TrigFunction(substitution_name, phase)
    terms = []
    for j in range(even_half + 1):
      coefficient = (sign * Rational(comb(even_half, j))
        * (Rational(-1) ** j) / frequency)
      integrated_exponent = base_exponent + 2 * j + 1
      if integrated_exponent == 0:
        term = _scale_by_rational(Logarithm(substitution), coefficient)
      else:
        power = (substitution if integrated_exponent == 1 else
          Power(substitution, _rational_expression(integrated_exponent)))
        term = _scale_by_rational(power, coefficient / integrated_exponent)
      terms.append(term)
    primitive = terms[0] if terms else Number(0)
    for term in terms[1:]: primitive = Sum(primitive, term)
    return add_integration_constant(primitive, intg)


class TrigSquareBinomialIntegerPower(IntegrationStrategy):
  """Integrate (d+e*sin(u)^2)^N or cosine for nonnegative integer N."""
  description = "binomial expansion and even trigonometric-power reduction"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Power) or not exp.base.is_a(Sum): return None
    exponent = _rational_value(exp.exponent)
    if exponent == None or exponent.denominator != 1 or exponent < 0: return None
    constant = _rational_value(exp.base.a)
    trig_square = _rational_trig_square(exp.base.b)
    if constant == None or trig_square == None:
      constant = _rational_value(exp.base.b)
      trig_square = _rational_trig_square(exp.base.a)
    if constant == None or trig_square == None: return None
    coefficient, trig = trig_square
    phase = _laurent_polynomial_coefficients(trig.arg, intg.var)
    if phase == None or phase.get(1, Rational(0)) == 0: return None
    if any(degree < 0 or degree > 1 for degree in phase): return None
    return constant, coefficient, trig, int(exponent), phase[1]

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    constant, coefficient, trig, exponent, frequency = self._parts(intg)
    sine = TrigFunction('sin', trig.arg)
    cosine = TrigFunction('cos', trig.arg)

    def even_power_integral(n):
      if n == 0: return _scale_by_rational(trig.arg, Rational(1) / frequency)
      if trig.name == 'sin':
        sine_power = sine if n - 1 == 1 else Power(sine, Number(n - 1))
        leading = _scale_by_rational(Product(sine_power, cosine),
          Rational(-1, n) / frequency)
      else:
        cosine_power = cosine if n - 1 == 1 else Power(cosine, Number(n - 1))
        leading = _scale_by_rational(Product(sine, cosine_power),
          Rational(1, n) / frequency)
      return Sum(leading, _scale_by_rational(even_power_integral(n - 2),
        Rational(n - 1, n)))

    terms = []
    for k in range(exponent + 1):
      binomial_coefficient = (Rational(comb(exponent, k))
        * constant ** (exponent - k) * coefficient ** k)
      if binomial_coefficient != 0:
        terms.append(_scale_by_rational(even_power_integral(2 * k),
          binomial_coefficient))
    primitive = terms[0] if terms else Number(0)
    for term in terms[1:]: primitive = Sum(primitive, term)
    return add_integration_constant(primitive, intg)


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


class TangentIntegerPowerReduction(IntegrationStrategy):
  """Integrate tan(ax+b)^n for every nonnegative integer n."""
  description = "integer tangent-power reduction recurrence"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    phase = None
    exponent = None
    if exp.is_a(Power) and exp.base.is_a(TrigFunction) and exp.base.name == 'tan':
      phase, exponent = exp.base.arg, _rational_value(exp.exponent)
    elif exp.is_a(TrigFunction) and exp.name == 'tan':
      phase, exponent = exp.arg, Rational(1)
    elif exp.is_a(Fraction):
      if (exp.numr.is_a(Power) and exp.denr.is_a(Power)
        and exp.numr.base.is_a(TrigFunction) and exp.numr.base.name == 'sin'
        and exp.denr.base.is_a(TrigFunction) and exp.denr.base.name == 'cos'
        and exp.numr.base.arg == exp.denr.base.arg
        and exp.numr.exponent == exp.denr.exponent):
        phase, exponent = exp.numr.base.arg, _rational_value(exp.numr.exponent)
      elif (exp.numr == Number(1) and exp.denr.is_a(Power)
        and exp.denr.base.is_a(TrigFunction) and exp.denr.base.name == 'cot'):
        phase, exponent = exp.denr.base.arg, _rational_value(exp.denr.exponent)
    if (phase == None or exponent == None or exponent.denominator != 1
      or exponent < 0): return None
    phase_coefficients = _laurent_polynomial_coefficients(phase, intg.var)
    if phase_coefficients == None or phase_coefficients.get(1, Rational(0)) == 0:
      return None
    if any(degree < 0 or degree > 1 for degree in phase_coefficients): return None
    return phase, int(exponent), phase_coefficients[1]

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    phase, exponent, frequency = self._parts(intg)
    tangent = TrigFunction('tan', phase)
    terms = []
    sign = Rational(1)
    n = exponent
    while n >= 2:
      power = tangent if n - 1 == 1 else Power(tangent, Number(n - 1))
      terms.append(_scale_by_rational(power, sign / (frequency * (n - 1))))
      sign = -sign
      n -= 2
    if n == 0:
      terms.append(_scale_by_rational(phase, sign / frequency))
    else:
      terms.append(_scale_by_rational(Logarithm(TrigFunction('cos', phase)),
        -sign / frequency))
    primitive = terms[0]
    for term in terms[1:]: primitive = Sum(primitive, term)
    return add_integration_constant(primitive, intg)


class SecantIntegerPowerReduction(IntegrationStrategy):
  """Integrate sec(ax+b)^n for every nonnegative integer n."""
  description = "integer secant-power reduction recurrence"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if exp.is_a(Power) and exp.base.is_a(TrigFunction) and exp.base.name == 'sec':
      phase, exponent = exp.base.arg, _rational_value(exp.exponent)
    elif exp.is_a(TrigFunction) and exp.name == 'sec':
      phase, exponent = exp.arg, Rational(1)
    else: return None
    if exponent == None or exponent.denominator != 1 or exponent < 0: return None
    phase_coefficients = _laurent_polynomial_coefficients(phase, intg.var)
    if phase_coefficients == None or phase_coefficients.get(1, Rational(0)) == 0:
      return None
    if any(degree < 0 or degree > 1 for degree in phase_coefficients): return None
    return phase, int(exponent), phase_coefficients[1]

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    phase, exponent, frequency = self._parts(intg)
    secant = TrigFunction('sec', phase)
    tangent = TrigFunction('tan', phase)

    def reduce_power(n):
      if n == 0: return _scale_by_rational(phase, Rational(1) / frequency)
      if n == 1:
        return _scale_by_rational(Logarithm(Sum(secant, tangent)),
          Rational(1) / frequency)
      if n == 2: leading_power = Number(1)
      elif n == 3: leading_power = secant
      else: leading_power = Power(secant, Number(n - 2))
      leading = _scale_by_rational(Product(leading_power, tangent).simplified(),
        Rational(1, n - 1) / frequency)
      if n == 2: return leading
      return Sum(leading, _scale_by_rational(reduce_power(n - 2),
        Rational(n - 2, n - 1)))

    return add_integration_constant(reduce_power(exponent), intg)


class SecantArbitraryPowerHypergeometric(IntegrationStrategy):
  """Integrate sec(ax+b)^p for a symbolic constant exponent p."""
  description = "hypergeometric form for an arbitrary constant secant power"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Power) or not exp.base.is_a(TrigFunction)
      or exp.base.name != 'sec' or not is_constant(exp.exponent, intg.var)):
      return None
    if _rational_value(exp.exponent) != None: return None
    phase_coefficients = _laurent_polynomial_coefficients(exp.base.arg, intg.var)
    if phase_coefficients == None or phase_coefficients.get(1, Rational(0)) == 0:
      return None
    if any(degree < 0 or degree > 1 for degree in phase_coefficients): return None
    return exp.base.arg, exp.exponent, phase_coefficients[1]

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    phase, exponent, frequency = self._parts(intg)
    sine = TrigFunction('sin', phase)
    second_parameter = Fraction(Sum(exponent, Number(1)), Number(2))
    hypergeometric = Hypergeometric2F1(Fraction(Number(1), Number(2)),
      second_parameter, Fraction(Number(3), Number(2)), Power(sine, Number(2)))
    primitive = _scale_by_rational(Product(sine, hypergeometric),
      Rational(1) / frequency)
    return add_integration_constant(primitive, intg)


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


def _rational_exponential_term(expr):
  """Return (rational coefficient, phase) for c*exp(phase)."""
  if expr.is_a(TrigFunction) and expr.name == 'exp':
    return Rational(1), expr.arg
  if expr.is_a(Product):
    left = _rational_value(expr.a)
    if left != None:
      term = _rational_exponential_term(expr.b)
      if term != None: return left * term[0], term[1]
    right = _rational_value(expr.b)
    if right != None:
      term = _rational_exponential_term(expr.a)
      if term != None: return right * term[0], term[1]
  if expr.is_a(Fraction):
    denominator = _rational_value(expr.denr)
    if denominator != None and denominator != 0:
      term = _rational_exponential_term(expr.numr)
      if term != None: return term[0] / denominator, term[1]
  return None


def _polynomial_times_exponential(expr, var):
  """Return (polynomial coefficients, exponential) for P(x)*exp(phase)."""
  if expr.is_a(TrigFunction) and expr.name == 'exp':
    return {0: Rational(1)}, expr
  if not expr.is_a(Product): return None
  for polynomial_expr, exponential in [(expr.a, expr.b), (expr.b, expr.a)]:
    if exponential.is_a(TrigFunction) and exponential.name == 'exp':
      polynomial = _laurent_polynomial_coefficients(polynomial_expr, var)
      if polynomial != None and all(degree >= 0 for degree in polynomial):
        return polynomial, exponential
  return None


def _exponential_trig_product(expr):
  state = {'coefficient': Rational(1), 'exponential': None,
    'trig': None, 'valid': True}

  def collect(item):
    value = _rational_value(item)
    if value != None:
      state['coefficient'] *= value
    elif item.is_a(Product):
      collect(item.a)
      collect(item.b)
    elif item.is_a(TrigFunction) and item.name == 'exp' and state['exponential'] == None:
      state['exponential'] = item
    elif (item.is_a(TrigFunction) and item.name in ['sin', 'cos']
      and state['trig'] == None):
      state['trig'] = item
    else:
      state['valid'] = False

  collect(expr)
  if not state['valid'] or state['exponential'] == None or state['trig'] == None:
    return None
  return state['coefficient'], state['exponential'], state['trig']


class ExponentialTrigProduct(IntegrationStrategy):
  """Integrate c*exp(ax+b)*sin(mx+n) or cosine."""
  description = "general exponential-trigonometric product"

  @classmethod
  def _parts(self, intg):
    parts = _exponential_trig_product(intg.simplified().exp)
    if parts == None: return None
    coefficient, exponential, trig = parts
    exp_phase = _laurent_polynomial_coefficients(exponential.arg, intg.var)
    trig_phase = _laurent_polynomial_coefficients(trig.arg, intg.var)
    if exp_phase == None or trig_phase == None: return None
    if any(d < 0 or d > 1 for d in exp_phase) or any(d < 0 or d > 1 for d in trig_phase):
      return None
    a = exp_phase.get(1, Rational(0))
    m = trig_phase.get(1, Rational(0))
    if a == 0 or m == 0: return None
    return coefficient, exponential, trig, a, m

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    coefficient, exponential, trig, a, m = self._parts(intg)
    sine = TrigFunction('sin', trig.arg)
    cosine = TrigFunction('cos', trig.arg)
    if trig.name == 'cos':
      combination = Sum(_scale_by_rational(cosine, a),
        _scale_by_rational(sine, m))
    else:
      combination = Sum(_scale_by_rational(sine, a),
        _scale_by_rational(cosine, -m))
    primitive = _scale_by_rational(Product(exponential, combination),
      coefficient / (a * a + m * m))
    return add_integration_constant(primitive, intg)


class ExponentialOverLinearQuotientDerivative(IntegrationStrategy):
  """Recognize c*d/dx(exp(ax+b)/(m*x+n))."""
  description = "reverse quotient rule for an exponential over a linear function"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(Fraction) or not exp.denr.is_a(Power)
      or exp.denr.exponent != Number(2)):
      return None
    numerator = _polynomial_times_exponential(exp.numr, intg.var)
    linear = _laurent_polynomial_coefficients(exp.denr.base, intg.var)
    if numerator == None or linear == None: return None
    polynomial, exponential = numerator
    phase = _laurent_polynomial_coefficients(exponential.arg, intg.var)
    if phase == None or phase.get(1, Rational(0)) == 0: return None
    if any(d < 0 or d > 1 for d in phase) or any(d < 0 or d > 1 for d in linear):
      return None
    m = linear.get(1, Rational(0))
    if m == 0: return None
    n = linear.get(0, Rational(0))
    a = phase[1]
    expected = {1: a * m, 0: a * n - m}
    pivot = 1 if expected[1] != 0 else 0
    if expected[pivot] == 0: return None
    coefficient = polynomial.get(pivot, Rational(0)) / expected[pivot]
    degrees = set(polynomial.keys()) | set(expected.keys())
    if coefficient == 0 or not all(polynomial.get(d, Rational(0)) ==
      coefficient * expected.get(d, Rational(0)) for d in degrees):
      return None
    return exponential, exp.denr.base, coefficient

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    exponential, linear, coefficient = self._parts(intg)
    primitive = _scale_by_rational(Fraction(exponential, linear), coefficient)
    return add_integration_constant(primitive, intg)


class PolynomialDerivativeExponentialSubstitution(IntegrationStrategy):
  """Integrate c*Q'(x)*exp(Q(x)) for a rational polynomial Q."""
  description = "substitution u=Q(x) in a polynomial derivative times exp(Q(x))"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Product): return None
    for factor, exponential in [(exp.a, exp.b), (exp.b, exp.a)]:
      if not exponential.is_a(TrigFunction) or exponential.name != 'exp': continue
      base = _laurent_polynomial_coefficients(exponential.arg, intg.var)
      multiplier = _laurent_polynomial_coefficients(factor, intg.var)
      if base == None or multiplier == None or any(d < 0 for d in base): continue
      derivative = dict((degree - 1, Rational(degree) * coefficient)
        for degree, coefficient in base.items() if degree > 0 and coefficient != 0)
      if not derivative: continue
      pivot = max(derivative.keys())
      coefficient = multiplier.get(pivot, Rational(0)) / derivative[pivot]
      if coefficient == 0: continue
      degrees = set(derivative.keys()) | set(multiplier.keys())
      if all(multiplier.get(d, Rational(0)) == coefficient * derivative.get(d, Rational(0))
          for d in degrees):
        return exponential, coefficient
    return None

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    exponential, coefficient = self._parts(intg)
    return add_integration_constant(_scale_by_rational(exponential, coefficient), intg)


class ExponentialBinomialLogSubstitution(IntegrationStrategy):
  """Integrate c*exp(ax+b)*ln(d+e*exp(ax+b))."""
  description = "substitution u=d+e*exp(ax+b) followed by integration of ln(u)"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Product): return None
    for exponential_expr, logarithm in [(exp.a, exp.b), (exp.b, exp.a)]:
      exponential = _rational_exponential_term(exponential_expr)
      if exponential == None or not logarithm.is_a(Logarithm): continue
      binomial = _constant_plus_exponential(logarithm.arg)
      if binomial == None or binomial[2] != exponential[1]: continue
      phase = _laurent_polynomial_coefficients(exponential[1], intg.var)
      if phase == None or phase.get(1, Rational(0)) == 0: continue
      if any(degree < 0 or degree > 1 for degree in phase): continue
      return exponential[0], logarithm.arg, binomial[1], phase[1]
    return None

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    coefficient, base, exponential_coefficient, frequency = self._parts(intg)
    factor = coefficient / (exponential_coefficient * frequency)
    primitive = Sum(Product(base, Logarithm(base)), Product(Number(-1), base))
    return add_integration_constant(_scale_by_rational(primitive, factor), intg)


def _constant_plus_exponential(expr):
  """Return (constant, exponential coefficient, phase) for d+e*exp(phase)."""
  if not expr.is_a(Sum): return None
  constant = _rational_value(expr.a)
  exponential = _rational_exponential_term(expr.b)
  if constant == None or exponential == None:
    constant = _rational_value(expr.b)
    exponential = _rational_exponential_term(expr.a)
  if constant == None or exponential == None or exponential[0] == 0: return None
  return constant, exponential[0], exponential[1]


class ExponentialBinomialPowerSubstitution(IntegrationStrategy):
  """Integrate c*exp(ax+b)*(d+e*exp(ax+b))^p."""
  description = "substitution u=d+e*exp(ax+b)"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    numerator = None
    binomial_power = None
    if exp.is_a(Fraction):
      numerator = _rational_exponential_term(exp.numr)
      if exp.denr.is_a(Power):
        denominator_exponent = _rational_value(exp.denr.exponent)
        if denominator_exponent != None:
          binomial_power = (exp.denr.base, -denominator_exponent)
      else:
        binomial_power = (exp.denr, Rational(-1))
    elif exp.is_a(Product):
      numerator = _rational_exponential_term(exp.a)
      other = exp.b
      if numerator == None:
        numerator = _rational_exponential_term(exp.b)
        other = exp.a
      if other.is_a(Power):
        power = _rational_value(other.exponent)
        if power != None: binomial_power = (other.base, power)
      else:
        binomial_power = (other, Rational(1))
    if numerator == None or binomial_power == None: return None
    coefficient, numerator_phase = numerator
    base, exponent = binomial_power
    binomial = _constant_plus_exponential(base)
    if binomial == None or binomial[2] != numerator_phase: return None
    phase = _laurent_polynomial_coefficients(numerator_phase, intg.var)
    if phase == None or phase.get(1, Rational(0)) == 0: return None
    if any(degree < 0 or degree > 1 for degree in phase.keys()): return None
    return coefficient, base, exponent, binomial[1], phase[1]

  @classmethod
  def applicable(self, intg):
    return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    coefficient, base, exponent, exponential_coefficient, frequency = self._parts(intg)
    substitution_factor = coefficient / (frequency * exponential_coefficient)
    if exponent == -1:
      primitive = _scale_by_rational(Logarithm(base), substitution_factor)
    else:
      new_exponent = exponent + 1
      power = base if new_exponent == 1 else Power(base,
        _rational_expression(new_exponent))
      primitive = _scale_by_rational(power, substitution_factor / new_exponent)
    return add_integration_constant(primitive, intg)


class ExponentialQuadraticDenominatorSubstitution(IntegrationStrategy):
  """Integrate c*exp(u)/(d+e*exp(2u)) for affine u."""
  description = "substitution t=exp(ax+b) in a quadratic exponential denominator"

  @classmethod
  def _parts(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Fraction): return None
    numerator = _rational_exponential_term(exp.numr)
    denominator = _constant_plus_exponential(exp.denr)
    if numerator == None or denominator == None: return None
    d, e, denominator_phase = denominator
    coefficient, numerator_phase = numerator
    numerator_coefficients = _laurent_polynomial_coefficients(numerator_phase, intg.var)
    denominator_coefficients = _laurent_polynomial_coefficients(denominator_phase, intg.var)
    if numerator_coefficients == None or denominator_coefficients == None: return None
    degrees = set(numerator_coefficients.keys()) | set(denominator_coefficients.keys())
    if not all(denominator_coefficients.get(k, Rational(0)) ==
      Rational(2) * numerator_coefficients.get(k, Rational(0)) for k in degrees):
      return None
    frequency = numerator_coefficients.get(1, Rational(0))
    if frequency == 0 or d == 0 or e == 0: return None
    return coefficient, TrigFunction('exp', numerator_phase), d, e, frequency

  @classmethod
  def applicable(self, intg): return self._parts(intg) != None

  @classmethod
  def apply(self, intg):
    coefficient, exponential, d, e, frequency = self._parts(intg)
    if d * e > 0:
      sqrt_product = _rational_square_root_expression(abs(d * e))
      sqrt_ratio = _rational_square_root_expression(abs(e / d))
      argument = Product(sqrt_ratio, exponential).simplified()
      standard = Fraction(TrigFunction('arctan', argument), sqrt_product)
      sign = Rational(1) if d > 0 else Rational(-1)
    else:
      sqrt_d = _rational_square_root_expression(abs(d))
      sqrt_e = _rational_square_root_expression(abs(e))
      plus = Sum(sqrt_d, Product(sqrt_e, exponential))
      minus = Sum(sqrt_d, Product(Number(-1), Product(sqrt_e, exponential)))
      sqrt_product = _rational_square_root_expression(abs(d * e))
      standard = Fraction(Logarithm(Fraction(plus, minus)),
        Product(Number(2), sqrt_product))
      sign = Rational(1) if d > 0 else Rational(-1)
    primitive = _scale_by_rational(standard, sign * coefficient / frequency)
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
      '((%s ^ 2) / ((1 + (-1 * (%s ^ 2))) ^ (1 / 2)))' % (x, x),
      '(%s * ln(%s))' % (x, x),
      '(exp((2 * %s)) / (1 + exp(%s)))' % (x, x),
      '(1 / (%s * ((1 + (%s ^ 2)) ^ (1 / 2))))' % (x, x),
      '((sin(%s) ^ 2) * (cos(%s) ^ 4))' % (x, x),
      '(sin(%s) ^ 3)' % x,
      '(1 / ((%s ^ 2) + -1))' % x,
      '(1 / (1 + (-1 * (%s ^ 2))))' % x]
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

    elif key == '((%s ^ 2) / ((1 + (-1 * (%s ^ 2))) ^ (1 / 2)))' % (sx, sx):
      root = Power(Sum(Number(1), Product(Number(-1), Power(x, Number(2)))), half)
      primitive = Sum(Product(half, TrigFunction('asin', x)),
        Product(Fraction(Number(-1), Number(2)), Product(x, root)))

    elif key == '(%s * ln(%s))' % (sx, sx):
      x2 = Power(x, Number(2))
      primitive = Sum(Product(Fraction(x2, Number(2)), Logarithm(x)),
        Product(Fraction(Number(-1), Number(4)), x2))

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
  OneOverX, SimpleTrig, TrigSquare, TrigNonnegativeIntegerPowerReduction,
  TrigProduct, PolynomialSineCosineProduct,
  RationalPowerTimesExponentialPowerSubstitution,
  ExponentialFunction, ConstantBaseExponential,
  PolynomialDerivativeExponentialSubstitution,
  TrigBinomialPowerSubstitution, OddSineCosinePowerSubstitution,
  TrigSquareBinomialIntegerPower,
  SecSquaredRationalTangent, ReciprocalSecSquared,
  ExponentialOverLinearQuotientDerivative, CompositeSquareSubstitution,
  PolynomialTimesRationalPowerBinomialExpansion,
  ExponentialRationalSubstitution, ExponentialBinomialLogSubstitution,
  ReciprocalOnePlusOrMinusCosine, ReciprocalCosSquared,
  SineFourthCosineFourth, RationalEvenFourthProduct,
  ReciprocalXSquaredQuadraticSquareRoot,
  LinearOverQuadraticSquareRoot, MonicQuadraticParameterSquareRoot,
  QuadraticDerivativePowerSubstitution,
  PolynomialTimesAffinePowerSubstitution,
  AffineSquareRootTrigSubstitution,
  ArcTangentAffineSquareRoot,
  SquaredSineCosineCombination,
  TangentIntegerPowerReduction,
  SecantIntegerPowerReduction, SecantArbitraryPowerHypergeometric,
  TangentPowerSecantSquaredSubstitution,
  ExponentialTrigProduct,
  ExponentialBinomialPowerSubstitution,
  ExponentialQuadraticDenominatorSubstitution,
  LaurentPolynomialOverOnePlusSquare,
  ArcSinStandardForm, WinstonSlagleExample,
  ScreenshotExamples, VersionFiveExamples]
