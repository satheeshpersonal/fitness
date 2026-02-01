from rest_framework import serializers
from .models import CustomUser, UserSelectLocation, GymMedia, GymEquipment, Gym, GymTiming, GymReview, GymFavorite
from lookups.models import GymFeature

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'mobile_number', 'status', 'user_type', 'login_type', 'profile_completed', 'profile_icon', 'address', 'new_to_gym', 'height', 'weight', 'dob', 'gender']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'mobile_number', 'profile_icon', 'new_to_gym', 'height', 'weight', 'dob', 'gender', 'address', 'country', 'state', 'city', 'profile_completed']


class UserSelectLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSelectLocation
        fields = '__all__'
        # fields = ['user', 'address', 'latitude', 'longitude', 'status', 'created_at']
        read_only_fields = ['created_at']


class GymMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymMedia
        fields = ['name', 'media', 'description']

class GymEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymEquipment
        fields = ['category', 'description', 'icon']

class GymFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymFeature
        fields = ['name', 'icon', 'details']

class GymTimingSerializer(serializers.ModelSerializer):
    day = serializers.SerializerMethodField()
    
    class Meta:
        model = GymTiming
        fields = ['day', 'morning_start', 'morning_end', 'evening_start', 'evening_end']
    
    def get_day(self, obj):
        return obj.get_day_display()

class GymOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'mobile_number']


class GymDetailsSerializer(serializers.ModelSerializer):
    media = serializers.SerializerMethodField()
    feature = serializers.SerializerMethodField()
    equipment = serializers.SerializerMethodField()
    gymtiming = serializers.SerializerMethodField()
    gymowner = serializers.SerializerMethodField()
    # rating = serializers.SerializerMethodField()
    # distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Gym
        fields = ['id', 'gym_id', 'name', 'description', 'address', 'city', 'state', 'latitude', 'longitude', 'premium_type', 'media', 'feature', 'equipment', 'gymtiming', 'gymowner' #distance_km, 'rating'
        ]

    def get_media(self, obj):
        return GymMediaSerializer(obj.gymmedia_set.all().order_by("position"), many=True).data
    
    def get_feature(self, obj):
        return GymFeatureSerializer(obj.feature.filter(status='A').order_by("position")[:6], many=True).data
    
    def get_equipment(self, obj):
        return GymEquipmentSerializer(obj.gymequipment_set.filter(status='A').order_by("position")[:6], many=True).data
    
    def get_gymtiming(self, obj):
        return GymTimingSerializer(obj.gymtiming_set.filter(status='A').order_by("position"), many=True).data
    
    def get_gymowner(self, obj):
        return GymOwnerSerializer(obj.owner).data

    # def get_rating(self, obj):
    #     reviews = obj.gymreview_set.all()
    #     if reviews:
    #         return round(sum(r.rating for r in reviews) / len(reviews), 1)
    #     return 0

    # def get_distance_km(self, obj):
    #     user_lat = self.context.get('user_lat')
    #     user_lon = self.context.get('user_lon')
    #     if user_lat and user_lon and obj.latitude and obj.longitude:
    #         from geopy.distance import geodesic
    #         return round(geodesic((user_lat, user_lon), (obj.latitude, obj.longitude)).km, 2)
    #     return None


class GymListSerializer(serializers.ModelSerializer):
    media = serializers.SerializerMethodField()
    feature = serializers.SerializerMethodField()
    gymowner = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    favorites = serializers.SerializerMethodField()
    # distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Gym
        fields = ['id', 'gym_id', 'name', 'description', 'address', 'city', 'state', 'premium_type', 'media', 'feature', 'gymowner', 'distance', 'rating', 'favorites']

    def get_media(self, obj):
        return GymMediaSerializer(obj.gymmedia_set.all().order_by("position"), many=True).data
    
    def get_feature(self, obj):
        return GymFeatureSerializer(obj.feature.filter(status='A').order_by("position"), many=True).data
    
    def get_gymowner(self, obj):
        return GymOwnerSerializer(obj.owner).data

    def get_distance(self, obj):
        return getattr(obj, 'distance', None)
    
    def get_rating(self, obj):
        reviews = obj.gymreview_set.all()
        if reviews:
            total = len(reviews)
            average = round(sum(r.rating for r in reviews) / total, 1)
            return {"average":average, "total":total}

        return {"average":0, "total":0}
    
    def get_favorites(self, obj):
        user = self.context.get("user")
        print("user - ", user)
        if not user or not user.is_authenticated:
            return False

        return GymFavorite.objects.filter(user=user,gym=obj).exists()
    

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'mobile_number', 'profile_icon']


class GymReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymReview
        fields = '__all__'
        read_only_fields = ['created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = UserDetailsSerializer(instance.user).data
        return data
    
class GymFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymFavorite
        fields = '__all__'
        read_only_fields = ['created_at']