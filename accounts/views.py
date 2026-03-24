from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication
from .models import CustomUser, UserOTP, UserSelectLocation, Gym, GymFavorite, GymReview, Referral, FreeSessionRequest, FreeSessionRequest
from .serializers import CustomUserSerializer, UserProfileSerializer, UserSelectLocationSerializer, GymDetailsSerializer, GymListSerializer, GymReviewSerializer, GymFavoriteSerializer, ReferralSerializer, GymCreateSerializer, GymOptionsSerializer, GymNameListSerializer
from subscriptions.serializers import UserSubscriptionSerializer
from subscriptions.models import UserSubscription
from workouts.models import GymAccessLog
from django.shortcuts import get_object_or_404
from .functions import generte_top, send_otp, gym_response, referral_data_update, validate_email, verify_msg91_token
from django.db.models import Q
from django.utils import timezone
from FitnessApp.utils.response import success_response, error_response
from rest_framework.authtoken.models import Token
from lookups.functions import send_template_email
from geopy.distance import geodesic
from subscriptions.functions import get_count_data
from workouts.functions import get_last_activity
from django.db.models import Avg, Count, Sum
from datetime import date
# Create your views here.


class CustomUserView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """

    def get(self, request):
        authentication_classes = [authentication.TokenAuthentication]
        permission_classes = [permissions.IsAuthenticated]
        
        user_data = UserProfileSerializer(request.user).data
        user_data["full_name"] = user_data["first_name"]+" "+user_data["last_name"]
        
        subscription_data = UserSubscription.objects.filter(user=request.user, is_active=True, expire_on__gte=date.today()).first()
        user_data["current_plan"] = {}
        if subscription_data:
            user_data["current_plan"] = UserSubscriptionSerializer(subscription_data).data
        
        success_data =  success_response(message=f"success", code="success", data=user_data)
        return Response(success_data, status=200)
        
    def post(self, request): #Register User
        # print(request.data)
        data = request.data
        mobile_number = data.get("mobile_number", None)
        email = data.get("email", None)
        referral_code = data.pop("referral_code", None)
        message = ""
        
        if not mobile_number and not email:
            print("value missing")
            error_data =  error_response(message="User name is required to create user", code="user_name", data={})
            return Response(error_data, status=200)
        
        if mobile_number:
            data["username"] = mobile_number 
            data["login_type"] = "M" 
            message = "OTP triggered to your register mobile number"
        else:
            valid_email = validate_email(email)
            if not valid_email:
                error_data =  error_response(message="Please use a valid email provider", code="user_name", data={})
                return Response(error_data, status=200)

            email = valid_email
            data["username"] = email 
            print("valid_email - ", email)
            data["login_type"] = "E" 
            message = "OTP triggered to your register email"

        #check user alredy exist
        user_data = CustomUser.objects.filter(Q(mobile_number = mobile_number, mobile_number__isnull=False) | Q(email__iexact = email, email__isnull=False)).first()
        if user_data:
            otp_code = generte_top(user_data, data["login_type"])
            send_otp(mobile_number, email, otp_code, data["login_type"])
            # return Response("Use OTP to login", status=status.HTTP_201_CREATED)
            success_data =  success_response(message=f"{message}, Please use to login", code="success", data=data)
            return Response(success_data, status=200) 
        
        #if new user
        serializer = CustomUserSerializer(data=data)
        if serializer.is_valid():
            user_obj = serializer.save()
            otp_code = generte_top(user_obj, data["login_type"]) 
            # trigger OTP
            send_otp(mobile_number, email, otp_code, data["login_type"])

            if referral_code: #refrel flow
                referred_by = CustomUser.objects.filter(~Q(id=user_obj.id), referral_code=referral_code).first()
                if referred_by:
                    referral_data_update({"referrer":referred_by.id, "referred_user":user_obj.id, "referral_code":referral_code, "email":user_obj.email})
                    
            success_data =  success_response(message=f"{message}, Please use to complete the register", code="success", data=data)
            return Response(success_data, status=200) 
            # return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        error_data =  error_response(message=serializer.errors, code="error", data={})
        return Response(error_data, status=200) 
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        authentication_classes = [authentication.TokenAuthentication]
        permission_classes = [permissions.IsAuthenticated]

        user_input_data = request.data
        if hasattr(user_input_data, "_mutable") and not user_input_data._mutable and not request.FILES:
            user_input_data._mutable = True

        required_fields = ['full_name']
        missing_fields = [field for field in required_fields if not user_input_data.get(field)]
        if missing_fields:
            error_data =  error_response(message=f"Missing or empty fields: {', '.join(missing_fields)}", code="success", data={})
            return Response(error_data, status=200)
        
        full_name = user_input_data.pop("full_name", None)
        # Split full name
        if full_name:
            print(full_name)
            name_parts = full_name[0].split()
            user_input_data["first_name"] = name_parts[0]
            user_input_data["last_name"] = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            user_input_data["profile_completed"] = True

        user_data = request.user
        print(user_data)
        serializer = UserProfileSerializer(user_data, data=user_input_data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()

            data = serializer.data
            data["full_name"] = data["first_name"]+" "+data["last_name"]
            success_data =  success_response(message=f"Profile updated successfully", code="success", data=data)
            return Response(success_data, status=200)
            # return Response(serializer.data)
        error_data =  error_response(message=serializer.errors, code="error", data={})
        return Response(error_data, status=200) 


class ResendOTPView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    def post(self, request): #Register User
        # print(request.data)
        data = request.data
        user_name = data.get("user_name", None)
        login_type = data.get("login_type", None)

        if not user_name:
            print("value missing")
            error_data =  error_response(message="User name is required to send OTP", code="user_name", data={})
            return Response(error_data, status=200)
        
        user_data = CustomUser.objects.filter(Q(mobile_number = user_name) | Q(email__iexact = user_name)).first()
        if not user_data:
            error_data =  error_response(message="User account not exist", code="not_found", data={})
            return Response(error_data, status=200) 
        elif user_data and user_data.status in ["I", "D"]:
            error_data =  error_response(message="Please contact admin", code="login_error", data={})
            return Response(error_data, status=200)
        
        otp_code = generte_top(user_data, login_type)
        send_otp(user_data.mobile_number, user_data.email, otp_code, login_type)
        # return Response("Use OTP to login", status=status.HTTP_201_CREATED)
        success_data =  success_response(message="OTP triggered successfully", code="success", data=data)
        return Response(success_data, status=200) 
        

class verifyOTPView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for verify OTP
    """
  
    def post(self, request): #Register User
        # print(request.data)
        data = request.data
        username = data.get("username", None)
        otp_code = data.get("otp_code", None)
        msg_token = data.get("msg_token", None)
        referral_code = data.pop("referral_code", None)
        msg_token_valid = False

        if not username and (not otp_code or not msg_token):
            error_data =  error_response(message="User name and OTP required for verfiy account", code="missing_value", data={})
            return Response(error_data, status=200) 
            # return Response({"error": "User name and OTP required for verfiy account"}, status=status.HTTP_400_BAD_REQUEST) 
        
        #check user alredy exist
        user_data = CustomUser.objects.filter(Q(mobile_number = username) | Q(email__iexact = username)).first()
        if not user_data and data["login_type"] == "M" :
            serializer = CustomUserSerializer(data=data)
            if serializer.is_valid():
                user_data = serializer.save()
                # if referral_code: #refrel flow
                #     referred_by = CustomUser.objects.filter(~Q(id=user_data.id), referral_code=referral_code).first()
                # if referred_by:
                #     referral_data_update({"referrer":referred_by.id, "referred_user":user_data.id, "referral_code":referral_code, "email":user_data.email})
            else:
                print(data)
                print("serializer - ", serializer.errors)
                error_data =  error_response(message=serializer.errors, code="error", data={})
                return Response(error_data, status=200)
            # error_data =  error_response(message="User account not exist", code="not_found", data={})
            # return Response(error_data, status=200) 
        elif user_data and user_data.status in ["I", "D"]:
            error_data =  error_response(message="Please contact admin", code="login_error", data={})
            return Response(error_data, status=200)
        if user_data:
            print("user_data")
            if data["login_type"] == "M":
                print("login_type")
                msg_verify_data = verify_msg91_token(msg_token)
                if msg_verify_data["code"] == 200:
                    msg_token_valid = True
            
            user_otp = UserOTP.objects.filter(user = user_data, expire_on__gte = timezone.now()).order_by("-created_at").first()
            if (user_otp and user_otp.otp == otp_code) or msg_token_valid:
                if user_data.status == "P":
                    user_data.status = "A"
                    user_data.save(update_fields=["status"])
                    #send welcome email to user if first time verifiy account
                    if user_data.email and user_data.user_type == "U":
                        # send_template_email("Welcome", f"Welcome to the application", [user_data.email]) 
                        emails = {"to_email":[user_data.email]}
                        param = {"first_name":user_data.first_name}
                        send_template_email("Welcome", emails, param)

                user_details = CustomUserSerializer(user_data).data
                
                # if user_data.profile_completed: #check Profile status
                # Delete old token if exists
                Token.objects.filter(user=user_data).delete()
                # Create new token
                token = Token.objects.create(user=user_data)
                user_details["token"]=token.key
                user_details["full_name"] = user_details["first_name"]+" "+user_details["last_name"]

                # check this user in referral program
                referred_user = Referral.objects.filter(referred_user = user_data.id, user_status="P").first()
                if referred_user:
                    referral_data = {"user_status":"C"}
                    referred_count = Referral.objects.filter(referrer = referred_user.referrer, user_status="C").count()
                    if referred_count >= 2: #first 2 referral for free session
                        referral_data["reward_points"] = 50

                    print("referral_data", referral_data)
                    serializer = ReferralSerializer(referred_user, data=referral_data, partial=True)
                    if serializer.is_valid():
                        instance = serializer.save()
                        print(instance.user_status)
                    else:
                        print("Error in referral update flow - ", serializer.errors)

                success_data =  success_response(message=f"User account verified successfully", code="success", data=user_details)
                return Response(success_data, status=200) 
                # return Response(user_details.datas, status=status.HTTP_201_CREATED)
            else:
                error_data =  error_response(message="Please enter vealid OTP", code="invalid", data={})
                return Response(error_data, status=200) 
                # return Response("Please enter vealid OTP", status=status.HTTP_201_CREATED)
        else:
            error_data =  error_response(message="User account not exist", code="not_found", data={})
            return Response(error_data, status=200) 
            # return Response({"error": "User account not exist"}, status=status.HTTP_400_BAD_REQUEST) 


