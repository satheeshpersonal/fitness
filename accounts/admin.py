from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

# Register your models here.
from .models import CustomUser, Gym, GymMedia, GymTiming, GymEquipment, GymReview, GymFavorite, UserSelectLocation


# Inline admin for user select locaiotn
class UserSelectLocationInline(admin.TabularInline):  # Or use admin.StackedInline for vertical layout
    model = UserSelectLocation
    extra = 0  # Number of empty forms to display
    fields = ('address', 'latitude', 'longitude', 'created_at', 'status')
    ordering = ('status', '-created_at',)
    readonly_fields = ('created_at',)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # inlines = [UserSelectLocationInline,]  # Add inline here
    # exclude_fields = ['password', 'last_login']  # fields to exclude
    list_display = (
        'username', 
        'email', 
        'mobile_number', 
        'first_name', 
        'last_name', 
        'is_staff',
        'user_type',
        'status',
        'created_at'
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
        'city', 
        'state', 
        'country', 
        'status', 
        'currency',
        'owner',
        'verified_by',
        'created_at'
    )

    inlines = [GymMediaInline, GymTimingline, GymEquipmentline]  # Add inline here

    # Enable filters in the sidebar
    list_filter = ('status', 'city', 'state', 'currency', 'verified_by')

    # Make fields searchable
    search_fields = ('name', 'city', 'state', 'country', 'owner__email')

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


# gym Review
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




admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Gym, GymAdmin)
admin.site.register(GymReview, GymReviewAdmin)
admin.site.register(GymFavorite, GymFavoriteAdmin)
