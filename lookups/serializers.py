import re
from rest_framework import serializers
from .models import WorkoutType, ExerciseName, GymFeature, ContactMessage, PartnerLead
from FitnessApp.utils.media import thumbnail_url

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

class ExerciseNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseName
        fields = ['id', 'name']

class GymFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymFeature
        fields = ['id', 'name', 'icon', 'details']

    icon = serializers.ImageField(use_url=True, required=False, allow_null=True)

    def to_representation(self, instance):
        # Feature icons only ever render as small pills/badges (biggest use is
        # a 20x20px icon on the gym-detail page) — every caller was getting
        # the full-resolution original from Cloudinary for that.
        data = super().to_representation(instance)
        if data.get('icon'):
            data['icon'] = thumbnail_url(data['icon'], width=80, height=80)
        return data


def _clean_mobile(value):
    digits = re.sub(r'\D', '', value or '')
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    if len(digits) != 10 or digits[0] not in '6789':
        raise serializers.ValidationError("Enter a valid 10-digit mobile number.")
    return digits


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'category', 'message']

    def validate_name(self, value):
        value = (value or '').strip()
        if len(value) < 2:
            raise serializers.ValidationError("Please enter your name.")
        return value

    def validate_message(self, value):
        value = (value or '').strip()
        if len(value) < 10:
            raise serializers.ValidationError("Please add a few more details (at least 10 characters).")
        return value[:5000]

    def validate_phone(self, value):
        value = (value or '').strip()
        return value[:20]


class PartnerLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerLead
        fields = ['gym_name', 'owner_name', 'mobile', 'email', 'city', 'message']

    def validate_gym_name(self, value):
        value = (value or '').strip()
        if len(value) < 2:
            raise serializers.ValidationError("Please enter your gym's name.")
        return value

    def validate_owner_name(self, value):
        value = (value or '').strip()
        if len(value) < 2:
            raise serializers.ValidationError("Please enter the owner's name.")
        return value

    def validate_city(self, value):
        value = (value or '').strip()
        if len(value) < 2:
            raise serializers.ValidationError("Please enter your city.")
        return value

    def validate_mobile(self, value):
        return _clean_mobile(value)

    def validate_message(self, value):
        return (value or '').strip()[:5000]