class SelectLocationView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):        
        select_location = UserSelectLocation.objects.filter(user = request.user.id).order_by("status", "-created_at")[:3]
        if select_location:
            select_location_data = UserSelectLocationSerializer(select_location, many=True).data
            success_data =  success_response(message=f"success", code="success", data=select_location_data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="No location found", code="not_found", data={})
            return Response(error_data, status=200) 
    
    def post(self, request): 
        data = request.data
        data["user"] = request.user.id
        
        if data.get("id", None) :
            select_location = select_location = UserSelectLocation.objects.filter(id = data["id"]).first()
            serializer = UserSelectLocationSerializer(select_location, data={"status":"A"}, partial=True)
        else:
            serializer = UserSelectLocationSerializer(data = data)
        
        if serializer.is_valid():
            instance = serializer.save()
            print("instance -- ", instance)
        else:
            error_data =  error_response(message=serializer.errors, code="error", data={})
            return Response(error_data, status=200)

        UserSelectLocation.objects.filter( ~Q(id=instance.id), user=request.user).update(status='I')
        success_data =  success_response(message=f"success", code="success", data={})   
        return Response(success_data, status=200)
    

    def delete(self, request, id): 
        select_location = UserSelectLocation.objects.filter(id=id, user = request.user).first()
        if select_location:
            if select_location.status == 'A':
                active_location = UserSelectLocation.objects.filter(~Q(id=select_location.id), user = request.user).order_by("-created_at").first()
                active_location.status = 'A'
                active_location.save()
            select_location.delete()
            success_data =  success_response(message=f"success", code="success", data={})
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="No location found", code="not_found", data={})
            return Response(error_data, status=200)
        

