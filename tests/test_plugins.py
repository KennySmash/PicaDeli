import unittest

from plugins.examples.blur_plus import plugin as blur
from plugins.vx.registry import get_registry


class TestPluginRegistry(unittest.TestCase):
    def test_register_and_list(self):
        reg = get_registry()
        # Ensure idempotent within test process by catching duplicate
        try:
            blur.register_plugin()
        except Exception:
            pass
        nodes = [p.name for p in reg.list(type="node")]
        self.assertIn("blur_plus", nodes)


if __name__ == "__main__":
    unittest.main()

