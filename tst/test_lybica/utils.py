from lybica.utils import execute_command
from unittest import TestCase


class TestExecuteCommand(TestCase):
    def test_execute_date_command(self):
        self.assertEqual(execute_command('date'), 0)

    def test_execute_ping_c_3_command(self):
        self.assertEqual(execute_command('ping', '-c', '3', '127.0.0.1'), 0)

    def test_execute_ping_invalid_command(self):
        self.assertNotEqual(execute_command('ping', 'invalid'), 0)
