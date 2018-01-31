class EAGLEError(BaseException):
    def __init__(self, errstr):
        self.err=errstr
