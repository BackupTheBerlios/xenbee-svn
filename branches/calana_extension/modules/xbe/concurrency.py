
class LockMgr:
    def __init__(self, mtx):
        self.__mtx = mtx
        self.__mtx.acquire()

    def __del__(self):
        self.__mtx.release()
        del self.__mtx
