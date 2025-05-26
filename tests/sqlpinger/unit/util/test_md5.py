from unittest import TestCase

from sqlpinger.util.md5 import calculate_md5


class TestMd5(TestCase):
    def test_calculate_md5(self):
        message = "123"
        hash = calculate_md5(message)
        self.assertEqual(hash, "202cb962ac59075b964b07152d234b70")
