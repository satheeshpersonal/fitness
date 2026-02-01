from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication
from FitnessApp.utils.response import success_response, error_response
from django.utils import timezone
from datetime import timedelta
from decouple import config
from .models import SubscriptionPlan, UserSubscriptionHistory, DicountCoupon
from .serializers import SubscriptionHistorySerializer, SubscriptionPlanSerializer
from .functions import get_subscription_data, razorpay_creat_order, verify_razorpay_event
# from django.views.decorators.csrf import csrf_exempt
# Create your views here.



class PlanView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """

    def get(self, request):
        premim_type = request.query_params.get('premim_type', None) 
        filters = {}
        if premim_type:
            filters["premim_type"] = premim_type
        plan_all = SubscriptionPlan.objects.filter(**filters, status = 'A').order_by("position")
        plan_all_data = SubscriptionPlanSerializer(plan_all, many=True).data
        success_data =  success_response(message=f"success", code="success", data=plan_all_data)
        return Response(success_data, status=200)


class ValidateCoupon(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, coupon_code):
        coupon_data = DicountCoupon.objects.filter(coupon_code=coupon_code).first()
        if coupon_data:
            # print(coupon_data.coupon_code)
            success_data =  success_response(message=f"success", code="success", data={"coupon_code": coupon_data.coupon_code, "percentage": coupon_data.percentage})
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="Invalid coupon code", code="not_found", data={})
            return Response(error_data, status=200) 
        

class SubscriptionView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscription_history = UserSubscriptionHistory.objects.filter(user = request.user, payment_status__in = ['S', 'E']).order_by("-created_at")
        subscription_history_data = SubscriptionHistorySerializer(subscription_history, many=True).data
        success_data =  success_response(message=f"success", code="success", data=subscription_history_data)
        return Response(success_data, status=200)
        
    def post(self, request): #Register User
        # print(request.data)
        request_data = request.data
        user_data = request.user

        plan_data = SubscriptionPlan.objects.filter(id = request_data["plan"], status='A').first()
        if not plan_data:
            error_data =  error_response(message="No plans available, Please select valid plan", code="not_found", data={})
            return Response(error_data, status=200) 
        
        # if plan_data.plan_type == "D":
        #     user_plan_data["sessions_count"] = request_data.get("sessions_count", 2)
        # else:
        #     user_plan_data["sessions_count"] = plan_data.session_count

        # user_plan_data = {}
        # user_plan_data["plan"] = plan_data
        # user_plan_data["per_session_price"] = plan_data.price
        # user_plan_data["currency"] = plan_data.currency
        # user_plan_data["duration_in_days"] = plan_data.duration_in_days
        # user_plan_data["expire_on"] = timezone.now().date()+timedelta(days=plan_data.duration_in_days)
        # user_plan_data["total_session_price"] = user_plan_data["sessions_count"]*plan_data.price
        # user_plan_data["discount_amount"] = 0
        # user_plan_data["tax"] = 0
        # user_plan_data["total_paid"] = user_plan_data["total_session_price"]+user_plan_data["discount_amount"]+user_plan_data["tax"]

        # user_plan_data["user"] = user_data

        user_plan_data = get_subscription_data(user_data, plan_data, request_data) # get plan data with price calculation
        
        user_plan_data["plan"] = plan_data.id
        user_plan_data["user"] = user_data.id
        
        # razorpay_order_id = razorpay_creat_order(user_plan_data)
        # user_plan_data["razorpay_order_id"] = razorpay_order_id
        serializer = SubscriptionHistorySerializer(data=user_plan_data)
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            success_data =  success_response(message=f"Enrollment initiated successfully.", code="success", data=response_data)
            return Response(success_data, status=200) 

        error_data =  error_response(message=serializer.errors, code="error", data={})
        return Response(error_data, status=200)
    

class SubscriptionDetailsView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        subscription_history = UserSubscriptionHistory.objects.filter(user = request.user, order_id=order_id).first()
        subscription_history_data = SubscriptionHistorySerializer(subscription_history).data
        success_data =  success_response(message=f"success", code="success", data=subscription_history_data)
        return Response(success_data, status=200)
        
    def patch(self, request, order_id): #Register User
        # print(request.data)
        request_data = request.data
        user_data = request.user

        subscription_history = UserSubscriptionHistory.objects.filter(user = request.user, order_id=order_id).first()
        if not subscription_history:
            error_data =  error_response(message="No orders available, Please select valid order", code="not_found", data={})
            return Response(error_data, status=200) 

        plan_data = SubscriptionPlan.objects.filter(id = subscription_history.plan.id, status='A').first()
        if not plan_data:
            error_data =  error_response(message="No plans available, Please select valid plan", code="not_found", data={})
            return Response(error_data, status=200) 

        if request_data.get("coupon", None):
            coupon_data = DicountCoupon.objects.filter(coupon_code=request_data["coupon"]).first()
            if coupon_data:
                request_data["coupon"] = coupon_data.coupon_code
                request_data["coupon_discount_percent"] = coupon_data.percentage
        else:
            request_data["coupon"] = None

        user_plan_data = get_subscription_data(user_data, plan_data, request_data) # get plan data with price calculation
        
        user_plan_data["plan"] = plan_data.id
        user_plan_data["user"] = user_data.id
        
        razorpay_order_id = razorpay_creat_order(user_plan_data)
        user_plan_data["razorpay_order_id"] = razorpay_order_id
        serializer = SubscriptionHistorySerializer(subscription_history, data=user_plan_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            response_data["razorpay_key"] = config('RAZORPAY_API_KEY')
            success_data =  success_response(message=f"Enrollment udates successfully.", code="success", data=response_data)
            return Response(success_data, status=200) 

        error_data =  error_response(message=serializer.errors, code="error", data={})
        return Response(error_data, status=200)
    
    
# @csrf_exempt
class RazorpayWebhook(APIView):
    def post(self, request): 
        # try:  
        if 1==1:      
            razorpay_event_data = verify_razorpay_event(request)
            if razorpay_event_data:
                # Update order status
                order = UserSubscriptionHistory.objects.filter(razorpay_order_id=razorpay_event_data["order_id"]).first()
                if order:
                    order.razorpay_payment_id = razorpay_event_data["payment_id"]

                    if razorpay_event_data["event"] == 'payment.captured':
                        order.payment_status = 'S'
                    elif razorpay_event_data["event"] == 'payment.failed':
                        order.payment_status = 'F'
                        order.error_code = razorpay_event_data["error_code"]
                        order.error_description = razorpay_event_data["error_description"]
                    
                    order.save()
                    # Add business logic here, e.g., send email
                
            # Handle other events as needed, e.g., payment.failed
        
        # except Exception as e:
        #     print("The razorpay_webhook error : ",e)
        
        success_data =  success_response(message=f"Webhook called successfully.", code="success", data={})
        return Response(success_data, status=200) 
        