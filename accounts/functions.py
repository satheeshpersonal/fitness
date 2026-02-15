from .models import UserOTP
from lookups.functions import send_sms, send_template_email
import uuid
from django.utils import timezone
from datetime import timedelta
from .serializers import ReferralSerializer
from .models import Referral

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

def referral_data_update(referral_data):
    referral_data["reward_points"] = 0
    referred_count = Referral.objects.filter(referrer = referral_data["referrer"], user_status="C").count()
    if referred_count >= 2: #first 2 referral for free session
        referral_data["reward_points"] = 50

    referred_user = Referral.objects.filter(email = referral_data["email"])
    if referred_user:
        serializer = ReferralSerializer(referred_user, data=referral_data, partial=True)
    else:
        serializer = ReferralSerializer(data=referral_data)
    
    if serializer.is_valid():
        instance = serializer.save()
        print("instance -- ", instance)
    else:
        print("Error in referral flow - ", serializer.errors)