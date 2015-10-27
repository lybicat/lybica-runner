from .executor import ScriptExecutor
import logging

SCRIPT_CONFIG = [
    # health check script before install package
    {
     "name": 'install_package_pre_check',
     "search_path": ["${TESTCASE_PATH}/AreaCI/${PID}/install_package_pre_check",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/${PRODUCT}/${TEST_TYPE}/install_package_pre_check",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/${PRODUCT}/install_package_pre_check",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/install_package_pre_check",
                     "${BRANCH_ROOT}/PlatformCI/system/install_package_pre_check",],
     "failed_actions": ['action_pate_to_maintaining', 'stop_actions'],
     "success_actions": ['no_action', ],
    },
    # health check script after install package
    {
     "name": 'install_package_post_check',
     "search_path": ["${TESTCASE_PATH}/AreaCI/${PID}/install_package_post_check",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/${PRODUCT}/${TEST_TYPE}/install_package_post_check",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/${PRODUCT}/install_package_post_check",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/install_package_post_check",
                     "${BRANCH_ROOT}/PlatformCI/system/install_package_post_check", ],
     "failed_actions": ['action_pate_to_maintaining', 'stop_actions'],
     "success_actions": ['no_action', ],
    },
    {
     "name": 'health_check_before_crt',
     "search_path": ["${TESTCASE_PATH}/AreaCI/${PID}/health_check_before_crt",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/${PRODUCT}/${TEST_TYPE}/health_check_before_crt",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/${PRODUCT}/health_check_before_crt",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/health_check_before_crt",
                     "${BRANCH_ROOT}/PlatformCI/system/health_check_before_crt",
                     ],
     "failed_actions": ['action_pate_to_maintaining', 'stop_actions'],
     "expired_actions": ['action_pkg_to_expired', 'stop_actions'],
     "success_actions": ['no_action', ],
    },
    {
     "name": 'health_check_after_crt',
     "search_path": ["${TESTCASE_PATH}/AreaCI/${PID}/health_check_after_crt",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/${PRODUCT}/${TEST_TYPE}/health_check_after_crt",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/${PRODUCT}/health_check_after_crt",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/health_check_after_crt",
                     "${BRANCH_ROOT}/PlatformCI/system/health_check_after_crt",
                     ],
     "failed_actions": ['action_pate_to_maintaining_and_task_error' ],
     "expired_actions": ['action_pkg_to_expired', 'stop_actions'],
     "success_actions": ['no_action', ],
    },
    {
     "name": 'health_check_after_run_case',
     "search_path": ["${TESTCASE_PATH}/AreaCI/${PID}/health_check_after_run_case",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/${PRODUCT}/health_check_after_run_case",
                     "${BRANCH_ROOT}/PlatformCI/${PID}/health_check_after_run_case",
                     "${BRANCH_ROOT}/PlatformCI/system/health_check_after_run_case",
                     ],
     "failed_actions": ['no_action', ],
     "expired_actions": ['no_action', ],
     "success_actions": ['no_action', ],
    },
]

class ScriptWraper(object):
    def __init__(self, configed_scripts=[]):
        self.configed_scripts = []

    def run_script(self, context, name, param={}, check_in_config=True):
        if check_in_config and not name in self.configed_scripts:
            logging.info("The external scripts '%s' does not configured to run." % name)
            return
        if not hasattr(self, name):
            logging.info("The external scripts '%s' does not supported by ipaci." % name)
            return
        return getattr(self, name)(context, param)

def load_scripts():
    wrapper = ScriptWraper()

    for param in SCRIPT_CONFIG:
        name = param['name']
        setattr(wrapper, name, ScriptExecutor(param))

    return wrapper