class GymView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, gym_id):
        if request.user.is_authenticated and request.user.user_type in ("E", "A", "G"): #if Executive or Admin
            gym_data = Gym.objects.filter(Q(owner=request.user) | Q(created_by=request.user), gym_id=gym_id).first()
        else:
            gym_data = Gym.objects.filter(gym_id=gym_id, status='A').first()
        if gym_data:
            data = GymDetailsSerializer(gym_data).data
            data["favorite"] = False
            if request.user.is_authenticated and GymFavorite.objects.filter(user=request.user, gym_id = data["id"] ).exists():
                data["favorite"] = True
            success_data =  success_response(message=f"success", code="success", data=data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="Gym data not found", code="not_found", data={})
            return Response(error_data, status=200)


class GymCreateView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        gym_input_data = request.data
        user_data = request.user
        gym_id = gym_input_data.get("gym_id", None)
        if not gym_id: #if create time
            if user_data.user_type == "G": #if Gym owner
                owner_data = request.user
            elif user_data.user_type in ("E", "A"): #if Executive or Admin
                data = {}
                email = gym_input_data.get("owner_email")
                mobile_number = gym_input_data.get("owner_mobile_number")
                gym_user_data = CustomUser.objects.filter(Q(mobile_number = mobile_number, mobile_number__isnull=False) | Q(email__iexact = email, email__isnull=False), user_type="G").first()
                if gym_user_data:
                    owner_data = gym_user_data
                else:
                    if not gym_input_data.get("owner_email") and not gym_input_data.get("owner_mobile_number"):
                        error_data =  error_response(message="Owner is required to create gym", code="user_not_found", data={})
                        return Response(error_data, status=200)
                
                    if mobile_number:
                        data["username"] = mobile_number 
                        data["login_type"] = "M" 
                    else:
                        data["username"] = email 
                        data["login_type"] = "E" 
                    data["user_type"] = "G" 
                    serializer = CustomUserSerializer(data=data)
                    if serializer.is_valid():
                        owner_data = serializer.save()
                    else:
                        print(serializer.errors)
                        error_data =  error_response(message=serializer.errors, code="error", data={})
                        return Response(error_data, status=200)
                    
            else:
                error_data =  error_response(message="Invalid user type", code="error", data={})
                return Response(error_data, status=200)
        # print(gym_input_data)
        if hasattr(gym_input_data, "_mutable") and not gym_input_data._mutable and not request.FILES:
            gym_input_data._mutable = True
            # print(gym_input_data)
        
        if gym_id:
            gym_data = Gym.objects.filter(Q(created_by=user_data)|Q(owner=user_data), gym_id=gym_input_data.get("gym_id", None)).first()
            if not gym_data:
                error_data =  error_response(message="Invalid gym", code="error", data={})
                return Response(error_data, status=200)
            elif gym_data.status == 'A':
                error_data =  error_response(message="Gym Already approved, Please contact admin to edit it.", code="error", data={})
                return Response(error_data, status=200)
            
            # print(request.data.getlist('feature_ids'))
            # serializer=GymCreateSerializer(gym_data, data = gym_input_data, partial=True, context={"user_data": user_data})
            serializer = GymOptionsSerializer(instance=gym_data, data=request.data,context={'request': request}, partial=True)
            
        else:
            # serializer=GymCreateSerializer(data=gym_input_data, context={"user_data": user_data})
            serializer = GymOptionsSerializer(data=request.data,context={'request': request, 'owner_data': owner_data})
        
        if serializer.is_valid(raise_exception=True):
            instance = serializer.save()
            gym_data = serializer.data
            
            try:
                # owner_data = request.user
                print("instance -- ", owner_data.email)
                if not gym_id: #send email only create time
                    emails = {"to_email":[owner_data.email]} # to-email and cc-email will add as array
                    param = {"gym_name": gym_data["name"], "city":gym_data["city"], "owner_name":owner_data.first_name+" "+owner_data.last_name, "mobile":owner_data.mobile_number} #all email parameters
                    send_template_email("register_gym", emails, param)
            except Exception as e:
                print("send email for register gym: ",e)

            success_data =  success_response(message=f"success", code="success", data=gym_data)   
            return Response(success_data, status=200)
        else:
            print(serializer.errors)
            error_data =  error_response(message=serializer.errors, code="error", data={})
            return Response(error_data, status=200)



