from rest_framework import serializers
from .models import CustomUser, UserSelectLocation, GymMedia, GymEquipment, Gym, GymTiming, GymReview, GymFavorite, Referral
from lookups.models import GymFeature
from lookups.serializers import GymFeatureSerializer
import json

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
import sys

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'mobile_number', 'status', 'user_type', 'login_type', 'profile_completed', 'profile_icon', 'address', 'new_to_gym', 'height', 'weight', 'dob', 'gender', 'referral_code', 'ip_country', 'ip_state', 'ip_city']
    
    profile_icon = serializers.ImageField(use_url=True, required=False, allow_null=True)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'mobile_number', 'profile_icon', 'new_to_gym', 'height', 'weight', 'dob', 'gender', 'address', 'country', 'state', 'city', 'profile_completed', 'user_type']

    profile_icon = serializers.ImageField(use_url=True, required=False, allow_null=True)


class UserSelectLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSelectLocation
        fields = '__all__'
        # fields = ['user', 'address', 'latitude', 'longitude', 'status', 'created_at']
        read_only_fields = ['created_at']


class GymMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymMedia
        fields = ['id', 'name', 'media', 'description', 'position']

    media = serializers.ImageField(use_url=True, required=False, allow_null=True)

class GymEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymEquipment
        fields = ['id', 'category', 'description', 'icon', 'position', 'status']
    
    icon = serializers.ImageField(use_url=True, required=False, allow_null=True)

class GymTimingSerializer(serializers.ModelSerializer):
    day_dispaly = serializers.SerializerMethodField()
    
    class Meta:
        model = GymTiming
        fields = ['id', 'day', 'day_dispaly', 'morning_start', 'morning_end', 'evening_start', 'evening_end', 'position', 'status']
    
    def get_day_dispaly(self, obj):
        return obj.get_day_display()

class GymOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'mobile_number', 'email']


