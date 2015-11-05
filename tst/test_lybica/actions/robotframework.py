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
        if not os.path.exists(self.context.WORKSPACE):
            os.makedirs(self.context.WORKSPACE)
        self.action = RepeatRunningWrapper()

    def tearDown(self):
        if os.path.exists(self.context.WORKSPACE):
            shutil.rmtree(self.context.WORKSPACE)

    def test_run_test_5_times(self):
        self.action._run_test(5, self.context.CASE_ROOT, self.context.WORKSPACE)
        self.assertEqual(len(os.listdir(self.context.WORKSPACE)), 5)

    def test_combine_2_records_together(self):
        from robot.api import ExecutionResult
        shutil.copy('tst/testdata/output-round-1.xml', self.context.WORKSPACE)
        shutil.copy('tst/testdata/output-round-2.xml', self.context.WORKSPACE)
        self.action._combine_output(self.context.WORKSPACE, 'output.xml')
        result = ExecutionResult(os.path.join(self.context.WORKSPACE, 'output.xml'))
        self.assertEqual(result.statistics.total.all.total, 6)

    def test_get_test_summary(self):
        summary = self.action._get_test_summary('tst/testdata/output.xml')
        self.assertEqual(summary['passed'], True)
        self.assertEqual(summary['total']['total'], 6)
        self.assertEqual(summary['total']['passed'], 6)
        self.assertEqual(summary['total']['failed'], 0)
        self.assertEqual(len(summary['tests']), 6)

