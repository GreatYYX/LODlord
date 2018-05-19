import uuid


class Record(object):
    def __init__(self, raw_object):
        self.raw_object = raw_object
        self.id = str(uuid.uuid4())


class slot(property):
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self

        return self.func(obj)
