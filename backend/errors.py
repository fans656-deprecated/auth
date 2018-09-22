class Error(Exception):

    def __init__(self, message, status_code=400):
        self.resp = (message, status_code)


class InternalError(Error):

    def __init__(self):
        super(InternalError, self).__init__(
            'internal server error', 500
        )
