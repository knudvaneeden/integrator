"""
Elements of expressions.

Expressions are composed of subclasses of the Expression class.

There are two basic expressions:
- Number
- Variable

There are a few binary composition expressions:
- Sum
- Product
- Fraction
- Power
- Logarithm
- Hypergeometric2F1

And finally there is the Integral expression which
represents an indefinite integral and contains
an expression to integrate and a variable to integrate
with respect to.

There is also VariableSet which is a hack that
tries to help make variables unique. It will
be gone soon.
"""

import string
from math import gcd

class Expression(object):
  """
  Expression is the base class for all types of elements of expressions.
  It cannot be instantiated.
  """
  def __init__(self):
    raise Exception("Expression is an abstract class")

  def reciprocal(self):
    return Fraction(Number(1), self)

  def simplified(self):
    return self

  def __eq__(self, other):
    """
    Test whether two expressions are equal.

    TODO Consider what this means.
         Are expressions equal that simplify to the same thing?
    """
    return self.__repr__() == other.__repr__()

  def __ne__(self, other):
    return not self.__eq__(other)

  def is_a(self, klass):
    """
    Utility method to clean up strategies.
    Used like this
    x = Number(1)
    x.is_a(Number) -> True
    """
    return isinstance(self, klass)

  def latex(self):
    """
    Convert an expression into its LaTeX representation
    for displaying.
    """
    raise Exception("latex not implemented for %s" % self)


class Number(Expression):
  """
  A basic element containg a single number.
  """
  def __init__(self, n):
    """
    Takes a single number `n` which is the value of this Number.
    """
    self.n = n

  def __repr__(self):
    return "{!r}".format(self.n)

  def latex(self):
    return "{!r}".format(self.n)


class VariableSet(object):
  """
  A unique set of variables.
  """
  SYMBOLS = set(string.ascii_letters)
  MAX_VARIABLES = len(SYMBOLS)

  def __init__(self):
    self.lookup = {} # hash of {Variable instance: symbol string}`

  # fetch or create a variable with symbol=symbol
  # if symbol=None then create a new variable
  def variable(self, symbol=None):
    if symbol == None:
      return self.new_variable()
    else:
      existing = self.variable_for(symbol)
      if existing != None:
        return existing
      else:
        return self.new_variable(symbol=symbol)

  # force creation of new variable
  # only one of symbol or suggest is allowed
  # if symbol then new variable will be created with symbol=symbol
  # if suggest then a new variable will be created, and if possible it will have symbol=suggest
  def new_variable(self, symbol=None, suggest=None):
    if symbol != None and suggest != None:
      return ValueError('only one of symbol and suggest is allowed, both supplied (symbol=%s, suggest=%s)' %(symbol, suggest))
    elif symbol != None:
      return self._new_variable(symbol)
    elif suggest != None:
      if self.variable_for(suggest) == None:
        return self._new_variable(suggest)
      else:
        return self._new_variable()
    else:
      return self._new_variable()

  # create a new variable with an unused symbol
  def _new_variable(self, symbol=None):
    if symbol != None:
      self._check_symbol_valid_new(symbol)
    else:
      symbol = self._unused_symbol()

    v = Variable(self)
    self.lookup[v] = symbol
    return v

  # throws ValueError on invalid symbol
  def _check_symbol_valid(self, symbol):
    if symbol == None:
      raise ValueError("symbol of None is not allowed")
    elif not symbol in self.SYMBOLS:
      raise ValueError("symbol '%s' not in SYMBOLS" % str(symbol) )

  # throws ValueError on invalid or used symbol
  def _check_symbol_valid_new(self, symbol):
    self._check_symbol_valid(symbol)
    if self.variable_for(symbol) != None:
      raise ValueError("symbol '%s' already used in VariableSet" % str(symbol) )

  def _unused_symbol(self):
    used = set([var_sym[1] for var_sym in list(self.lookup.items())])
    unused = self.SYMBOLS - used
    if len(unused) == 0:
      raise Exception("VariableSet out of symbols")
    # Stable ordering makes generated constants and test output reproducible
    # across Python versions and hash seeds.
    return sorted(unused)[0]

  def symbol_for(self, var):
    return self.lookup[var]

  # use self.lookup to backwards-lookup the Variable from the symbol
  # return None if no variables exist for symbol
  def variable_for(self, symbol):
    filtered = [var_sym1 for var_sym1 in list(self.lookup.items()) if var_sym1[1] == symbol]

    if len(filtered) == 0:
      return None
    elif len(filtered) == 1:
      return filtered[0][0]
    else:
      raise RuntimeError("more than one variable points to same symbol! (symbol=%s)" %symbol)


