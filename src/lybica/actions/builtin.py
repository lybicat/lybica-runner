import os
import logging
import zipstream
import requests


class InitPrimaryActions(object):
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
                                    'zip_archive',
                                    'load_task',
                                    'sync_task_status',
                                    ])


class InitWorkspace(object):
    ID = 1
    ESC = 'Init task execution context.'
    NAME = 'init_context'
    DEPENDS = ['init_primary_actions', ]
    CRITICAL = True

    def start_action(self, context):
        context.WORKSPACE = os.getenv('WORKSPACE', os.path.abspath('.'))
        logging.info('use WORKSPACE: ' + context.WORKSPACE)


class ZipArchiver(object):
    ID = 5
    ESC = 'archive workspace contents to remote storage.'
    NAME = 'zip_archive'
    DEPENDS = ['init_context', ]

    def start_action(self, context):
        self.rpc = context.rpc
        self.hdfs_view_url = os.getenv('LYBICA_HDFS_URL')
        if self.hdfs_view_url is None:
            raise RuntimeError('No "${LYBICA_HDFS_URL}" env variable defined!')
        logging.info('LYBICA HDFS URL: %s' % self.hdfs_view_url)

    def stop_action(self, context):
        logging.info('create zip stream from WORKSPACE: ' + context.WORKSPACE)
        stream = self._create_zip_stream(context.WORKSPACE)
        logging.info('post zip stream to HDFS')
        log_url = self._post_to_hdfs(stream)
        logging.info('update task log URL')
        self._update_task_logurl(context.TASK_ID, log_url)

    def _create_zip_stream(self, root_path):
        def file_iter(file_path):
            with open(file_path, 'rb') as fp:
                for line in fp:
                    yield line

        z = zipstream.ZipFile(mode='w')
        for root, _, files in os.walk(root_path):
            root = unicode(root, 'utf-8')
            dir_path = (root[len(root_path):].strip('/') + '/').lstrip('/')
            if dir_path != '':
                z.write(root, dir_path)
            for _f in files:
                _f = unicode(_f, 'utf-8')
                z.write_iter(iterable=file_iter(os.path.join(root, _f)), arcname=dir_path + _f)

        return z

    def _post_to_hdfs(self, stream):
        def data_iter():
            for chunk in stream:
                if chunk:
                    yield chunk
        response = requests.post(self.hdfs_view_url, data=data_iter())
        if response.status_code != 200:
            raise RuntimeError('failed to post data to hdfs, reason: "%s"' % response.reason)

        log_url = '/hdfs/%s!/' % response.headers['hdfsurl']
        logging.info('Log URL: %s' % log_url)

        return log_url

    def _update_task_logurl(self, task_id, log_url):
        getattr(self.rpc, 'task__' + task_id)(loglink=log_url)


class TaskLoader(object):
    ID = 8
    DESC = 'Load testing task information from Lybica Platform server.'
    NAME = 'load_task'
    DEPENDS = ['init_context', ]
    CRITICAL = True

    def start_action(self, context):
        self.rpc = context.rpc
        logging.info('loading task from server.....')
        task_id = os.getenv('TASK_ID')
        if task_id is None:
            raise RuntimeError('no TASK_ID defined')
        task = getattr(self.rpc, 'task__' + task_id)()
        context.TASK_ID = task_id
        context.BUILD_ID = task['build']
        context.CASE_SET = task['caseset']
        context.DEVICE_SET = task['device']
        context.ACTION_LIST.extend(task['actions'])
        logging.info('add actions: %s' % '; '.join(task['actions']))


class TaskStatusUpdater(object):
    ID = 9
    DESC = 'Sync task status to central server.'
    NAME = 'sync_task_status'
    DEPENDS = []
    CRITICAL = True

    def start_action(self, context):
        logging.info('start task %s' % context.TASK_ID)
        getattr(context.rpc, 'task__%s__start' % context.TASK_ID)(method='PUT')

    def stop_action(self, context):
        logging.info('done task %s' % context.TASK_ID)
        getattr(context.rpc, 'task__%s__done' % context.TASK_ID)(method='PUT')

