from django.core.mail  import EmailMessage
from ..exceptions      import InternalServerErrorException

EMAIL_BODY_STYLES : dict

class Email:
    subtype       = 'html'
    fail_silently = False
    body_style    = EMAIL_BODY_STYLES
    email_class   = EmailMessage

    def __init__(self, recipient_name, recipient_email, auth_number):
        self.recipient_name  = recipient_name
        self.recipient_email = recipient_email
        self.auth_number     = auth_number

    def get_body(self):
        return (
            "<div style=\"{text_style}\">"
            "<H2>환영합니다. {recipient_name}님</H2>"
            "<p>아래 인증번호를 입력하여 이메일 인증을 완료하세요.</p></div>"
            "<br><div class=\"wrap\" style=\"{wrap_style}\">"
            "<button style=\"{button_style}\">"
            "{auth_number}</button></div>".format(
                text_style=self.body_style['TEXT'],
                recipient_name=self.recipient_name,
                auth_number=self.auth_number,
                wrap_style=self.body_style['WRAP'],
                button_style=self.body_style['BUTTON'],
            )
        )

    def get_email_message(self):
        return self.email_class(
            subject=self.body_style['SUBJECT'], 
            body=self.get_body(), 
            from_email=self.body_style['FROM'], 
            to=[self.recipient_email]
        )

    def send(self):
        try:
            email_message = self.get_email_message()
            email_message.content_subtype = self.subtype
            email_message.send(self.fail_silently)
        except Exception as e:
            raise InternalServerErrorException(
                message=f'{self.__class__.__name__} {e}'
            )