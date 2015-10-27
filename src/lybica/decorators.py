import time
import logging


def retry(retry_times, retry_interval):
    ''' a decorator to handle retry operations '''
    def new_f(f):
        def _f(*args, **kwargs):
            for i in xrange(retry_times - 1):
                try:
                    return f(*args, **kwargs)
                except Exception, err:
                    logging.warn('error:%s, retry times:%s, sleep %s seconds and try again.' % (err, i, retry_interval))
                    time.sleep(retry_interval)
            else:
                return f(*args, **kwargs)
        _f.func_name = f.func_name
        return _f

    return new_f


def ignore_error(default_value):
    ''' a decorator to handle error execution, return default_value if error occurred '''
    def new_f(f):
        def _f(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception, err:
                logging.warn('error:%s, ignore it and return %s' % (err, default_value))
                return default_value
        _f.func_name = f.func_name
        return _f

    return new_f

