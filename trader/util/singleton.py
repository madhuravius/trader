class Singleton(type):
    """
    This should enable singleton usage with any class specified. Can be used with:

    class Something(metaclass=Singleton)

    source: https://stackoverflow.com/a/6798042
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
