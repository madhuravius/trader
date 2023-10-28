class TraderException(Exception):
    def __init__(self, message="Trader exception encountered"):
        self.message = message
        super().__init__(self.message)
