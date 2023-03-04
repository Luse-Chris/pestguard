class VFDError(Exception):
    def __str__(self):
        return f"CODE: {self.error_code}\nDescription: {self.error_message}"

class VFDValidationError(VFDError):
    error_code = "validation_error"
    def __init__(self, error):
        super(VFDError, self).__init__(error)
        self.error_code = self.error_code
        message = ""
        for item in error["detail"]:
            message += item.get("msg") + "\n"
        self.error_message = message

    def __str__(self):
        return f"CODE: {self.error_code}\nDescription: {self.error_message}"

class VFDAuthEror(VFDError):
    error_code = "auth_error"
    def __init__(self, error):
        super(VFDAuthEror, self).__init__(error)
        self.error_code = self.error_code
        self.error_message = error["detail"]

class VFDSubscriptionExpired(VFDError):
    error_code = "subscription_expired"
    def __init__(self, error):
        super(VFDSubscriptionExpired, self).__init__(error)
        self.error_code = self.error_code
        message = None
        self.error_message = error["detail"]

class VFDInternalServerError(VFDError):
    error_code = "internal_server_error"
    def __init__(self, error):
        super(VFDInternalServerError, self).__init__(error)
        self.error_code = self.error_code
        message = None
        self.error_message = error["detail"]