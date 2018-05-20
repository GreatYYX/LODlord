class ParseException(BaseException):
    def __init__(self, message, line):
        super().__init__(message)
        self.line = line
        self.message = message

    def __str__(self):
        return 'Exception #{}: {}'.format(self.line, self.message)