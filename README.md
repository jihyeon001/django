# django
django 삽질 기록

## Dependency
- [Django](https://github.com/django/django)
- [Django-REST-Framework](https://github.com/encode/django-rest-framework)
- [rest-framework-jwt](https://github.com/jpadilla/django-rest-framework-jwt)
- [requests](https://github.com/psf/requests)
- [boto3](https://github.com/boto/boto3)
- [numpy](https://github.com/numpy/numpy)
- [opencv-python](https://github.com/opencv/opencv-python)
- [urllib3](https://github.com/urllib3/urllib3)

## Progress
Active Record 방식의 model에서 Entity를 분리하기보다
Serializer + Repository를 추가하고
Service에 DI를 적용 해보는 시도 중

## Source
~~~sh
├─bases        # baseclass
│  │ model.py
│  │ repository.py
│  │ service.py
│  │ test.py
│  │ viewset.py
│
├─commons      # exceptions 등의 공통 모듈
│  │ exceptions.py
│  │ image_resize.py
│  │ logging.py
│
├─outbounds    # 외부 API
│  │ aws.py
│  │ mail.py
│  │ slack.py
│  │ sms.py
│
│ .gitignore
│ README.md
~~~
