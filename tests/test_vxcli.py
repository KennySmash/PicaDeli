import unittest
from pathlib import Path

from cli.vxcli import validate_path


class TestVxcliValidate(unittest.TestCase):
    def test_validate_example_vxdoc(self):
        example = Path("examples/basic.vxdoc")
        self.assertTrue(validate_path(example))


if __name__ == "__main__":
    unittest.main()

