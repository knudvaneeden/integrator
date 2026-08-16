Solved:

    int x dx
    int x^2 dx
    int x * ( x + 1 ) dx
    int x + x^2 dx
    int 2 + cos( x ) dx
    int sin( x )^2 * cos( x ) dx
    int sin( x )^4 * cos( x )^4 dx
    int sin( x )^4 / cos( x )^4 dx
    int 1 / cot( x )^4 dx
    int 32 * x^4 / ( ( 1 + x^2 ) * ( 1 - x^2 ) )^4 dx
    int x^4 / ( 1 + x^2 ) dx
    int ( 1 / x^4 / ( 1 + x^2 ) ) dx
    int x * sqrt( x^2 + 16 ) dx
    int cos( sqrt( x ) ) dx
    int ( sin( x ) + cos( x ) )^2 dx
    int tan( x ) * sec( x )^2 dx
    int sin( x ) + cos( x ) dx
    int x * sqrt( 1 + x ) dx
    int ( x^2 + 1 ) / sqrt( x ) dx
    int ( 3 * x^7 - 2 * x^3 + 5 ) / ( 1 + x^2 ) dx
    int sec(x)^2 / ( 1 + sec( x )^2 - 3 * tan( x ) ) dx
    int 1 / sec( x )^2 dx
    int x / sqrt( x^2 + 2 * x + 5 ) dx
    int ( x^2 + x ) / sqrt( x ) dx
    int ( x + 1 ) / sqrt( 2 * x - x^2 ) dx
    int x * ( x^(1/2) + x^(-1/2) )^2 dx
    int exp( 6 * x ) / ( exp( 4 * x ) + 1 ) dx
    int exp( 2 * x ) * ln( 1 + exp( 2 * x ) ) dx
    int 1 / ( 1 + cos( x ) ) dx
    int 1 / cos( x )^2 dx
    int x * exp( x ) / ( 1 + x )^2 dx
    int (arcsin(x) + sin(x))^2 * ((1 - x^2)^(-1/2) + cos(x)) dx
    int cos( 3 * x ) / ( 1 - sin( 3 * x ))^2 dx
    int x^4 / ( 1 - x^2 )^( 5 / 2 ) dx
    int tan(x)^5 * sec(x)^2 dx
    int 1 / (1 + x^4)^2 dx
    int x^2 / sqrt( 1 - x^2 ) dx
    int x * ln( x ) dx
    int tan( x )^5 sec( x )^2 dx
    int exp(2*x) / ( 1 + exp(x) ) dx
    int 1 / ( x * sqrt( 1 + x^2 ) ) dx
    int sin( x )^2 * cos( x )^4 dx
    int c^x dx
    int x^n dx
    int 1/x dx
    int exp( x ) dx
    int sin( x ) dx
    int cos( x ) dx
    int sec( x )^2 dx
    int csc( x )^2 dx
    int 1 / ( 1 + x^2 ) dx
    int 1 / ( 1 - x^2 ) dx
    int cos( x ) / ( 1 + sin( x ) )^2 dx
    int x exp(x)^2 dx
    int x exp(x^2) dx
    int ln( x ) dx
    int log( x ) dx
    int arcsin( x ) dx
    int arccos( x ) dx
    int arctan( x ) dx
    int arccot( x ) dx
    int arcsec( x ) dx
    int arccsc( x ) dx
    int x^c dx
    int sec( x ) * tan( x ) dx
    int csc( x ) * cot( x ) dx
    int sin( m * x ) * cos( n * x ) dx
    int sin( m * x ) * sin( n * x ) dx
    int cos( m * x ) * cos( n * x ) dx
    int x / ( x^2 + x ) dx

===

Not solved:

    None of the examples listed above.

# Author

This program was originally developed by Miles Steele. It solved only the
integral of powers of the variable x initially. It has now been extended
(solely by involving ChatGPT, which supplied all the changes) to correspond
more closely to the original examples solvable by the SAINT program written
by James Robert Slagle (for example, trigonometric functions can be
integrated).

# Original LISP source of SAINT by James Robert Slagle

This LISP 1.5 source code (running on an IBM 7090 mainframe computer with a
total of 32 kilobytes of memory available) has been lost and has not been
found anywhere on the Internet.

# You can see a very good explanation of the working of SAINT

Professor Patrick Winston explains it in his MIT Artificial Intelligence
Lecture 2:

https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/resources/lecture-2-reasoning-goal-trees-and-problem-solving/

# Prerequisites

Use Python 3.8 or newer. Python 3.11 and later are recommended.

https://www.python.org/downloads/

Install the web dependency from the project directory:

    python -m pip install -r requirements.txt

Then start the web interface:

    python web.py

Open http://127.0.0.1:5000/ in a browser. The bundled MathJax files allow
LaTeX rendering without an Internet connection.

# AND-OR solution graph

Every integral submitted through the web interface also creates an AND-OR
solution graph. OR nodes show integration-rule selection, while AND nodes
show subexpressions that must all be solved. Use the **Print / Save as PDF**
button above the graph to print it or save it as a PDF from the browser.

# Integrator
This is a symbolic integrator based on James Slagle's 1961 thesis.
The goal of this project is to solve integrals symbolically
in an accessible manner.
The machine will work to solve the integration problem, and will share its
thoughts and methods with you.