class GymCreateSerializer(serializers.ModelSerializer):

    feature = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, allow_empty=True
    )

    equipment = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False, allow_empty=True
    )

    gymtiming = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False, allow_empty=True
    )

    media = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False, allow_empty=True
    )

    class Meta:
        model = Gym
        fields = [
            'gym_id',
            'name',
            'description',
            'profile_icon',
            'address',
            'city',
            'state',
            'country',
            'zip_code',
            'latitude',
            'longitude',
            'premium_type',
            'per_session_cost',
            'currency',
            'feature',
            'equipment',
            'gymtiming',
            'media'
        ]
        read_only_fields = ['gym_id']

    def create(self, validated_data):
        print("create ---", validated_data)
        user = self.context["user_data"]
        gym = Gym.objects.create(owner=user, **validated_data)
        self._handle_nested_fields(gym, validated_data) #function to create data 
        return gym

    def update(self, instance, validated_data):
        print("update ---", **validated_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self._handle_nested_fields(instance, validated_data, is_update=True)  #function to update data  
        return instance


    def _handle_nested_fields(self, instance, validated_data, is_update=False):
        print(validated_data)
        feature_ids = validated_data.pop("feature_ids", [])
        equipment_data = validated_data.pop("equipments", [])
        timing_data = validated_data.pop("timings", [])
        media_data = validated_data.pop("media", [])

        # user = self.context["user_data"]

        # gym = Gym.objects.create(owner=user, **validated_data)

        # Features
        print("feature_ids -- ", feature_ids)
        print("equipment_data -- ", equipment_data)
        print("timing_data -- ", timing_data)
        print("media_data -- ", media_data)
        if feature_ids is not None:
            instance.feature.set(feature_ids)

        # Equipment
        if equipment_data is not None:
            if is_update:
                instance.gymequipment_set.all().delete()
            for eq in equipment_data:
                GymEquipment.objects.create(gym=instance, **eq)

        # Timing
        if timing_data is not None:
            if is_update:
                instance.gymtiming_set.all().delete()
            for timing in timing_data:
                GymTiming.objects.create(gym=instance, **timing)

        # Media
        if media_data is not None:
            if is_update:
                instance.gymmedia_set.all().delete()
            for media in media_data:
                GymMedia.objects.create(gym=instance, **media)

        # return gym


from rest_framework import serializers
from django.db import transaction
from .models import Gym, GymMedia, GymTiming, GymEquipment, GymFeature


class GymOptionsSerializer(serializers.ModelSerializer):
    # ---------- Main Fields ----------
    # media = GymMediaSerializer(many=True, required=False)
    # timings = GymTimingSerializer(many=True, required=False)
    # equipment = GymEquipmentSerializer(many=True, required=False)
    # feature = serializers.PrimaryKeyRelatedField(
    #     queryset=GymFeature.objects.all(),
    #     many=True,
    #     required=False
    # )
    feature = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, allow_empty=True
    )

    class Meta:
        model = Gym
        fields = '__all__'
        read_only_fields = ['owner', 'verified_by', 'verified_at']

    def convert_to_webp(self, image):
        img = Image.open(image)

        output = BytesIO()
        img.save(output, format='WEBP', quality=85)
        output.seek(0)

        return InMemoryUploadedFile(
            output,
            'ImageField',
            f"{image.name.split('.')[0]}.webp",
            'image/webp',
            sys.getsizeof(output),
            None
        )


    # ---------- CREATE ----------
    @transaction.atomic
    def create(self, validated_data):
        print("Ceate -- ")
        request = self.context.get('request')
        owner_data = self.context.get('owner_data')

         # 🔹 convert image if provided
        profile_image = validated_data.get('profile_icon')
        if profile_image:
            validated_data['profile_icon'] = self.convert_to_webp(profile_image)
            
        gym = Gym.objects.create(
            owner=owner_data,
            created_by=request.user,
            **validated_data
        )
        
        return gym


    # ---------- UPDATE ----------
    @transaction.atomic
    def update(self, instance, validated_data):
        # owner_data = self.context.get('owner_data')
        request = self.context.get("request")

        validated_data.pop("feature", None)
        
        # 🔹 convert image if provided
        profile_image = validated_data.get("profile_icon")
        if profile_image:
            validated_data["profile_icon"] = self.convert_to_webp(profile_image)

        # Update simple fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        self._handle_nested_data(instance, request)

        return instance


    # ---------- GENERIC NESTED HANDLER ----------
    # ===============================
    # HANDLE ALL NESTED LOGIC HERE
    # ===============================
    def _handle_nested_data(self, gym, request):

        # -------------------------
        # FEATURE IDS (ManyToMany)
        # -------------------------
        feature_ids = []
        media_dict = {}
        timings_dict = {}
        equipment_dict = {}
        for key in request.data.keys():
            if key.startswith("feature_ids["): # for gym feature
                feature_ids.append(request.data.get(key))
            # media list
            if key.startswith("media["):
                # Extract index
                index = key.split("[")[1].split("]")[0]
                if index not in media_dict:
                    media_dict[index] = {}
                # Extract field name
                field_name = key.split("][")[1].replace("]", "")
                if "file" in field_name:
                    media_dict[index]["file"] = request.data.get(key)
                else:
                    media_dict[index][field_name] = request.data.get(key)
            # timings list
            elif key.startswith("timings["):
                # Extract index
                index = key.split("[")[1].split("]")[0]
                if index not in timings_dict:
                    timings_dict[index] = {}
                # Extract field name
                field_name = key.split("][")[1].replace("]", "")
                if request.data.get(key) != 'null' and request.data.get(key) != '':
                    timings_dict[index][field_name] = request.data.get(key)
            # equipment list
            elif key.startswith("equipments["):
                # Extract index
                index = key.split("[")[1].split("]")[0]
                if index not in equipment_dict:
                    equipment_dict[index] = {}
                # Extract field name
                field_name = key.split("][")[1].replace("]", "")
                equipment_dict[index][field_name] = request.data.get(key)

        # -------------------------
        # GYM features
        # -------------------------
        if feature_ids:
            # feature_ids = json.loads(feature_ids)
            gym.feature.set(feature_ids)

        # -------------------------
        # MEDIA
        # -------------------------
        print("media_data - ", media_dict)
        if media_dict:
            existing_ids = []

            for index in media_dict:
                item = media_dict[index]
                media_id = item.get("id")
                gym_image = item.get("file")
                if gym_image:
                    gym_image = self.convert_to_webp(gym_image)

                if media_id:
                    media_obj = GymMedia.objects.get(id=media_id, gym=gym)
                    media_obj.name = item.get("name", media_obj.name)
                    media_obj.description = item.get("description", media_obj.description)
                    media_obj.position = item.get("position", media_obj.position)

                    if gym_image:
                        media_obj.media = gym_image

                    media_obj.save()
                    existing_ids.append(media_obj.id)

                else:
                    new_media = GymMedia.objects.create(
                        gym=gym,
                        name=item.get("name"),
                        description=item.get("description"),
                        position=item.get("position", 1),
                        media=gym_image
                    )
                    existing_ids.append(new_media.id)

            # Delete removed media
            GymMedia.objects.filter(gym=gym).exclude(id__in=existing_ids).delete()

        # -------------------------
        # TIMINGS (JSON ONLY)
        # -------------------------
        print("timings_dict - ", timings_dict)
        if timings_dict:
            existing_ids = []

            for index in timings_dict:
                item = timings_dict[index]
                timing_id = item.get("id")

                if timing_id:
                    timing_obj = GymTiming.objects.get(id=timing_id, gym=gym)
                    for key, value in item.items():
                        setattr(timing_obj, key, value)
                    timing_obj.save()
                    existing_ids.append(timing_obj.id)
                else:
                    print
                    new_obj = GymTiming.objects.create(gym=gym, **item)
                    existing_ids.append(new_obj.id)

            GymTiming.objects.filter(gym=gym).exclude(id__in=existing_ids).delete()

        # -------------------------
        # EQUIPMENT (JSON ONLY)
        # -------------------------
        if equipment_dict:
            existing_ids = []

            for index in equipment_dict:
                item = equipment_dict[index]
                equip_id = item.get("id")

                if equip_id:
                    equip_obj = GymEquipment.objects.get(id=equip_id, gym=gym)
                    for key, value in item.items():
                        setattr(equip_obj, key, value)
                    equip_obj.save()
                    existing_ids.append(equip_obj.id)
                else:
                    new_obj = GymEquipment.objects.create(gym=gym, **item)
                    existing_ids.append(new_obj.id)

            GymEquipment.objects.filter(gym=gym).exclude(id__in=existing_ids).delete()


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
        fields = ['id', 'gym_id', 'profile_icon', 'name', 'description', 'address', 'city', 'state', 'country', 'zip_code', 'latitude', 'longitude', 'premium_type', 'media', 'feature', 'equipment', 'gymtiming', 'gymowner', 'status', 'per_session_cost', 'currency' #distance_km, 'rating'
        ]

    profile_icon = serializers.ImageField(use_url=True, required=False, allow_null=True)

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
        fields = ['id', 'gym_id', 'name', 'description', 'address', 'city', 'state', 'premium_type', 'media', 'feature', 'gymowner', 'distance', 'rating', 'favorites', 'status']

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


class GymNameListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Gym
        fields = ['id', 'gym_id', 'profile_icon', 'name', 'address', 'city', 'state', 'premium_type', 'status']
  

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'mobile_number', 'profile_icon', 'email']
    
    profile_icon = serializers.ImageField(use_url=True, required=False, allow_null=True)


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

class ReferralSerializer(serializers.ModelSerializer):
    user_status_display = serializers.SerializerMethodField()
    user_data= serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = '__all__'
        read_only_fields = ['created_at']

    def get_user_status_display(self, obj):
        return {
            "code": obj.user_status,
            "label": obj.get_user_status_display()
        }
    
    def get_user_data(self, obj):
        return UserDetailsSerializer(obj.referred_user).data