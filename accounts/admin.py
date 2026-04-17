from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

# Register your models here.
from .models import CustomUser, Gym, GymMedia, GymTiming, GymEquipment, GymReview, GymFavorite, UserSelectLocation, FreeSessionRequest, UserOTP, AccountDeleteRequest, BankDetail


# Inline admin for user select locaiotn
class UserSelectLocationInline(admin.TabularInline):  # Or use admin.StackedInline for vertical layout
    model = UserSelectLocation
    extra = 0  # Number of empty forms to display
    fields = ('address', 'latitude', 'longitude', 'created_at', 'status')
    ordering = ('status', '-created_at',)
    readonly_fields = ('created_at',)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    ordering = ('-created_at',)
    # inlines = [UserSelectLocationInline,]  # Add inline here
    # exclude_fields = ['password', 'last_login']  # fields to exclude
    list_display = (
        'username', 
        'email', 
        'mobile_number', 
        'first_name', 
        'last_name', 
        'user_type',
        'status',
        'created_at',
        "get_otp"
    )
    list_editable = ('user_type',)

    def get_otp(self, obj):
        otp = UserOTP.objects.filter(user=obj).order_by("-created_at").first()
        return otp.otp if otp else "-"
    get_otp.short_description = "OTP"

    list_filter = ('status', 'user_type',)

    # list_editable = ('status', 'premium_type',)

    # Make fields searchable
    search_fields = ('username', 'mobile_number', 'email', 'first_name', 'last_name',)

    fieldsets = UserAdmin.fieldsets + (
        ("Personal info", {
            "fields": ("mobile_number", "user_type"),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Personal info", {
            "fields": ("mobile_number", "user_type"),
        }),
    )



# Inline admin for GymMedia
class GymMediaInline(admin.TabularInline):  # Or use admin.StackedInline for vertical layout
    model = GymMedia
    extra = 0  # Number of empty forms to display
    fields = ('name', 'description', 'media', 'position', )
    ordering = ('position',)

# Inline admin for GymTimes
class GymTimingline(admin.TabularInline):  # Or use admin.StackedInline for vertical layout
    model = GymTiming
    extra = 0  # Number of empty forms to display
    fields = ('day', 'morning_start', 'morning_end', 'evening_start', 'evening_end', 'position', 'status')
    ordering = ('position',)

# Inline admin for Gym Equipment
class GymEquipmentline(admin.TabularInline):  # Or use admin.StackedInline for vertical layout
    model = GymEquipment
    extra = 0  # Number of empty forms to display
    fields = ('icon', 'category', 'description', 'position', 'status')
    ordering = ('position',)

# gym admin
class GymAdmin(admin.ModelAdmin):
    # model = Gym
    # Show these columns in the admin list view
    list_display = (
        'name', 
        'address',
        'city', 
        'state', 
        'country', 
        'status', 
        'per_session_cost',
        'premium_type',
        'owner',
        'verified_by',
        'created_by',
        'created_at'
    )

    inlines = [GymMediaInline, GymTimingline, GymEquipmentline]  # Add inline here

    # Enable filters in the sidebar
    list_filter = ('status', 'premium_type')

    list_editable = ('status', 'premium_type')

    # Make fields searchable
    search_fields = ('name', 'city', 'state', 'country', 'owner__email', 'created_by__email')

    # Automatically set read-only fields
    readonly_fields = ('created_at', 'updated_at', 'gym_id')

    # Optional: organize fields into sections
    fieldsets = (
        ("Basic Info", {
            'fields': ('name', 'description', 'profile_icon')
        }),
        ("Location", {
            'fields': ('address', 'city', 'state', 'country', 'zip_code', 'latitude', 'longitude')
        }),
        ("Pricing & Status", {
            'fields': ('per_session_cost', 'currency', 'premium_type', 'status')
        }),
        ("Feature", {
            'fields': ('feature',)
        }),
        ("Ownership", {
            'fields': ('owner', 'verified_by')
        }),
        ("System Info", {
            'fields': ('gym_id', 'created_at', 'updated_at')
        }),
    )



# gym Review
class GymReviewAdmin(admin.ModelAdmin):
    # model = Gym
    # Show these columns in the admin list view
    # list_display_links = None
    list_display = (
        'id',
        'user',
        'gym',
        'rating', 
        'created_at',
        'status'
    )

    # Make fields searchable
    search_fields = ('user', 'gym', 'rating')
    list_filter = ('user', 'gym', 'rating', 'status')

    list_editable = ('status',)
    ordering = ('-created_at',)



class GymFavoriteAdmin(admin.ModelAdmin):
    list_display_links = None
    list_display = (
        'user',
        'gym',
        'created_at',
    )

    # Make fields searchable
    search_fields = ('user', 'gym')
    list_filter = ('user', 'gym')

    # list_editable = ('status',)
    ordering = ('-created_at',)



class FreeSessionRequestAdmin(admin.ModelAdmin):
    list_display_links = None
    list_display = (
        'user__username',
        'user__mobile_number',
        'user__email',
        'created_at',
        'status'
    )

    # Make fields searchable
    search_fields = ('user__username','user__mobile_number','user__email',)
    list_filter = ('status',)

    list_editable = ('status',)
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        obj.full_clean()   # 👈 This triggers clean()
        super().save_model(request, obj, form, change)


class AccountDeleteRequestAdmin(admin.ModelAdmin):
    list_display_links = None
    list_display = (
        'user__username',
        'user__mobile_number',
        'user__email',
        'requested_on',
        'status'
    )

    # Make fields searchable
    search_fields = ('user__username','user__mobile_number','user__email',)
    list_filter = ('status',)

    list_editable = ('status',)
    ordering = ('-requested_on',)


class BankDetailAdmin(admin.ModelAdmin):
    # list_display_links = None
    list_display = (
        'user',
        'account_holder_name',
        'bank_name',
        'account_number',
        'ifsc_code',
        'is_verified',
        'status'
    )

    # Make fields searchable
    search_fields = ('user', 'account_holder_name', 'bank_name', 'account_number', 'ifsc_code',)
    list_filter = ('user', )

    list_editable = ('is_verified','status',)
    ordering = ('-created_at',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Gym, GymAdmin)
admin.site.register(GymReview, GymReviewAdmin)
admin.site.register(GymFavorite, GymFavoriteAdmin)
admin.site.register(FreeSessionRequest, FreeSessionRequestAdmin)
admin.site.register(AccountDeleteRequest, AccountDeleteRequestAdmin)
admin.site.register(BankDetail, BankDetailAdmin)




