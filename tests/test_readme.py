import unittest
from pathlib import Path

from parseintg import parse


class TestReadmeExamples(unittest.TestCase):
  ADDED_VERSION_58 = [
    'int sqrt( 5 * x + 4 ) dx',
    'int sin( x )^2 * cos( x ) dx',
    'int 4 - x^2 dx',
    'int 2 * x^2 - x^3 dx',
    'int 1 / x^2 - 1 / x^3 dx',
    'int 1 / x^(1/2) dx',
    'int 2 + x dx',
    'int 2 - x^2 dx',
    'int 3 - 2 * x + x^2 dx',
    'int x * ( 1 - x^2 ) dx',
    'int x * ( 1 - x ) * sqrt( x ) dx',
    'int sqrt( 1 + 3 * x ) dx',
    'int x^2 * ( x^3 + 1 ) dx',
    'int 1 / sqrt( 1 + x ) dx',
    'int x / sqrt( x^2 - 15 ) dx',
    'int x * ( 1 - sqrt( x ) )^2 dx']

  ADDED_VERSION_59 = [
    'int sqrt( x ) * exp( sqrt( x ) ) dx']

  ADDED_VERSION_67 = [
    'int 1 / ( x^2 * sqrt( x^2 + 4 ) ) dx']

  ADDED_VERSION_68 = [
    'int arctan( sqrt( x ) ) dx']

  ADDED_VERSION_69 = [
    'int cos( x )^4 dx']

  def _solved_examples(self):
    readme = Path(__file__).resolve().parents[1] / 'README.md'
    lines = readme.read_text().splitlines()
    start = lines.index('Solved:') + 1
    end = lines.index('===', start)
    return [line.strip() for line in lines[start:end] if line.strip()]

  def test_solved_examples_are_semantically_unique(self):
    examples = self._solved_examples()

    first_example_by_expression = {}
    duplicates = []
    for example in examples:
      expression = repr(parse(example).simplified())
      if expression in first_example_by_expression:
        duplicates.append((first_example_by_expression[expression], example))
      else:
        first_example_by_expression[expression] = example

    self.assertEqual(duplicates, [])

  def test_new_examples_are_the_final_readme_entries(self):
    examples = self._solved_examples()
    added = (self.ADDED_VERSION_58 + self.ADDED_VERSION_59
      + self.ADDED_VERSION_67 + self.ADDED_VERSION_68 + self.ADDED_VERSION_69)
    self.assertEqual(examples[-len(added):], added)


if __name__ == '__main__':
  unittest.main()
