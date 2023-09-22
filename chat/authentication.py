from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication

from .protocol import AUTH_KEY
from .exceptions import NotAuthenticated


class AuthRequest():
    def __init__(self, auth_header):
        header_bytes = bytes(auth_header, encoding='utf-8')
        self.META = {'HTTP_AUTHORIZATION': header_bytes}

class JWTAuthentication():
    base_auth = BaseJWTAuthentication()
    
    def authenticate(self, auth_data):
        header = auth_data[AUTH_KEY]
        request = AuthRequest(header)

        try:
            auth_result = self.base_auth.authenticate(request)
        except Exception as exc:
            raise NotAuthenticated(*exc.args)
        
        if isinstance(auth_result, tuple):
            user = auth_result[0]
            return user
        else:
            raise NotAuthenticated('Authentication Failed')