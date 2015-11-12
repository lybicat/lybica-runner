from lybica.utils import execute_command
from unittest import TestCase


class TestExecuteCommand(TestCase):
    def test_execute_date_command(self):
        execute_command('date')

    def test_execute_ping_c_3_command(self):
        execute_command('ping', '-c', '3', '127.0.0.1')

    def test_execute_ping_invalid_command(self):
        self.assertRaises(RuntimeError, execute_command, 'ping', 'invalid')
