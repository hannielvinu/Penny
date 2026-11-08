class GatewayError(Exception):
    pass


class GatewayUnreachable(GatewayError):
    pass


class GatewayBudgetExceeded(GatewayError):
    pass


class RateLimited(GatewayError):
    pass


class AllProvidersFailed(GatewayError):
    pass


class AuthError(GatewayError):
    pass


class BadRequest(GatewayError):
    pass


class Timeout(GatewayError):
    pass
