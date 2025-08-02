from rest_framework import serializers
from .models import UserSubscriptionHistory, SubscriptionPlan, PlanDetails, UserSubscription

class SubscriptionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscriptionHistory
        fields = '__all__'  # include all fields
        read_only_fields = ['subscription_id', 'order_id', 'created_at']  # only these are read-only
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['plan'] = instance.plan.name
        data['premim_type'] = {"code": instance.plan.premim_type, "value":instance.plan.get_premim_type_display()}

        return data
    
class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = '__all__'  # include all fields
        # read_only_fields = ['expire_on']  # only these are read-only
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['plan_name'] = instance.plan.name
        data['price'] = instance.plan.price
        data['plan_type'] = instance.plan.plan_type
        data['premim_type'] = {"code": instance.plan.premim_type, "value":instance.plan.get_premim_type_display()}

        return data
    

class PlanDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanDetails
        fields = '__all__'  # include all fields


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    plan_details = PlanDetailsSerializer(many=True, read_only=True)
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'  # include all fields
        
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # data['details'] = PlanDetailsSerializer(instance.plan_details.all(), many=True).data

        return data