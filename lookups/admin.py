from django.contrib import admin

from .models import WorkoutType, ExerciseName, GymFeature, ContactMessage, PartnerLead
# Register your models here.

# gym admin
class WorkoutTypeAdmin(admin.ModelAdmin):
    # model = Gym
    # Show these columns in the admin list view
    list_display_links = None
    list_display = (
        'name', 
        'details', 
        'position',
        'status'
    )

    # Make fields searchable
    search_fields = ('name', 'details')
    list_editable = ('name', 'details', 'position', 'status')
    ordering = ('position',)


# gym admin
class ExerciseNameAdmin(admin.ModelAdmin):
    # model = Gym
    # Show these columns in the admin list view
    list_display_links = None
    list_display = (
        'name', 
        'workout_type',
        'details', 
        'position',
        'status'
    )

    # Make fields searchable
    search_fields = ('name', 'details')
    list_editable = ('name', 'workout_type', 'details', 'position', 'status')
    ordering = ('position',)

# gym Feature
class GymFeatureAdmin(admin.ModelAdmin):
    # model = Gym
    # Show these columns in the admin list view
    # list_display_links = None
    list_display = (
        'id',
        'name', 
        'details', 
        'position',
        'status'
    )

    # Make fields searchable
    search_fields = ('name', 'details')
    list_editable = ('name', 'details', 'position', 'status')
    ordering = ('position',)


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'name', 'email', 'phone', 'category', 'status')
    list_filter = ('status', 'category', 'created_at')
    list_editable = ('status',)
    search_fields = ('name', 'email', 'phone', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('name', 'email', 'phone', 'category', 'message', 'source_ip', 'created_at')

    def has_add_permission(self, request):
        return False


class PartnerLeadAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'gym_name', 'owner_name', 'mobile', 'city', 'status')
    list_filter = ('status', 'city', 'created_at')
    list_editable = ('status',)
    search_fields = ('gym_name', 'owner_name', 'mobile', 'email', 'city', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('gym_name', 'owner_name', 'mobile', 'email', 'city', 'message', 'source_ip', 'created_at')

    def has_add_permission(self, request):
        return False


admin.site.register(WorkoutType, WorkoutTypeAdmin)
admin.site.register(ExerciseName, ExerciseNameAdmin)
admin.site.register(GymFeature, GymFeatureAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)
admin.site.register(PartnerLead, PartnerLeadAdmin)