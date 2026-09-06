from django.core.mail import EmailMessage, BadHeaderError
import smtplib
from decouple import config
import requests
from threading import Thread
import logging

logger = logging.getLogger(__name__)

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

def send_email_api(to_email, param={}, template_id=0, cc_email=None):
    try:
        if isinstance(to_email, list): # if to email is list 
            to_list = [{"email": email} for email in to_email]
        else:
            to_list = [{"email": to_email}]
        
        if isinstance(cc_email, list): # if to email is list 
            cc_list = [{"email": email} for email in cc_email]
        elif cc_email:
            cc_list = [{"email": cc_email}]

        payload = {
            "sender": {
                "email": config("DEFAULT_FROM_EMAIL"),
                "name": "Fitzz"
            },
            "to": to_list,
            # "subject": subject,
            # "htmlContent": f"<p>{body}</p>"
            "templateId": template_id,
            "params": param
        }

        if cc_email:
            payload["cc"] = cc_list

            
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": config("EMAIL_HOST_API_KEY"),
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10  # prevents long hanging
        )

        if response.status_code != 201:
            logger.error("Brevo email failed [%s]: %s", response.status_code, response.text)

    except Exception:
        logger.exception("Email API request failed")


def send_sms(otp, to_number):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        # "route" : "otp",
        # "variables_values" : otp, #only otp
        "route": "q",   # transactional route
        "message": f"Fitzz: Your OTP is {otp}. Valid for 5 minutes. Do not share this code.",
        "numbers" : to_number,
    }

    headers = {
        "authorization":config('FAST2SMS_API_KEY'),
        "Content-Type":"application/json"
    }

    response = requests.post(url, data=payload, headers=headers)
    # print("Response Headers:", response.headers)


def send_template_email(template_key, emails, param):
    # send_email_smtp(subject, body, to_email, cc_email)
    cc_email = None
    template_id = 0
    if template_key == "OTP":
        template_id = 1
    elif template_key == "Welcome":
        template_id = 2
    elif template_key == "register_gym":
        template_id = 3
        cc_email = ["admin@fitzz.in"]
    elif template_key == "subscription_plan":
        template_id = 5
        cc_email = ["admin@fitzz.in"]
    elif template_key == "access_session":
        template_id = 4
        cc_email = ["admin@fitzz.in"]
    elif template_key == "access_session_gym_owner":
        template_id = 6
        cc_email = ["admin@fitzz.in"]
    
    if template_id>0:
        Thread(
            target=send_email_api,
            args=(emails["to_email"], param, template_id, cc_email),
            daemon=True
        ).start()
    pass