class Variable(Expression):
  """
  A variable.

  This class should not be instantiated.
  Creating a variable from a VariableSet is currently
  the preferred method of creating a new variable.
  This will change soon.
  Until then call variableset.variable(symbol=optional_symbol)
  """
  def __init__(self, vset):
    if not isinstance(vset, VariableSet):
      raise Exception('Variable instantiated without VariableSet')
    self.vset = vset

  # VariableSet uses Variable instances as dictionary keys.  Python 3 removes
  # the default hash when __eq__ is inherited, so retain identity hashing for
  # these internal keys.
  __hash__ = object.__hash__

  def symbol(self):
    """
    Get the symbol of the variable.
    For example, 'x'.
    """
    return self.vset.symbol_for(self)

  def __repr__(self):
    return "{0}".format(self.symbol())

  def latex(self):
    return "{0}".format(self.symbol())


class Sum(Expression):
  """
  An expression representing the sum of two sub-expressions.
  """
  def __init__(self, a, b):
    """
    a and b are the left and right operands of the sum 'a + b'.
    """
    self.a = a
    self.b = b

  def simplified(self):
    """
    Get the simplified form of the sum.
    """
    a = self.a.simplified()
    b = self.b.simplified()
    # If both operands are numbers, then sum their values.
    if a.is_a(Number) and b.is_a(Number):
      return Number(a.n + b.n)
    else:
      return Sum(a, b)

  def __repr__(self):
    return "(%s + %s)" %(self.a, self.b)

  def latex(self):
    return "(%s + %s)" %(self.a.latex(), self.b.latex())


class Product(Expression):
  """
  An expression representing the product of two sub-expressions.
  """
  def __init__(self, a, b):
    """
    a and b are the left and right operands of the sum 'a + b'.
    """
    self.a = a
    self.b = b

  def simplified(self):
    a = self.a.simplified()
    b = self.b.simplified()
    # If both operands are numbers, then multiply their values.
    if a.is_a(Number) and b.is_a(Number):
      return Number(a.n * b.n)
    else:
      return Product(a, b)

  def __repr__(self):
    return "(%s * %s)" %(self.a, self.b)

  def latex(self):
    return r"%s \cdot %s" %(self.a.latex(), self.b.latex())


