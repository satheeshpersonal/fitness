from .models import UserOTP
from lookups.functions import send_sms, send_template_email
import uuid
from django.utils import timezone
from datetime import timedelta

def generte_top(user, login_type=None):
    data = {}
    otp_code =str(uuid.uuid4().int)[0:6]
    UserOTP.objects.create(otp=otp_code, user=user, expire_on=timezone.now() + timedelta(minutes=10))

    return otp_code

def send_otp(mobile_number, email, otp_code, semding_type):
    if semding_type == 'M':
        # send_sms(otp_code, mobile_number) #send OTP to mobile number
        pass
    else:
        send_template_email("OTP", f"OTP is {otp_code}", [email])


def gym_response(gym):
    data = {}
    data['id'] = gym.id
    data['gym_name'] = gym.name
    data['address'] = gym.address
    data['city'] = gym.city
    data['state'] = gym.state
    data['country'] = gym.country
    data['latitude'] = gym.latitude
    data['longitude'] = gym.longitude

    data['profile_icon'] = None
    if gym.profile_icon:
        data['profile_icon'] = gym.profile_icon.url
    
    return data