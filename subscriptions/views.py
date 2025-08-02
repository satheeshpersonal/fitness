from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication
from FitnessApp.utils.response import success_response, error_response
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, UserSubscriptionHistory
from .serializers import SubscriptionHistorySerializer, SubscriptionPlanSerializer
from .functions import get_subscription_data
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

        serializer = SubscriptionHistorySerializer(data=user_plan_data)
        if serializer.is_valid():
            serializer.save()

            success_data =  success_response(message=f"Enrollment initiated successfully.", code="success", data=serializer.data)
            return Response(success_data, status=200) 

        error_data =  error_response(message=serializer.errors, code="error", data={})
        return Response(error_data, status=200) 