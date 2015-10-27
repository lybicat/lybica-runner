import os
import subprocess
import logging
import re
import sys

MESSAGE_TO_TAGS = {'Suite setup failed:':'not-run',
                   'Setup failed:':'not-run',
                   'Setup of the parent suite failed':'not-run',
                   'Testbed failure':'non-critical',
                   'Testbed failure':'not-run',
                  }


class ScriptExecutor(object):
    '''
    config => {
        "search_path": ["${TESTCASE}/${CATEGORY}", "${TESTCASE}/${PID}/${CATEGORY}" ],
        "failed_actions": ['set_device_to_maintainence', ],
        "success_actions": ['no_action', ],
        "name": 'pate_health_check'
    }
    '''
    def __init__(self, config):
        self.config = config

    def run_script(self, context, param):
        logging.info('start to run "%s" script, param:%s.' % (self.config.get('name'), str(param)))
        script_cmd = self._search_script(context)

        if not script_cmd:
            logging.info('not found "%s" script.' % self.config.get('name'))
            return
        _, script_ext = os.path.splitext(script_cmd)
        if script_ext in ('.robot', '.html', '.tsv', '.txt'):
            script_cmd = self._wraper_pybot_script(context, script_cmd, param)
        elif script_ext in ('.py', ):
            script_cmd = self._wraper_python_script(context, script_cmd, param)
        elif script_cmd in ('.sh', ):
            # set env variables
            for k, v in param.iteritems():
                logging.info('#param: %s -> %s' % (k, v))
                os.environ[str(k)] = str(v)

        logging.info('starting %s' % script_cmd)
        cwd = os.getenv('WORKSPACE', '.')
        logging.info('#script_cmd:%s' % script_cmd)
        err_code = subprocess.call(script_cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr, cwd=cwd)
        logging.info('error code:%s' % err_code)

        if err_code == 0:
            self._success_actions(context)
        else:
            self._failed_actions(context)

        return err_code

    def __call__(self, context, param):
        return self.run_script(context, param)

    def _search_script(self, context):
        supported_types = ('.htm', '.html', '.robot', '.txt', '.tsv', '.py', '.sh')
        for path in self.config.get('search_path', []):
            logging.info('check script pattern:%s' % path)
            new_path = re.sub(r'\$\{([\w_]+)\}', lambda x:os.getenv(x.group(1), ''), path)
            for _ext in supported_types:
                if os.path.isfile(new_path + _ext):
                    new_path = new_path + _ext
                    break

            if os.path.isfile(new_path):
                logging.info('find script "%s"' % new_path)
                return new_path

            logging.info('not find script "%s.(htm|html|robot|tsv|py|txt|sh)"' % new_path)

        return None

    def _wraper_pybot_script(self, context, file_path, param):
        name, ext = os.path.splitext(os.path.basename(file_path))
        from datetime import datetime
        time_stamp = datetime.now().strftime("%H%M%S")

        if not os.path.exists(context.OUTPUT_LOG):
            os.makedirs(context.OUTPUT_LOG)
        variable_file = '%s/variablefile_%s_%s.py' % (context.OUTPUT_LOG, name.replace('.', '_'), time_stamp)
        with open(variable_file, 'w') as vf:
            for k, v in param.iteritems():
                vf.write("%s='%s'\n" % (k, v))
        robot_settings = ['--variablefile', variable_file,
                          '--monitorcolors', 'off',
                          '--exclude', 'not-ready',
                          '--loglevel', 'TRACE',
                          '--outputdir', context.OUTPUT_LOG,
                          '--output', '%s_%s.xml' % (name, time_stamp),
                          '--log', '%s_%s.html' % (name, time_stamp),
                          '--report', 'none',
                        ]

        # robot_settings.extend(['--listener', 'rdb.Listener', file_path])
        robot_settings = '" "'.join(robot_settings)

        return 'pybot "%s"' % robot_settings

    def _wraper_python_script(self, context, script_cmd, param):
        return 'python "%s"' % script_cmd

    def _failed_actions(self, context):
        for action in self.config.get('failed_actions', []):
            getattr(self, action)(context)

    def _success_actions(self, context):
        for action in self.config.get('success_actions', []):
            getattr(self, action)(context)

    def stop_actions(self, context):
        logging.info('cleanup all actions')
        context.clean_action()

    def no_action(self, context):
        logging.info('no actions')

