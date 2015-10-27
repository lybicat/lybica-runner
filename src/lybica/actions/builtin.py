import logging

class InitParameter(object):
    ID = 0
    DESC = "Init CI primary action list."
    NAME = "init_primary_actions"
    DEPENDS = []
    CRITICAL = True

    def start_action(self, context):
        logging.debug("init primary actions......")

        # Here only primary actions be added,
        # Other action are selected in 'load_task' action with test category.
        # Task ID rule: 0 - 9 system reservation for primary actions;
        #              10-100 task define common actions, selected by 'load_task';
        #             101-200 crt actions, selected by 'load_task';
        #             501-600 sys task actions, selected by 'load_task';
        #             601-    custom task actions, selected by 'load_task';
        context.ACTION_LIST.extend(['init_context',
                                    'load_task',
                                    'sync_task_status',
                                    ])


class InitWorkspace(object):
    ID = 1
    ESC = 'Init task execution context.'
    NAME = 'init_context'
    DEPENDS = ["init_primary_actions", ]
    CRITICAL = True

    def start_action(self, context):
        pass

    def stop_action(self, context):
        pass


class TaskLoader(object):
    ID = 8
    DESC = "Load testing task information from Lybica Platform server."
    NAME = "load_task"
    DEPENDS = ["init_context", ]
    CRITICAL = True

    def start_action(self, context):
        logging.info('loading task from server.....')

    def stop_action(self, context):
        pass


class TaskStatusUpdater(object):
    ID = 9
    DESC = 'Sync task status to central server.'
    NAME = 'sync_task_status'
    DEPENDS = [] # TODO: depends on execution actions
    CRITICAL = True

    def start_action(self, context):
        # TODO: start task
        pass

    def stop_action(self, context):
        # TODO: stop task
        pass