class Fraction(Expression):
  """
  An expression representing a fraction.
  """
  def __init__(self, numr, denr):
    """
    Create the fraction (numr / denr).
    """
    self.numr = numr
    self.denr = denr

  def reciprocal(self):
    return Fraction(self.denr, self.numr)

  def simplified(self):
    numr = self.numr.simplified()
    denr = self.denr.simplified()

    if numr.is_a(Number) and denr.is_a(Number):
      this_gcd = gcd(numr.n, denr.n)
      numr = Number(numr.n // this_gcd)
      denr = Number(denr.n // this_gcd)

    if denr == Number(1):
      return numr
    else:
      return Fraction(numr, denr)

  def __repr__(self):
    return "(%s / %s)" %(self.numr, self.denr)

  def latex(self):
    return "\\frac{%s}{%s}" %(self.numr.latex(), self.denr.latex())


class Power(Expression):
  def __init__(self, base, exponent):
    """
    `base` to the power `exponent`.
    """
    self.base     = base
    self.exponent = exponent

  def simplified(self):
    base     = self.base.simplified()
    exponent = self.exponent.simplified()
    if base.is_a(Number) and exponent.is_a(Number):
      return Number(base.n ** exponent.n)
    else:
      return Power(base, exponent)

  def __repr__(self):
    return "(%s ^ %s)" %(self.base, self.exponent)

  def latex(self) :
    return "{%s}^{%s}" %(self.base.latex(), self.exponent.latex())


class Logarithm(Expression):
  def __init__(self, arg, base="euler"):
    """
    The logarithm base `base` of `arg`.
    """
    self.arg = arg
    self.base = base

  def simplified(self):
    return Logarithm(self.arg.simplified(), self.base)

  def __repr__(self):
    if self.base == "euler" :
      return "ln(%s)" %(self.arg)
    else :
      return "log(%s)" %(self.arg)

  def latex(self):
    if self.base == "euler" :
      return r"\ln{%s}" %(self.arg.latex())
    else :
      return r"\log_{%s}{%s}" %(self.base.latex(), self.arg.latex())


class Hypergeometric2F1(Expression):
  """Gauss hypergeometric function 2F1(a,b;c;z)."""
  def __init__(self, a, b, c, z):
    self.a = a
    self.b = b
    self.c = c
    self.z = z

  def simplified(self):
    return Hypergeometric2F1(self.a.simplified(), self.b.simplified(),
      self.c.simplified(), self.z.simplified())

  def __repr__(self):
    return "hypergeometric2F1(%s, %s, %s, %s)" % (self.a, self.b, self.c, self.z)

  def latex(self):
    return r"{}_2F_1\left(%s,%s;%s;%s\right)" % (
      self.a.latex(), self.b.latex(), self.c.latex(), self.z.latex())


class TrigFunction(Expression):
  """A trigonometric or inverse-trigonometric function."""
  NAMES = set(['sin', 'cos', 'tan', 'sec', 'csc', 'cot', 'asin',
    'acos', 'atan', 'acot', 'asec', 'acsc', 'arcsin', 'arccos',
    'arctan', 'arccot', 'arcsec', 'arccsc', 'exp'])

  def __init__(self, name, arg):
    if name not in self.NAMES:
      raise ValueError("unknown trigonometric function '%s'" % name)
    self.name = name
    self.arg = arg

  def simplified(self):
    return TrigFunction(self.name, self.arg.simplified())

  def __repr__(self):
    return "%s(%s)" % (self.name, self.arg)

  def latex(self):
    if self.name == 'asin':
      return "\\arcsin\\left(%s\\right)" % self.arg.latex()
    if self.name == 'atan':
      return "\\arctan\\left(%s\\right)" % self.arg.latex()
    if self.name in ['acos', 'acot', 'asec', 'acsc']:
      return "\\arc%s\\left(%s\\right)" % (self.name[1:], self.arg.latex())
    if self.name in ['arcsin', 'arccos', 'arctan', 'arccot', 'arcsec', 'arccsc']:
      return "\\%s\\left(%s\\right)" % (self.name, self.arg.latex())
    if self.name == 'exp':
      return "e^{%s}" % self.arg.latex()
    return "\\%s\\left(%s\\right)" % (self.name, self.arg.latex())


class Integral(Expression):
  """
  An expression represent a single integral.
  """
  def __init__(self, exp, var, include_constant=True):
    """
    The integral of `exp` with respect to the variable `var`.
    """
    self.exp = exp
    self.var = var
    self.include_constant = include_constant

  def simplified(self):
    return Integral(self.exp.simplified(), self.var.simplified(),
      self.include_constant)

  def __repr__(self):
    return "int[%s]d%s" %(self.exp, self.var)

  def latex(self):
    return r"\int{%s}\;d%s" %(self.exp.latex(), self.var.latex())
