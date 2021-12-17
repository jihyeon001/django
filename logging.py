import json
import os
import logging
import time
from datetime              import datetime
from logging.handlers      import RotatingFileHandler
from rest_framework.views  import exception_handler
from .outbounds            import AWSS3Client, SlackIncomingWebhooks

ACCESS_LOGER_NAME = 'access'
ERROR_LOGER_NAME = 'error'
SERVICE_NAME = 'service'
ENVIRONMENT = 'local'
VERSION = '210915'


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
            'datetime'  : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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

        1. AccessLoggingMiddleware와의 분리
            DRF의 APIException과 Django의 exception
            Response가 각각 Response, HttpResponse로 
            HttpResponse의 경우 내부 메시지를 가져오려면 후처리가 필요
            따라서 custom handler로 분리
            exception_handler에서 APIException이 아닐경우 None을 반환하는 로직을 활용
            동일한 포맷(예외클래스명, 상세메시지)의 메시지로 로깅

        2. slack
            실시간 에러를 확인하기 위해 적용,
            threading 모듈로 비동기처리
    '''
    reponse = exception_handler(exc, context)
    request = context['request']
    if not reponse:
        message = f'{exc.__class__.__name__}, {exc.args[0]}'
    else:
        message = reponse.data.get('detail', None)

    server_id = get_server_id()
    contents = (
        f'{SERVICE_NAME}|{ENVIRONMENT}-{VERSION}|{server_id}|'
        f'{request.method}|{request.path}] {message}'
    )
    web_hooks = SlackIncomingWebhooks(contents=contents)
    web_hooks.start()
    logger = logging.getLogger(ERROR_LOGER_NAME)
    logger.error(contents)
    
class S3RotatingFileHandler(RotatingFileHandler):
    '''
        RotatingFileHandler를 활용하여 동일한 설정 값으로
        Access Log들을 S3에 주기적으로 백업        
    '''
    content_type = 'text/plain'
    SERVER_ID = get_server_id()

    def get_s3_access_log_filename(self):
        now = datetime.now().strftime('%Y%m%d-%H%M%S')
        return f'access_log/{SERVICE_NAME}-{ENVIRONMENT}-{VERSION}-{self.SERVER_ID}-{now}.log'

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        cli = AWSS3Client()
        file_object = open(self.baseFilename, mode='rb')
        cli.upload(
            file_object=file_object, 
            object_key=self.get_s3_access_log_filename(), 
            content_type=self.content_type
        )
        super().doRollover()

