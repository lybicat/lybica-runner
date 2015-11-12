''' define some user script execution actions '''
import logging
from lybica.executor import ScriptExecutor


class _UserScriptAction(object):
    ''' common user script action '''
    def __init__(self):
        self.action_name = self.get_script_name()

    def get_script_name(self):
        raise RuntimeError('not implemented')

    def start_action(self, context):
        self._run_script(context, context.VARIABLES or {})

    def _run_script(self, context, param):
        logging.info('execute action "%s"' % self.action_name)
        executor = ScriptExecutor({
            'name': 'install_build',
            'search_path': ['${CASE_ROOT}/'+ self.action_name,
                            '${CASE_ROOT}/lybica/'+ self.action_name,
                            '/usr/local/bin/'+ self.action_name,
                            '/opt/bin/' + self.action_name
                            ],
            'failed_actions': ['no_action', ],
            'success_actions': ['no_action', ],
            })

        error_code = executor(context, param)
        if error_code != 0 :
            raise RuntimeError('failed to execute script "%s"' % self.action_name)

        return error_code


class InstallBuild(_UserScriptAction):
    ID = 51
    DESC = 'Install Software Build'
    NAME = 'install_build'
    DEPENDS = []
    CRITICAL = True

    def get_script_name(self):
        return 'install_build'


