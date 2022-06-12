import os

def get_hostname():
    '''
        인스턴스를 식별하기 위한 문자열을 가져오는 함수
        - EC2 Instance의 경우 HOSTNAME에 Private IP DNS를 자동할당        
    '''
    hostname = os.getenv('HOSTNAME', 'localhost')
    if '.' in hostname:
        hostname = hostname.split('.')[0]
    if '-' in hostname:
        hostname = hostname.split('-')[-1]
    return hostname