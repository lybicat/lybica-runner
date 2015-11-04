'''
It's a framework to running testing. All the actions are loading as plugins.

name-
id-
desc-
'''
import sys
import logging
import types
import re
import os
import inspect

class Context(object):
    def __init__(self):
        #current running action names
        self.DONE_ACTIONS = []
        #enable action list
        self.ACTION_LIST = []
        #current action ID
        self.CURRENT_ID = None
        #the error code at process done.
        self.ERR_CODE = 0

        self.namespaces = NameSpaces()

    def clean_action(self):
        self.ACTION_LIST = []

    def parse_value(self, name, def_val=None):
        if name == 'context': return self
        if hasattr(self, name):
            return getattr(self, name) or def_val
        else:
            return self.namespaces.parse_value(name, def_val)

    def update_context(self, data):
        self.namespaces.update(data)

    def __str__(self):
        return '#context@%s' % self.CURRENT_ID

class NameSpaces(dict):
    _extended_var_re = re.compile(r'''
    ^(\w+?)        # base name (group 1)
    ([^\s\w].+)  # extended part (group 2)
    $''', re.VERBOSE)

    _var_re = re.compile(r'''
    ^(\w+?)$        # base name (group 1)
    ''', re.VERBOSE)

    def parse_value(self, name, def_val=None):
        if self._var_re.match(name):
            return self.get_val(name, def_val)
        if self._extended_var_re.match(name):
            base, expression = self._extended_var_re.search(name).groups()
            variable = self.get_val(base)
            try:
                return eval('_BASE_VAR_' + expression, {'_BASE_VAR_': variable})
            except Exception, e:
                logging.error('error:%s, variable:%s' % (e, str(variable)))
                raise
        else:
            return def_val

    def get_val(self, name, def_val=None):
        if name in self:
            return self.get(name)
        else:
            return os.getenv(name, def_val)

class Action(object):
    ERR_IGNORE = 1 # ignore remaining action, start to execution stop_action
    ERR_EXIT = 2   # exit the process immediately
    ERR_IGNORE_ONE = 3 # ignore current action, all actions be depended can not start.

    def __init__(self, obj):
        self._handler = obj
        self.id = obj.ID
        self.desc = ''
        self.name = obj.__class__.__name__
        if hasattr(obj, 'NAME'):
            self.name = obj.NAME
        if hasattr(obj, 'DESC'):
            self.desc = obj.DESC
        self.depends = []
        if hasattr(obj, 'DEPENDS'):
            self.depends = obj.DEPENDS
        self.critical = True
        if hasattr(obj, 'CRITICAL'):
            self.critical = obj.CRITICAL

    def start_action(self, context):
        if not hasattr(self._handler, 'start_action'):return
        try:
            #self._handler.start_action(context)
            self._run_fun(self._handler.start_action, context)
        except Exception, e:
            logging.exception(e)
            if 'ERR_EXIT' in str(e): return self.ERR_EXIT
            return self.ERR_IGNORE

    def stop_action(self, context):
        if not hasattr(self._handler, 'stop_action'):return
        try:
            self._run_fun(self._handler.stop_action, context)
        except Exception, e:
            logging.exception(e)
            if 'ERR_IGNORE' in str(e): return self.ERR_IGNORE
            if 'ERR_EXIT' in str(e): return self.ERR_EXIT

    def _run_fun(self, func, context):
        args, kws, kw_names = self._get_func_args(func)
        args_val, kws_vals = self._parse_args_values(context, args, kws)

        message = [ '%s=%s' % (args[i], args_val[i]) for i in range(len(args)) ]
        message += [ '%s=%s' % (k, kws_vals[k]) for k in kw_names ]
        logging.debug('[ARGS] %s' % ','.join(message))

        data = func(*args_val, **kws_vals)

        if data and isinstance(data, dict):
            context.update_context(data)

    def _get_func_args(self, func):
        spec = inspect.getargspec(func)

        args_len = len(spec.args)
        kws_len = spec.defaults and len(spec.defaults) or 0

        args = spec.args[: args_len - kws_len]
        kw_names = spec.args[args_len - kws_len: ]
        kws = dict(((kw_names[i], spec.defaults[i]) for i in range(kws_len)))
        if args_len > 0 and args[0] == 'self':
            args = args[1:]

        return args, kws, kw_names

    def _parse_args_values(self, context, args, kws):
        args_val = [ context.parse_value(e, None) for e in args ]
        kws_val = {}

        for name, val in kws.iteritems():
            vars = isinstance(val, basestring) and re.match('\\$\\{(.*)\\}', val)
            if vars:
                kws_val[name] = context.parse_value(vars.group(1), None)
            else:
                kws_val[name] = context.parse_value(name, val)

        return args_val, kws_val

