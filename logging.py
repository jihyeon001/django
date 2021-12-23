import json
import os
import logging
import time
from datetime                import datetime
from logging.handlers        import RotatingFileHandler
from rest_framework          import exceptions
from rest_framework.views    import set_rollback
from rest_framework.response import Response
from .outbounds              import AWSS3Client, SlackIncomingWebhooks

ACCESS_LOGER_NAME = 'access'
ERROR_LOGER_NAME = 'error'
SERVICE_NAME = 'service'
ENVIRONMENT = 'local'
VERSION = '210915'
LOG_DATETIME_FORMAT = '%Y%m%d-%H%M%S'
MODEL_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def get_server_id():
    '''
        인스턴스를 식별하기 위한 SERVER_ID를 가져오는 함수
        - EC2 Instance의 경우 HOSTNAME에 Private IP DNS를 자동할당        
    '''
    hostname = getattr(os.environ, 'HOSTNAME', None)
    server_domain = getattr(os.environ, 'SERVER_DOMAIN', None)
    if server_domain and '.' in server_domain:
        private_ip = server_domain.split('.')[0]
        if '-' in private_ip:
            return private_ip.split('-')[-1]
    else:
        return hostname

class AccessLoggingMiddleware:
    '''
        Access Log를 기록하는 미들웨어
        get_response를 이용하여 requset정보를 가져와 기록 (0.5ms 소요)
    '''
    SERVER_ID = get_server_id()
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self.access_loger(request=request)
        return response

    def json_converter(obj):
        if isinstance(obj, datetime):
            return int(time.mktime(obj.timetuple()))

    def access_loger(self, request):
        message = json.dumps({
            'timestamp' : int(time.time()),
            'datetime'  : datetime.now().strftime(MODEL_DATETIME_FORMAT),
            'client_ip' : request.META.get('HTTP_X_FORWARDED_FOR', None),
            'server_id' : self.SERVER_ID,
            'method'    : request.method,
            'path'      : request.path,
            'params'    : request.GET.dict(),
        }, ensure_ascii=False)
        logger = logging.getLogger(ACCESS_LOGER_NAME)
        logger.info(message)

def error_exception_handler(exc, context):
    '''
        Exception 로깅, 슬랙 (5ms 소요)
        - DRF의 APIException과 Django의 exception 포맷이 달라 후처리
        - slack으로 실시간 에러를 확인
    '''
    request = context['request']
    headers = {}
    if isinstance(exc, exceptions.APIException):
        message = exc.detail
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait
        if isinstance(exc.detail, (list, dict)):
            data = message
        else:
            data = {'detail': message}

        status_code = exc.status_code
    else:
        message = f'{exc.__class__.__name__}, {exc.args[0]}'
        data = {'detail': message}
        status_code = 500

    contents = (
        '{status_code}|{service_name}|{environment}-'
        '{version}|{server_id}|{method}|{path}] '
        '{message}'.format(
            status_code=status_code,
            service_name=SERVICE_NAME,
            environment=ENVIRONMENT,
            version=VERSION,
            server_id=get_server_id(),
            method=request.method,
            path=request.path,
            message=message,
        )
    )
    web_hooks = SlackIncomingWebhooks(contents=contents)
    web_hooks.start()
    logger = logging.getLogger(ERROR_LOGER_NAME)
    logger.error(contents)

    set_rollback()
    return Response(data, status=status_code, headers=headers)

class S3RotatingFileHandler(RotatingFileHandler):
    ACCESS_LOG_DIR = 'access_log'
    DEFAULT_CONTENT_TYPE = 'text/plain'

    def doRollover(self):
        """
            RotatingFileHandler를 활용하여 동일한 설정 값으로
            Access Log들을 S3에 주기적으로 백업
        """
        aws_s3_client = AWSS3Client()
        file_object = open(self.baseFilename, mode='rb')
        aws_s3_client.upload(
            file_object=file_object, 
            content_type=self.DEFAULT_CONTENT_TYPE,
            object_key=(
                '{access_log_dir}/{service_name}-'
                '{environment}-{version}-'
                '{server_id}-{now}.log'.format(
                    access_log_dir=self.ACCESS_LOG_DIR,
                    service_name=SERVICE_NAME,
                    environment=ENVIRONMENT,
                    version=VERSION,
                    server_id=get_server_id(),
                    now=datetime.now().strftime(LOG_DATETIME_FORMAT)
                )
            ),
        )
        super().doRollover()

