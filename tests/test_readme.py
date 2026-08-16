import unittest
from pathlib import Path

from parseintg import parse


class TestReadmeExamples(unittest.TestCase):
  def test_solved_examples_are_semantically_unique(self):
    readme = Path(__file__).resolve().parents[1] / 'README.md'
    lines = readme.read_text().splitlines()
    start = lines.index('Solved:') + 1
    end = lines.index('===', start)
    examples = [line.strip() for line in lines[start:end] if line.strip()]

    first_example_by_expression = {}
    duplicates = []
    for example in examples:
      expression = repr(parse(example).simplified())
      if expression in first_example_by_expression:
        duplicates.append((first_example_by_expression[expression], example))
      else:
        first_example_by_expression[expression] = example

    self.assertEqual(duplicates, [])


if __name__ == '__main__':
  unittest.main()
