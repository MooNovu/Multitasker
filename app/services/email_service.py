from email.mime.text import MIMEText
import smtplib


class EmailService:
    def __init__(self):
        self.SMTP_SERVER = "smtp.yandex.ru"
        self.SMTP_PORT = 465
        self.SMTP_LOGIN = "andrey2004rus@yandex.ru"
        self.SMTP_PASSWORD = "nhtxirjmtsdcxawk"


    async def send_email(self, to_email: str, subject: str, body: str):
        try:
            # Создаем сообщение
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.SMTP_LOGIN
            msg['To'] = to_email

            with smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.login(self.SMTP_LOGIN, self.SMTP_PASSWORD)
                server.send_message(msg)
            return {"message": "Email успешно отправлен"}
        except Exception as e:
            return {"error": f"Ошибка при отправке email: {str(e)}"}
