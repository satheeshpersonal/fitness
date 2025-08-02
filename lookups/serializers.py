from rest_framework import serializers
from .models import WorkoutType

class WorkoutTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutType
        # fields = '__all__'  # include all fields
        fields = ['id', 'name']
        # read_only_fields = ['subscription_id', 'order_id', 'created_at']  # only these are read-only
    
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data['plan'] = instance.plan.name
#         data['premim_type'] = instance.plan.get_premim_type_display()

#         return data