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

## Progress
typing 적용

## Structure
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
│  │ go_pub_data.py
│  │ slack.py
│  │ sms.py
│
│ .gitignore
│ README.md
~~~
