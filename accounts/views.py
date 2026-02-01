from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication
from .models import CustomUser, UserOTP, UserSelectLocation, Gym, GymFavorite, GymReview
from .serializers import CustomUserSerializer, UserProfileSerializer, UserSelectLocationSerializer, GymDetailsSerializer, GymListSerializer, GymReviewSerializer, GymFavoriteSerializer
from subscriptions.serializers import UserSubscriptionSerializer
from subscriptions.models import UserSubscription
from django.shortcuts import get_object_or_404
from .functions import generte_top, send_otp, gym_response
from django.db.models import Q
from django.utils import timezone
from FitnessApp.utils.response import success_response, error_response
from rest_framework.authtoken.models import Token
from lookups.functions import send_template_email
from geopy.distance import geodesic
from subscriptions.functions import get_count_data
from workouts.functions import get_last_activity
from django.db.models import Avg, Count
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
            data["username"] = email 
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
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            user_obj = serializer.save()
            otp_code = generte_top(user_obj, data["login_type"]) 
            # trigger OTP
            send_otp(mobile_number, email, otp_code, data["login_type"])

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

        required_fields = ['full_name', 'dob', 'gender', 'address']
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


class verifyOTPView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for verify OTP
    """
  
    def post(self, request): #Register User
        # print(request.data)
        data = request.data
        user_name = data.get("user_name", None)
        otp_code = data.get("otp_code", None)

        if not user_name and not otp_code:
            error_data =  error_response(message="User name and OTP required for verfiy account", code="missing_value", data={})
            return Response(error_data, status=200) 
            # return Response({"error": "User name and OTP required for verfiy account"}, status=status.HTTP_400_BAD_REQUEST) 
        
        #check user alredy exist
        user_data = CustomUser.objects.filter(Q(mobile_number = user_name) | Q(email__iexact = user_name)).first()
        if user_data and user_data.status in ["I", "D"]:
            error_data =  error_response(message="Please contact admin", code="login_error", data={})
            return Response(error_data, status=200)
        if user_data:
            user_otp = UserOTP.objects.filter(user = user_data, expire_on__gte = timezone.now()).order_by("-created_at").first()
            if user_otp and user_otp.otp == otp_code:
                if user_data.status == "P":
                    user_data.status = "A"
                    user_data.save(update_fields=["status"])
                    #send welcome email to user if first time verifiy account
                    if user_data.email:
                        send_template_email("Welcome", f"Welcome to the application", [user_data.email]) 
                user_details = CustomUserSerializer(user_data).data
                
                # if user_data.profile_completed: #check Profile status
                # Delete old token if exists
                Token.objects.filter(user=user_data).delete()
                # Create new token
                token = Token.objects.create(user=user_data)
                user_details["token"]=token.key
                user_details["full_name"] = user_details["first_name"]+" "+user_details["last_name"]

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
        
        if data["id"] :
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
    

class DashboardView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscription_data = {}
        subscription_data = get_count_data(request.user.id)

        subscription_data["activity_count"] = subscription_data.pop("session_count", 0)
        subscription_data["expires_days"] = max((subscription_data["expire_on"] - date.today()).days, 0)

        subscription_data["last_activity"] = get_last_activity(request.user.id)

        success_data =  success_response(message=f"success", code="success", data=subscription_data)
        return Response(success_data, status=200)

        # else:
        #     error_data =  error_response(message="No data found", code="not_found", data={})
        #     return Response(error_data, status=200)


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
        serializer = GymReviewSerializer(data = data)
        if serializer.is_valid():
            instance = serializer.save()
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
        # try:
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
        # except Exception as e:
        #     print("FavoritesGymView: ",e)
        #     error_data =  error_response(message="Something went wrong. Please try again.", code="error", data={})
        #     return Response(error_data, status=200) 