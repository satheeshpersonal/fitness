from django.shortcuts import render
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication
from decouple import config
import json
import logging
from FitnessApp.utils.response import success_response, error_response
from FitnessApp.utils import appcache
from .models import WorkoutType, ExerciseName, GymFeature
from .serializers import (
    WorkoutTypeSerializer,
    ExerciseNameSerializer,
    GymFeatureSerializer,
    ContactMessageSerializer,
    PartnerLeadSerializer,
)
from .functions import client_ip, notify_contact_message, notify_partner_lead

logger = logging.getLogger(__name__)


def _rate_limited(request, scope, limit=5, window=60 * 60):
    """
    Lightweight per-IP throttle for the public website forms. Backed by the
    default cache (per-process LocMemCache) — enough to blunt casual abuse;
    real protection would need a shared store + captcha.
    """
    key = f"formrl:{scope}:{client_ip(request) or 'unknown'}"
    count = cache.get(key)
    if count is None:
        cache.set(key, 1, window)
        return False
    if count >= limit:
        return True
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, count + 1, window)
    return False


# Create your views here.
class WorkoutTypeView(APIView):
    """Active workout types. Rarely changes → read-through cached."""

    def get(self, request):
        def build():
            qs = WorkoutType.objects.filter(status="A").order_by("position")
            return WorkoutTypeSerializer(qs, many=True).data

        data = appcache.get_or_set(appcache.WORKOUT_TYPES_KEY, build, appcache.LOOKUP_TTL)
        return Response(success_response(message="success", code="success", data=data), status=200)


class ExerciseNameView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """

    def get(self, request):
        workout_types = request.query_params.get('workout_types', None)
        exercise_name_data = []
        if workout_types:
            workout_types_list = []
            for wt in workout_types.split(','):
                wt = wt.strip()
                if wt.isdigit():
                    workout_types_list.append(int(wt))
            if workout_types_list:
                exercise_name = ExerciseName.objects.filter(workout_type__in=workout_types_list, status = 'A').order_by("workout_type__position","position")
                exercise_name_data = ExerciseNameSerializer(exercise_name, many=True).data
        success_data =  success_response(message=f"success", code="success", data=exercise_name_data)
        return Response(success_data, status=200)


class GymFeatureView(APIView):
    """Active gym features. Rarely changes → read-through cached."""

    def get(self, request):
        def build():
            qs = GymFeature.objects.filter(status="A").order_by("position")
            return GymFeatureSerializer(qs, many=True).data

        data = appcache.get_or_set(appcache.GYM_FEATURES_KEY, build, appcache.LOOKUP_TTL)
        return Response(success_response(message="success", code="success", data=data), status=200)


class ContactMessageView(APIView):
    """Public — fitzz.in 'Send us a message' form."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if _rate_limited(request, "contact"):
            return Response(
                error_response(
                    message="You've sent a few messages already — please try again later.",
                    code="rate_limited",
                ),
                status=200,
            )

        serializer = ContactMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                error_response(message=serializer.errors, code="validation_error"),
                status=200,
            )

        try:
            obj = serializer.save(source_ip=client_ip(request))
            notify_contact_message(obj)
        except Exception:
            logger.exception("ContactMessage submission failed")
            return Response(
                error_response(message="Something went wrong. Please try again.", code="error"),
                status=200,
            )

        return Response(
            success_response(message="Thanks for reaching out — we'll get back to you soon.", data={}),
            status=200,
        )


class PartnerLeadView(APIView):
    """Public — fitzz.in 'Become a Partner' form."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if _rate_limited(request, "partner"):
            return Response(
                error_response(
                    message="We've already received a request from you — our team will be in touch.",
                    code="rate_limited",
                ),
                status=200,
            )

        serializer = PartnerLeadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                error_response(message=serializer.errors, code="validation_error"),
                status=200,
            )

        try:
            obj = serializer.save(source_ip=client_ip(request))
            notify_partner_lead(obj)
        except Exception:
            logger.exception("PartnerLead submission failed")
            return Response(
                error_response(message="Something went wrong. Please try again.", code="error"),
                status=200,
            )

        return Response(
            success_response(message="Thanks! Our partnerships team will contact you within 24 hours.", data={}),
            status=200,
        )


class AppVersionView(APIView):
    """
    Version gate for the mobile app. Called on launch.

    Per platform:
      - min_version    : installed < this  -> FORCED, non-dismissable update
      - latest_version : min <= installed < this -> OPTIONAL, dismissable prompt
                         (leave unset / "0" to never show the optional prompt)

    All values are env vars so each release's policy is set from the hosting
    dashboard with no code deploy:
      * forced release   -> raise APP_MIN_VERSION_<PLATFORM> to the new version
      * optional release -> raise APP_LATEST_VERSION_<PLATFORM> only
      * silent release   -> change neither

    IMPORTANT: only raise these AFTER that build is live on the store, else
    users are told to update to something that isn't there yet.
    """

    def get(self, request):
        data = {
            "android": {
                "min_version": config("APP_MIN_VERSION_ANDROID", default="1.0"),
                "latest_version": config("APP_LATEST_VERSION_ANDROID", default="0"),
                "package_name": config("APP_ANDROID_PACKAGE", default="in.fitzz.app"),
                "store_url": config(
                    "APP_ANDROID_STORE_URL",
                    default="https://play.google.com/store/apps/details?id=in.fitzz.app",
                ),
            },
            "ios": {
                "min_version": config("APP_MIN_VERSION_IOS", default="1.0"),
                "latest_version": config("APP_LATEST_VERSION_IOS", default="0"),
                "app_id": config("APP_IOS_APP_ID", default=""),
                "store_url": config("APP_IOS_STORE_URL", default=""),
            },
            "title": config("APP_UPDATE_TITLE", default="Update required"),
            "message": config(
                "APP_UPDATE_MESSAGE",
                default="Please update to the latest version to continue using the app.",
            ),
            "optional_title": config("APP_OPTIONAL_UPDATE_TITLE", default="Update available"),
            "optional_message": config(
                "APP_OPTIONAL_UPDATE_MESSAGE",
                default="A new version is available with improvements and fixes.",
            ),
        }
        success_data = success_response(message="success", code="success", data=data)
        return Response(success_data, status=200)
