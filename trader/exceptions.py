class TraderException(Exception):
    def __init__(self, message="Trader exception encountered"):
        self.message = message
        super().__init__(self.message)


class TraderClientException(TraderException):
    pass


class TraderDaoException(TraderException):
    pass


class TraderQueueException(TraderException):
    pass
