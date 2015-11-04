import os
import shutil
from unittest import TestCase
from lybica.actions.robotframework import RepeatRunningWrapper
from lybica.__main__ import Context


class TestRepeatRunningWrapper(TestCase):
    def setUp(self):
        super(TestRepeatRunningWrapper, self).setUp()
        self.context = Context()
        self.context.WORKSPACE = './ut_logs'
        self.context.CASE_ROOT = 'tst/testsuite'
        self.action = RepeatRunningWrapper()

    def tearDown(self):
        if os.path.exists(self.context.WORKSPACE):
            shutil.rmtree(self.context.WORKSPACE)

    def test_run_test_5_times(self):
        self.action._run_test(5, self.context.CASE_ROOT, self.context.WORKSPACE)
        self.assertEqual(len(os.listdir(self.context.WORKSPACE)), 5)

