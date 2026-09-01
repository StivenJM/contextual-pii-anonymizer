class ApplicationError(Exception):
    pass


class ResourceNotFoundError(ApplicationError):
    pass


class InvalidConfigurationError(ApplicationError):
    pass


class InferenceUnavailableError(ApplicationError):
    pass


class ModelUnavailableError(ApplicationError):
    pass
