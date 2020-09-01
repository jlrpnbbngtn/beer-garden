# -*- coding: utf-8 -*-


class ConfigurationError(Exception):
    """Generic configuration error"""

    pass


class PluginValidationError(Exception):
    """Plugin could not be created successfully"""

    pass


class PluginStartupError(Exception):
    """Plugin could not be started"""

    pass


class ShutdownError(Exception):
    """Backend has been shut down"""

    pass


class LoggingLoadingError(Exception):
    """Unable to load Plugin logging configuration"""

    pass


class EndpointRemovedException(Exception):
    """Requested endpoint is no longer valid"""

    def __init__(self, message=None):
        self.message = message


# Routing
class UnknownGardenException(Exception):
    """Route requested is not valid"""

    pass


class RoutingRequestException(Exception):
    """Route requested is not valid"""

    pass