class RemoteAction(object):
    ERR_IGNORE = 1 # ignore remaining action, start to execution stop_action
    ERR_EXIT = 2   # exit the process immediately
    ERR_IGNORE_ONE = 3 # ignore current action, all actions be depended can not start.

    def __init__(self, declare):
        self._handler = self
        self.id = 999
        self.desc = declare.get('desc')
        self.name = declare.get('name')
        depends = declare.get('depends')
        self.depends = depends and depends.split(',') or []
        self.critical = bool(declare.get('critical'))
        self.start_action = getattr(self, '%s_handler'%declare.get('start_action_type'))(declare.get('start_action'))
        self.stop_action = getattr(self, '%s_handler'%declare.get('stop_action_type'))(declare.get('stop_action'))

    def python_handler(self, script):
        def fun(context):
            try:
                eval(script)
            except Exception, e:
                logging.exception(e)
                if 'ERR_IGNORE' in str(e): return self.ERR_IGNORE
                if 'ERR_EXIT' in str(e): return self.ERR_EXIT
        return fun


class CIServices(object):
    def __int__(self):
        self._services = []
        self.status = 'start'

    def scan_ci_services(self):
        #load all external scripts configuration.
        from lybica.loader import load_scripts
        self.scripts = load_scripts()

        # warn for duplicate action
        _exist_actions = {}

        #scan local actions
        import lybica.actions as actions
        local_action_list = []
        for e in dir(actions):
            cls = getattr(actions, e)
            if not isinstance(cls, (types.ClassType, types.TypeType)):
                continue
            if not hasattr(cls, 'NAME'):
                continue
            action = Action(cls())
            action._handler.scripts = self.scripts
            if action.name in _exist_actions:
                old = _exist_actions[action.name]
                logging.warn('old: [%3d] %20s(depend %s) - %s' % (old.id, old.name, old.depends, old.desc))
                logging.warn('new: [%3d] %20s(depend %s) - %s' % (action.id, action.name, action.depends, action.desc))
            else:
                _exist_actions[action.name] = action
            local_action_list.append(action)
        local_action_list.sort(lambda x,y: cmp(x.id, y.id))
        logging.debug('--------------list all local available actions-------------')
        for e in local_action_list:
            logging.debug('[%3d] %20s(depend %s) - %s' % (e.id, e.name, e.depends, e.desc))

        #scan actions on remote server
        logging.debug('--------------list all remote available actions-------------')
        remote_action_list = []
        remote_actions = self.context.rpc.actions()
        for action in remote_actions:
            if action['name'] in _exist_actions:
                old = _exist_actions[action['name']]
                logging.warn('old: [%3d] %20s(depend %s) - %s' % (old.id, old.name, old.depends, old.desc))
                logging.warn('Ignore duplicate action %s on Coci server.'%(action['name']))
                continue
            logging.debug('[999] %20s(depend %s) - %s' % (action['name'], action['depends'], action['desc']))
            remote_action_list.append(str(action['name']))

        logging.debug('--------------Done list available actions-------------')

        return local_action_list + remote_action_list

    def run(self):
        from .rpc import RPC

        self.context = Context()
        self.context.ACTION_LIST = ['init_primary_actions', ]
        self.context.rpc = RPC()
        self._services = self.scan_ci_services()

        logging.debug('--------------Start to run actions-------------')
        self._start_actions(self.context)
        logging.debug('--------------Stop actions-------------')
        self._stop_action(self.context)
        sys.exit(self.context.ERR_CODE)

    def _get_ci_action(self, name_or_id):
        for e in self._services:
            if isinstance(e, types.StringType):
                if name_or_id == e:
                    values = {'name': e,}
                    action_declare = self.context.rpc.action__detail(**values).get('action_declare',{})
                    self._services.remove(e)
                    e = RemoteAction(action_declare)
                    e._handler.scripts = self.scripts
                    self._services.append(e)
                    return e
            else:
                if name_or_id == e.name or name_or_id == e.id:
                    return e
        return None

    def _start_actions(self, context):
        def _action_could_be_run(depends):
            # TODO: support use () to composition condition.
            for action in depends:
                if action.endswith('*'):
                    action = action.strip('*')
                    if action in context.ACTION_LIST and action not in context.DONE_ACTIONS:
                        return False
                elif action.count('|') > 0:
                    status = False
                    for act in action.split('|'):
                        if act in context.DONE_ACTIONS:
                            status = True
                    if not status:
                        return False
                elif action not in context.DONE_ACTIONS:
                    return False
            return True
        has_action_execute = True
        while context.ACTION_LIST and has_action_execute:
            has_action_execute = False
            for action_name in context.ACTION_LIST:
                action = self._get_ci_action(action_name)
                if action is None:
                    logging.debug('Action %s not in available actions. Please add it in Lybica Platform first.' % action_name)
                elif _action_could_be_run(action.depends):
                    context.CURRENT_ID = action.id
                    has_action_execute = True
                    context.ACTION_LIST.remove(action_name)
                    logging.info('')
                    logging.info('[Start] %s(depend %s) - %s...' % (action.name, action.depends, action.desc))
                    ret = action.start_action(context)
                    if ret == Action.ERR_EXIT:
                        logging.info('Exit process at "%s(%s)".' % (action.name, action.id))
                        sys.exit(context.ERR_CODE)
                    elif ret == Action.ERR_IGNORE:
                        logging.info('Skip all actions for error action "%s(%s)". %s remaining in ACTION_LIST.' % (action.name, action.id, context.ACTION_LIST))
                        return
                    elif ret == Action.ERR_IGNORE_ONE:
                        logging.info('Skip error action "%s(%s)".' % (action.name, action.id))
                    else:
                        context.DONE_ACTIONS.append(action.name)
                    break
        if context.ACTION_LIST:
            logging.info('%s remaining in ACTION_LIST.' % (context.ACTION_LIST))
        critical_actions = [action_name for action_name in context.ACTION_LIST if self._get_ci_action(action_name).critical]
        if critical_actions:
            logging.info('Critical actions %s remaining in ACTION_LIST.' % (critical_actions))

    def _stop_action(self, context):
        end_actions = context.DONE_ACTIONS
        end_actions.reverse()
        for action_name in end_actions:
            action = self._get_ci_action(action_name)
            if action is None:
                logging.debug('Action %s not in available actions. Please add it in Lybica Platform first.' % action_name)
            else:
                context.CURRENT_ID = action.id
                logging.info('')
                logging.info('[Stop] %s(%s)' % (action.name, action.id))
                ret = action.stop_action(context)
                if ret == Action.ERR_EXIT:
                    logging.info('Exit process at "%s(%s)".' % (action.name, action.id))
                    sys.exit(context.ERR_CODE)
                elif ret == Action.ERR_IGNORE:
                    logging.info('Ignore stop action from "%s(%s)".' % (action.name, action.id))
                    break

def main():
    FORMAT = '%(asctime)s %(levelname)6s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt='%m%d%H%M%S', stream=sys.stdout)
    CIServices().run()

def _print_build_info():
    try:
        from lybica.version import VERSION
        print 'Version:%s' % VERSION
    except ImportError:
        print 'Version: unkown'

if '__main__' == __name__:
    _print_build_info()
    main()


