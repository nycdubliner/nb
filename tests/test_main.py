import unittest
from nb.main import main
import sys
from io import StringIO

class TestNB(unittest.TestCase):
    def test_import(self):
        try:
            from nb import generate_images
            self.assertTrue(callable(generate_images))
        except ImportError:
            self.fail("Could not import generate_images from nb")

    def test_cli_help(self):
        # Just ensure --help works and doesn't crash
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("sys.argv", ["nb", "--help"]):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 0)

from unittest.mock import patch

if __name__ == "__main__":
    unittest.main()
