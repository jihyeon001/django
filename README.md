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

## Source 구조
~~~sh
├─Github
│ .gitignore
│ .gitmessage.txt
│ base_model.py      # model의 baseclass
│ base_test.py       # service test의 baseclass
│ base_viewset.py
│ README.md
│ exceptions.py
│ logging.py         # access log, log handler
│ outbounds.py       # 외부 API
│ #services.py       # service layer - PR 도전중
│ utils.py           # image uploader 등
~~~
