from rest_framework.exceptions import APIException
from rest_framework import status

class BaseDetailException(APIException):
    def __init__(self, detail=None, code=None):
        '''
            메시지 수정
        '''
        super().__init__(detail=detail, code=code)
        
class NotauthenticatedException(APIException):
    status_code    = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Notauthenticated, Authentication credentials were not provided.'
    default_code   = 'Notauthenticated'

class PermissionDeniedException(APIException):
    status_code    = status.HTTP_403_FORBIDDEN
    default_detail = 'PermissionDenied, Authentication not have permission to perform this action.'
    default_code   = 'PermissionDenied'

class ObjectDoesNotExistException(BaseDetailException):
    status_code    = status.HTTP_404_NOT_FOUND
    default_detail = 'NotFound, Object does not exist.'
    default_code   = 'ModelNotFound'

class KeyErrorException(BaseDetailException):
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = 'BadRequest, KeyError'
    default_code   = 'KeyError'

class AttributeErrorException(BaseDetailException):
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = 'BadRequest, AttributeError'
    default_code   = 'AttributeError'

class ValidationErrorException(BaseDetailException):
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = 'BadRequest, ValidationError'
    default_code   = 'ValidationError'

class InternalServerErrorException(BaseDetailException):
    status_code    = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'InternalServerError'
    default_code   = 'InternalServerError'
