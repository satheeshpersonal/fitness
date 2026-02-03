from django.core.mail import EmailMessage, BadHeaderError
import smtplib
from decouple import config
import requests
from threading import Thread

# def send_email_smtp(subject, body, to_email, cc_email=None):
#     email = EmailMessage(
#         subject=subject,
#         body=body,
#         from_email=config('DEFAULT_FROM_EMAIL'),
#         to=to_email,
#     )
#     # email.send()
#     try:
#         result = email.send(fail_silently=False)
#         if result == 1:
#             print("Email sent successfully ")
#         else:
#             print("Email not sent ")
#     except BadHeaderError as e:
#         print(f"Invalid header found: : {e}")
#     except smtplib.SMTPException as e:
#         print(f"SMTP error: {e}")
#     except Exception as e:
#         print(f"Other error: {e}")

def send_email_api(subject, body, to_email, cc_email=None):
    try:
        if isinstance(to_email, list): # if to email is list 
            to_list = [{"email": email} for email in to_email]
        else:
            to_list = [{"email": to_email}]
            
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": config("EMAIL_HOST_API_KEY"),
                "Content-Type": "application/json",
            },
            json={
                "sender": {
                    "email": config("DEFAULT_FROM_EMAIL"),
                    "name": "Fitness App"
                },
                "to": to_list,
                "subject": subject,
                "htmlContent": f"<p>{body}</p>"
            },
            timeout=10  # prevents long hanging
        )

        if response.status_code == 201:
            print("Email sent via API ")
        else:
            print("Brevo error ", response.text)

    except Exception as e:
        print("Email API failed ", e)


def send_sms(otp, to_number):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "route" : "otp",
        "variables_values" : otp, #only otp
        "numbers" : to_number,
    }

    headers = {
        "authorization":config('FAST2SMS_API_KEY'),
        "Content-Type":"application/json"
    }

    response = requests.post(url, data=payload, headers=headers)
    print("Status Code:", response.status_code)
    # print("Response Headers:", response.headers)
    print("Response Text:", response.text)
    print("Response JSON (if any):", response.json() if response.headers.get('Content-Type') == 'application/json' else "Not JSON")


def send_template_email(subject, body, to_email, cc_email=None, template_key = None):
    # send_email_smtp(subject, body, to_email, cc_email)
    # print(to_email)
    Thread(
        target=send_email_api,
        args=(subject, body, to_email),
        daemon=True
    ).start()