## Demo
You can try the integrator for yourself [here](http://milessteele.com:5000).

## Getting Your Hands Dirty

After playing with the integrator, you might
be inclined to change some of the ways in which it operates.

Running the integrator locally will enable you to mess
with the code and change how it works.
You can experiment with different ways
of presenting how it does the integration,
or try adding your own strategies to make it smarter,
or anything you can think of.

To get more ideas about what to fiddle with, 
you may want to read the _Parts of the Machine_
section below to get a sense for how the pieces
of the integrator fit together and decide
which one to tackle first.

Here are a few instructions to get you started
running the integrator locally.

### Installing Requirements
Before running the integrator, you will need a few things
set up first.

- __git__ will enable you to track changes that you make
  and submit pull requests to add features for everyone to see.
  This is optional, you could just download a
  zip to get started quickly.
- __python__ comes already installed on many computers, you will
  need this to run the integration engine and webserver.
- __flask__ is a web framework for python which serves
  the web interface. You can install it via
  [pip](http://pip.readthedocs.org/en/latest/installing.html)
  using
  [these instructions](http://flask.pocoo.org/)

### Running
After you have downloaded the `integrator` directory
somewhere go ahead and open up a terminal and
`cd` into the directory:

    $ cd /where/did/you/put/the/integrator

Then install the dependency and run:

    $ python -m pip install -r requirements.txt
    $ python web.py

If all goes well, you should now see something like:

     * Running on http://127.0.0.1:5000/
     * Restarting with reloader

Great, you've started the integrator web server
on your computer on port 5000.
Visit [http://localhost:5000](http://localhost:5000)
to see the web interface to your local copy of the integrator.

You can now start editing the code, be sure to refresh
the web page to see your changes take effect.

## Parts of the Machine

### Web Front-End
This is the part of the program that you see when you visit
the website.

It is a simple web page which asks the python server
to solve integration problems for you and then displays
the results.

The html is in
`templates/solver.html`
and the javascript that talks to the server is in
`static/js/solver.js`.

### Web Server
The web server receives requests to solve expressions from
the web page and passes them on to the underlying layers
of the program before passing the result back to the web page.

### Parser
The web server sends input from the web interface to the parser
which lives in `parseintg.py`.

Right now, the parser is a horrible tangled mess, so it
would probably be best at this point to think of it as a black
box which converts text like `int x + 1 dx` into a
tree of expressions representing that expression.

That particular example, `int x + 1 dx`,
would be converted into something like:

    Integral(
      Sum(
        Variable("x"), Number(1)
      ),
      Variable("x"))

### Elements
The parser parses the input string into elements
like `Number`, `Sum`, `Product`, and `Integral`.
These types of expressions are implemented in `elements.py`.

Each type of expressions is a kind of `Expression`
which is a class that knows how to simplify itself a bit.

### Solver
The elements forming the expression to be solved
are then passed on to `solver.py` which does
the meat of the integration.

The solver is responsible for coralling expressions
into their simplified form, and then trying integration
strategies to solve the integrals in the expression.

You can run the solver by itself from the command line.
But the output is not very pretty as it is meant for the web.

    $ python solver.py
    Enter a string to be integrated.
    Just press enter to integrate 'int 3 x / 4 dx'
    -> 
    I will attempt to solve \( \int{\frac{3 \cdot x}{4}}\;dx \).
    \( \int{\frac{3 \cdot x}{4}}\;dx \) is an integral.
    Which of my strategies are applicable to this integral?
    The "integral with a constant divisor" rule <div class="strategy-icon"><div class="strategy-code"><pre>class ConstantDivisor(IntegrationStrategy):<br>  description = "integral with a constant divisor"<br><br>  @classmethod<br>  def applicable(self, intg):<br>    exp = intg.simplified().exp<br>    return (exp.is_a(Fraction)<br>      and (is_constant(exp.denr, intg.var)))<br><br>  @classmethod<br>  def apply(self, intg):<br>    exp = intg.simplified().exp<br>    return Product(Fraction(Number(1), exp.denr), Integral(exp.numr, intg.var))<br></pre></div></div> is applicable, I will try it.
    I will attempt to solve \( \frac{1}{4} \cdot \int{3 \cdot x}\;dx \).
    \( \frac{1}{4} \cdot \int{3 \cdot x}\;dx \) is a product. I will solve the two sub-problems and then multiply the results.
    [<sublogger.SubLogger object at 0x7f3ff3543490>, <sublogger.SubLogger object at 0x7f3ff3543510>]
    I will multiply the results of the sub-problems back together to get \( \frac{1}{4} \cdot 3 \cdot (\frac{1}{2} \cdot {x}^{2} + C) \).


### Strategies
All of the strategies that the solver knows how to
try are in `strategies.py`

Here is an example of a strategy.
This strategy takes a sum inside of an integral
and ouputs a new equivalent expression which
is the sum of two integrals.

```python
# int x + x^2 dx = int x dx + int x^2 dx
class DistributeAddition(IntegrationStrategy):
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
```

Applying these strategies as they become applicable
will solve a surprising number of integrals.

## Trigonometric functions

This version also recognizes `sin`, `cos`, `tan`, `sec`, `csc`, and `cot`.
Function arguments must be parenthesized. It integrates the six basic
functions when their argument is linear in the integration variable, as well
as `sec(u)^2`, `csc(u)^2`, `sec(u)*tan(u)`, and `csc(u)*cot(u)`.

Examples:

    int sin(x) dx
    int cos(3*x+2) dx
    int sec(2*x)^2 dx
    int csc(4*x)*cot(4*x) dx

The worked Slagle example discussed by Patrick Winston in MIT 6.034 Lecture 2
is also supported:

    int x^4/(1-x^2)^(5/2) dx

The parser also accepts `sqrt(x)`, `exp(x)`, `log(x)`/`ln(x)`, `asin(x)`,
and `atan(x)`.  The regression suite includes every distinct integral in
the user-supplied SAINT screenshots, including the two examples labelled
as failures there. Historical provenance is kept separate: those labels
do not agree with the two failures printed on page 72 of Slagle's thesis.
