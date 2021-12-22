from rest_framework.exceptions import APIException
from rest_framework import status

class BaseDetailException(APIException):
    def __init__(self, detail=None, code=None):
        '''
            메시지 수정
        '''
        super().__init__(detail=detail, code=code)
        
class ObjectDoesNotExistException(BaseDetailException):
    status_code    = status.HTTP_404_NOT_FOUND
    default_detail = 'model does not exist'
    default_code   = 'NotFound'
        
class KeyErrorException(BaseDetailException):
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = 'key error'
    default_code   = 'KeyError'

class NotauthenticatedException(APIException):
    status_code    = status.HTTP_401_UNAUTHORIZED
    default_detail = 'missing authentication token'
    default_code   = 'Notauthenticated'

class PermissionDeniedException(APIException):
    status_code    = status.HTTP_403_FORBIDDEN
    default_detail = 'permission denied'
    default_code   = 'PermissionDenied'

class InternalServerErrorException(BaseDetailException):
    status_code    = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'internal server error'
    default_code   = 'InternalServerError'

