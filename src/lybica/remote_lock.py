import os
import logging
import urllib
import socket
import time
import threading

class RemoteLock(object):
    def __init__(self, end_point=''):
        self.log = logging.getLogger("lock")
        self.end_point = end_point

    def require(self, lock_name='', owner='', timeout=60 * 1000):
        data = self._rpc_call(name=lock_name, owner=owner,
                              timeout=timeout or 60 * 1000)
        lock = Lock(lock_name, owner)
        lock.timeout = data.get('lock_timeout')
        lock.cur_owner = data.get('lock_owner', 'error')
        lock.isLocked = data.get('locked') == 'ok'
        lock._rpc = self
        return lock

    def release(self, lock):
        self._rpc_call(name=lock.name, owner=lock.owner, release='Y')
        lock.isLocked = False
        return lock

    def _rpc_call(self, **kw):
        socket.setdefaulttimeout(10)
        data = {}
        kw['ajax'] = 'Y'
        resp_data = ""
        try:
            response = urllib.urlopen(self.end_point, urllib.urlencode(kw),
                                  proxies={})
            resp_data = response.read()
            data['locked'] = response.headers['locked']
            data['lock_owner'] = response.headers['lock_owner']
            data['lock_name'] = response.headers['lock_name']
            data['lock_timeout'] = response.headers['lock_timeout']
        except Exception, e:
            self.log.warn("lock error:%s, reponse_data:%s" % (e, resp_data))
        return data

class Lock(object):
    def __init__(self, name, owner, isLocked=False):
        self.name = name
        self.owner = owner
        self.isLocked = isLocked
        self.timeout = 0

    def ok(self):
        return self.isLocked

    def release(self):
        if hasattr(self, "_rpc"): self._rpc.release(self)

class DeviceLocker(object):
    def __init__(self, dev_list):
        self.lock_service = os.getenv('REMOTE_LOCK_RPC', "http://10.56.117.81/lock/")
        self.lock_service = RemoteLock(self.lock_service)
        self.lock_names = ['dev_%s' % e.strip() for e in dev_list if e.strip()]
        self.owner = os.getenv('BUILD_URL', "http://127.0.0.1/")
        self.mutex = threading.Lock()
        self.locks = {}

    def try_and_wait_lock(self):
        all_is_ok = False

        logging.info("try to lock devices...")
        for retry in range(20):
            all_is_ok = True
            for e in self.lock_names:
                l = self.lock_service.require(e, self.owner, timeout=60 * 1000 * 5)
                if not l.ok():
                    logging.info("Failed to lock '%s', current is locked by '%s'" % (e, l.cur_owner))
                    all_is_ok = False
                else:
                    self.locks[e] = l
            if all_is_ok:
                logging.info("all lock is ok now.")
                break
            else:
                logging.info("waiting 60 seconds, try again.")
                time.sleep(60)
        logging.info("all devices are locked, device:%s" % (",".join(self.lock_names)))

        return all_is_ok

    def start_to_keep_lock(self):
        th = threading.Thread(target=self._refresh_lock)
        th.daemon = True
        th.start()

    def _refresh_lock(self):
        logging.info("start to keep the lock...")
        while 1:
            self.mutex.acquire()
            if self.locks:
                for e in self.lock_names:
                    l = self.lock_service.require(e, self.owner, timeout=60 * 1000 * 5)
                    if not l.ok():
                        logging.warn("Failed to lock '%s', current is locked by '%s'" % (e, l.cur_owner))
                self.mutex.release()
            else:
                self.mutex.release()
                break
            time.sleep(60)

    def stop(self):
        self.mutex.acquire()
        cur_locks = self.locks.values()
        self.locks = {}
        for e in cur_locks:
            e.release()
        self.mutex.release()
        logging.info("All lock is released.")