class GymListView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        offset = int(self.request.query_params.get('offset', 0))
        limit = int(self.request.query_params.get('limit', 20))
        data = request.data
        
        user_data = {}
        if request.user.is_authenticated:
            user_data = request.user
        
        print("user_data", user_data)
        # if request.user.is_authenticated:
        #     #get user's current active location
        #     select_location = UserSelectLocation.objects.filter(user = request.user.id, status='A').first()
        #     if not select_location:
        #         error_data =  error_response(message="Please select location", code="not_found", data={})
        #         return Response(error_data, status=200)
            
        #     user_location = (float(select_location.latitude), float(select_location.longitude))

        #     gym_list = Gym.objects.filter(~Q(latitude=None), ~Q(longitude=None), status='A', city__iexact=select_location.city)
        # else:    
        if not data["latitude"] and data["longitude"]:
            error_data =  error_response(message="Please select location", code="not_found", data={})
            return Response(error_data, status=200)
        user_location = (float(data["latitude"]), float(data["longitude"]))

        # gym_list = Gym.objects.filter(~Q(latitude=None), ~Q(longitude=None), status='A', city__iexact=data["city"])
        gym_list = Gym.objects.filter(~Q(latitude=None), ~Q(longitude=None), status='A')

        # # city filter 
        # gym_list = gym_list.filter(city__iexact=data["city"])
        
        # If request asks for favorite gyms only
        if data.get("favorite") == True and user_data !={}:
            gym_list = gym_list.filter(favorited_users__user=user_data)
        
        #if passing premium_type filter - plan
        if data.get("type", None):
            gym_list = gym_list.filter(premium_type=data["type"])

        #if search gym name based
        if data.get("search_text", None):
            gym_list = gym_list.filter(name__icontains=data["search_text"])

        gym_with_distance = []

        for gym in gym_list:
            gym_location = (float(gym.latitude), float(gym.longitude))
            distance_km = geodesic(user_location, gym_location).km
            gym.distance = round(distance_km, 2)
            gym_with_distance.append(gym)

            print(gym.distance)

        # Sort by distance
        sorted_gyms = sorted(gym_with_distance, key=lambda x: x.distance)

        print(sorted_gyms)

        # Pagination
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))
        paginated = sorted_gyms[offset:offset + limit]

        
        serializer = GymListSerializer(paginated, many=True, context={"user": user_data})
        # print(serializer.data)
        
        success_data =  success_response(message=f"success", code="success", data=serializer.data)
        return Response(success_data, status=200)
    


