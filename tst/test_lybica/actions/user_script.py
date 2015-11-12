from unittest import TestCase
from lybica.actions.user_script import _UserScriptAction
from lybica.__main__ import Context
import os
import shutil


class TestUserScriptAction(TestCase):
    def setUp(self):
        super(TestUserScriptAction, self).setUp()
        self.context = Context()
        os.environ['WORKSPACE'] = './ut_logs'
        self.context.WORKSPACE = './ut_logs'
        os.makedirs(self.context.WORKSPACE)

    def tearDown(self):
        if os.path.exists(self.context.WORKSPACE):
            shutil.rmtree(self.context.WORKSPACE)

    def test_run_do_ut_action_under_case_root(self):
        os.environ['CASE_ROOT'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'testsuite'))
        class _Action(_UserScriptAction):
            def get_script_name(self):
                return 'do_ut'

        _Action()._run_script(self.context, {})

    def test_run_do_lybica_ut_action_under_lybica_directory(self):
        os.environ['CASE_ROOT'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'testsuite'))
        class _Action(_UserScriptAction):
            def get_script_name(self):
                return 'do_lybica_ut'

        _Action()._run_script(self.context, {})

    def test_run_do_undefined_action(self):
        os.environ['CASE_ROOT'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'testsuite'))
        class _Action(_UserScriptAction):
            def get_script_name(self):
                return 'do_undefined'

        self.assertRaises(RuntimeError, _Action()._run_script, self.context, {})
