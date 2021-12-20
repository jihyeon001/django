# django
django 삽질 기록

## Resource
- ECR
- ECS
- RDS(mariadb), Elastic Cache

![aws-architecture](./img/aws-architecture.png)

## Source구조
- [terraform best practice](https://medium.com/xebia-engineering/best-practices-to-create-organize-terraform-code-for-aws-2f4162525a1a) 참고.
~~~sh
├─Github
│ README.md
│ .gitignore
│ 
├─app                   # application source directory
│  │  Dockerfile
│  │  manage.py
│  │  requirements.txt
│  ├─env
│  └─hello_django
└─terraform             # terraform source directory
   │  main.tf
   │  variables.tf
   │  terraform.tfvars
   │  secrets.tfvars.sample
   ├─bin                # application docker image build & push
   │   └─build.sh 
   └─modules
       ├─alb
       │  main.tf
       │  variables.tf
       ├─ecr
       │  main.tf
       │  variables.tf
       ├─ecs
       │  main.tf
       │  variables.tf
       ├─elasticache
       │  main.tf
       │  variables.tf
       ├─network
       │  main.tf
       │  variables.tf
       ├─rds
       │  main.tf
       │  variables.tf
       └─sg
          main.tf
          variables.tf
~~~