class OwnerGymListView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        offset = int(self.request.query_params.get('offset', 0))
        limit = int(self.request.query_params.get('limit', 20))
        page_type = self.request.query_params.get('page', 'L')
        data = request.data
       
        user_data = request.user

        # gym_list = Gym.objects.filter(~Q(latitude=None), ~Q(longitude=None), status='A', city__iexact=data["city"])
        gym_list = Gym.objects.filter(Q(owner=user_data) | Q(created_by=user_data)).order_by("-created_at")

        if page_type == 'D':
            gym_list = gym_list[0:3]

        #if passing premium_type filter - plan
        if data.get("search_text", None): 
            gym_list = gym_list.filter(name__icontains=data["search_text"])

        # Pagination
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))
        paginated = gym_list[offset:offset + limit]

        
        serializer = GymListSerializer(paginated, many=True, context={"user": user_data})
        
        success_data =  success_response(message=f"success", code="success", data=serializer.data)
        return Response(success_data, status=200)


class GymNameListView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        page_type = self.request.query_params.get('page', 'L')
        user_data = request.user

        # gym_list = Gym.objects.filter(~Q(latitude=None), ~Q(longitude=None), status='A', city__iexact=data["city"])
        gym_list = Gym.objects.filter(Q(owner=user_data) | Q(created_by=user_data)).order_by("-created_at")
        if gym_list:
            if page_type == "D":
                gym_list = gym_list[0:3]

            serializer = GymNameListSerializer(gym_list, many=True)
            
            success_data =  success_response(message=f"success", code="success", data=serializer.data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="No gym found", code="not_found", data={})
            return Response(error_data, status=200) 
   

class DashboardView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscription_data = {}
        subscription_data = get_count_data(request.user.id)
        print("subscription_data - ",subscription_data)

        subscription_data["activity_count"] = subscription_data.pop("session_count", 0)
        subscription_data["expires_days"] = max((subscription_data.get("expire_on", date.today()) - date.today()).days, 0)

        subscription_data["last_activity"] = get_last_activity(request.user.id)

        success_data =  success_response(message=f"success", code="success", data=subscription_data)
        return Response(success_data, status=200)

        # else:
        #     error_data =  error_response(message="No data found", code="not_found", data={})
        #     return Response(error_data, status=200)

