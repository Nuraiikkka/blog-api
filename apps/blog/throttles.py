from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class RegisterRateThrottle(AnonRateThrottle):
    scope = 'register'
    rate = '5/min'


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'
    rate = '10/min'


class PostCreateRateThrottle(UserRateThrottle):
    scope = 'post_create'
    rate = '20/min'