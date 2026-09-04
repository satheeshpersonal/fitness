from decimal import Decimal
from rest_framework import serializers
from .models import UserSubscriptionHistory, SubscriptionPlan, PlanDetails, UserSubscription

class SubscriptionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscriptionHistory
        fields = '__all__'  # include all fields
        read_only_fields = ['subscription_id', 'order_id', 'created_at']  # only these are read-only
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['plan'] = {"id": instance.plan.id, "name": instance.plan.name, "plan_type":instance.plan.plan_type}
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

        # price        = list / MRP price (struck out on the card when discounted)
        # final_price  = what the user actually pays per unit (price - price_discount%)
        # discount_percent is a flat % off, matching get_subscription_data()
        list_price = instance.price or Decimal("0")
        discount_percent = instance.price_discount or Decimal("0")
        final_price = (list_price - (list_price * discount_percent / 100)).quantize(Decimal("0.01"))

        data["price"] = format(list_price.normalize(), 'f')
        data["final_price"] = format(final_price.normalize(), 'f')
        data["discount_percent"] = format(discount_percent.normalize(), 'f')
        data["has_discount"] = discount_percent > 0

        return data