class ExecutiveDashboardView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = {}
        now = timezone.now()
        user_data = request.user
        # full_counts = Gym.objects.aggregate(
        #                 pending=Count('id', filter=Q(status='P')),
        #                 approved=Count('id', filter=Q(status='A')),
        #                 rejected=Count('id', filter=Q(status='R')),
        #                 total=Count('id')
        #             )
        
        month_counts = Gym.objects.filter(
                        created_by = user_data,
                        created_at__year=now.year,
                        created_at__month=now.month).values('status').annotate(total=Count('id')).order_by('status')
        
        full_counts = Gym.objects.filter(created_by = user_data).values('status').annotate(total=Count('id')).order_by('status')

        month_total_counts = Gym.objects.filter(created_by = user_data,
                                                created_at__year=now.year,
                                                created_at__month=now.month).count()

        total_counts = Gym.objects.filter(created_by = user_data).count()

        data["month_counts"] = month_counts     
        data["month_total_counts"] = month_total_counts   
        data["full_counts"] = full_counts       
        data["total_counts"] = total_counts       

        success_data =  success_response(message=f"success", code="success", data=data)
        return Response(success_data, status=200)

class GymDashboardView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = {}
        now = timezone.now()
        user_data = request.user
    
        queryset = GymAccessLog.objects.filter(gym__owner=user_data)

        data = queryset.aggregate(
            # 💰 Full totals
            full_total_amount=Sum('amount'),
            processed_total_amount=Sum('amount', filter=Q(settled_status='PR')), #all procressed amount
            pending_total_amount=Sum('amount', filter=~Q(settled_status='PR')),   #all pending amount (include inprocess status)

            # 📅 This month total
            month_total_amount=Sum(
                'amount',
                filter=Q(access_date__year=now.year,
                         access_date__month=now.month)
            ),

            # 📊 Sessions
            month_session=Count('id', filter=Q(access_date__year=now.year, access_date__month=now.month)),

            # 👤 Unique users
            month_unique_user=Count('user', distinct=True, filter=Q(access_date__year=now.year, access_date__month=now.month)),
        )

        # Replace None with 0
        for key, value in data.items():
            if value is None:
                data[key] = 0     

        success_data =  success_response(message=f"success", code="success", data=data)
        return Response(success_data, status=200)


class ReviewView(APIView):
    
    def get(self, request):  
        gym_id = request.query_params.get('gym_id', None) 
        page_type = request.query_params.get('page_type', None)  # g - gym details page , 
        gym_data = {}

        if page_type == 'g':
            review_data = GymReview.objects.filter(gym__gym_id = gym_id, status='A').order_by("-created_at")[:1]
        else:
            review_data = GymReview.objects.filter(gym__gym_id = gym_id, status='A').select_related('gym').order_by("-created_at")
        if review_data:
            serializer = GymReviewSerializer(review_data, many=True).data
            total_average = GymReview.objects.filter(gym__gym_id=gym_id, status='A').aggregate(
                total=Count('id'),
                average=Avg('rating')
            )
            average_rating = round(total_average.pop("average", 0.0), 1)
            total_average["average"] = average_rating
            if not page_type == 'g':
                # gym_data["name"] = review_data[0].gym.name
                # gym_data["city"] = review_data[0].gym.city
                # gym_data["state"] = review_data[0].gym.state
                gym_data = gym_response(review_data[0].gym)
                if review_data[0].gym.profile_icon:
                    gym_data["profile_icon"] = review_data[0].gym.profile_icon.url

            extra_data = total_average
            extra_data["gym"] = gym_data
            success_data =  success_response(message=f"success", code="success", data=serializer, extra_data = total_average)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="No reviews found", code="not_found", data={})
            return Response(error_data, status=200) 
        
    
    def post(self, request): 
        authentication_classes = [authentication.TokenAuthentication]
        permission_classes = [permissions.IsAuthenticated]

        data = request.data
        data["user"] = request.user.id
        review_id = data.get("review_id", None)
        if review_id:
            review_data = GymReview.objects.filter(id = review_id, user=request.user).first()
            if review_data:
                serializer = GymReviewSerializer(review_data, data=data, partial=True)
            else:
                error_data =  error_response(message="No review found", code="not_found", data={})
                return Response(error_data, status=200)
        else:
            serializer = GymReviewSerializer(data = data)
        if serializer.is_valid():
            instance = serializer.save()
            #connect session review
            session_id = data.get("session_id", None)
            if session_id and not review_id:
                gym_session = GymAccessLog.objects.filter(id = int(session_id)).first()
                if gym_session:
                    gym_session.review_id = instance.id
                    gym_session.save()
                
            success_data =  success_response(message=f"success", code="success", data=serializer.data)   
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message=serializer.errors, code="error", data={})
            return Response(error_data, status=200)
    

    def delete(self, request, id): 
        authentication_classes = [authentication.TokenAuthentication]
        permission_classes = [permissions.IsAuthenticated]

        review_data = GymReview.objects.filter(id= id, user = request.user).first()
        if review_data:
            review_data.delete()
            success_data =  success_response(message=f"Review removed successfully", code="success", data={})
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="No review found", code="not_found", data={})
            return Response(error_data, status=200)
        

class ReviewDetailtView(APIView):
    def get(self, request, id):  
        review_data = GymReview.objects.filter(id= id, user = request.user).first()
        if review_data:
            serializer = GymReviewSerializer(review_data).data
            success_data =  success_response(message=f"success", code="success", data=serializer)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="No reviews found", code="not_found", data={})
            return Response(error_data, status=200) 


class FavoritesGymView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            user_data = request.user
            if data["action"] == "A":
                # serializer = GymFavoriteSerializer(data={"user":user_data.id, "gym":data["gym"]})
                favorite, created = GymFavorite.objects.get_or_create(user=user_data, gym_id=data["gym"])
                # if serializer.is_valid():
                # instance = serializer.save()
                success_data =  success_response(message=f"Added to favorites", code="success", data={})
                return Response(success_data, status=200)
                # else:
                #     error_data =  error_response(message=serializer.errors, code="error", data={})
                #     return Response(error_data, status=200)
            elif data["action"] == "D":
                favorites_data = GymFavorite.objects.filter(user=user_data, gym_id=data["gym"]).first()
                if favorites_data:
                    favorites_data.delete()
                    success_data =  success_response(message=f"Removed successfully", code="success", data={})
                return Response(success_data, status=200)
        except Exception as e:
            print("FavoritesGymView: ",e)
            error_data =  error_response(message="Something went wrong. Please try again.", code="error", data={})
            return Response(error_data, status=200) 


class HealthCheckView(APIView):
    def get(self, request):
        success_data =  success_response(message=f"success", code="success", data={})
        return Response(success_data, status=200)
    

class ReferralView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        extra_data = {"total_referrals": 0, "total_reward_points": 0}
        try:  
            user_data = request.user
            referral_data = Referral.objects.filter(referrer = user_data)
            if referral_data:
                aggregates = referral_data.aggregate(
                    total_referrals=Count('id'),
                    total_reward_points=Sum('reward_points')
                )

                extra_data = {"total_referrals": aggregates["total_referrals"], "total_reward_points": aggregates["total_reward_points"] or 0}
            serializer_data = ReferralSerializer(referral_data, many=True).data
            success_data =  success_response(message=f"success", code="success", data=serializer_data, extra_data = extra_data)
            return Response(success_data, status=200)
        except Exception as e:
            print("Referral error: ",e)
            error_data =  error_response(message="Something went wrong. Please try again.", code="error", data={})
            return Response(error_data, status=200)


class ReferralCountView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        try:  
            user_data = request.user
            referral_data = Referral.objects.filter(referrer = user_data, user_status="C")
            total_count = referral_data.count()

            free_session_request = FreeSessionRequest.objects.filter(user = user_data).order_by("-created_at").first()

            # total_reward_points = referral_data.aggregate(total_points=Sum('reward_points'))['total_points'] or 0
            data = {"total_count":total_count
                    # , "total_points":total_reward_points
                    }
            if free_session_request:
                data["free_session_request"] = free_session_request.status

            success_data =  success_response(message=f"success", code="success", data=data)
            return Response(success_data, status=200)
        except Exception as e:
            print("Referral error: ",e)
            error_data =  error_response(message="Something went wrong. Please try again.", code="error", data={})
            return Response(error_data, status=200)
    
class FreeSessionRequestView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        try:  
            user_data = request.user
            referral_count = Referral.objects.filter(referrer = user_data, user_status='C').count()
            request_count = FreeSessionRequest.objects.filter(user=user_data, status='A').count()
            if request_count <=0 and referral_count >=2:
                FreeSessionRequest.objects.create(user=user_data)
                success_data =  success_response(message=f"success", code="success", data={})
                return Response(success_data, status=200)
            else:
                error_data =  error_response(message="Error in referral flow, Please contact admin", code="error", data={})
                return Response(error_data, status=200)
        except Exception as e:
            print("Referral error: ",e)
            error_data =  error_response(message="Something went wrong. Please try again.", code="error", data={})
            return Response(error_data, status=200)
    