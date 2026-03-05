from django.contrib import admin
from .models import WorkoutSchedule, GymAccessLog, WorkoutExercise

# Register your models here.
# Inline admin for GymMedia

# class GymAccessLogInline(admin.TabularInline):  # Or use admin.StackedInline for vertical layout
#     model = GymAccessLog
#     extra = 0  # Number of empty forms to display
#     fields = ('gym_access_id', 'gym', 'date')
#     ordering = ('date',)

class WorkoutExerciseInline(admin.TabularInline):  # Or use admin.StackedInline for vertical layout
    model = WorkoutExercise
    extra = 0  # Number of empty forms to display
    fields = ('exercise_name', 'reps', 'sets', 'weight', 'duration_minutes', 'notes')
    ordering = ('created_at',)

# gym admin
class WorkoutScheduleAdmin(admin.ModelAdmin):
    # model = Gym
    # Show these columns in the admin list view
    list_display = (
        'user', 
        'gym', 
        'list_workout_type',
        'scheduled_at', 
        'created_at', 
    )

    inlines = [WorkoutExerciseInline]  # Add inline here

    # Enable filters in the sidebar
    list_filter = ('user', 'gym', 'scheduled_at',)

    # Make fields searchable
    search_fields = ('user', 'gym', 'workout_type', 'country', )

    # Automatically set read-only fields
    readonly_fields = ('created_at',)

    # Optional: organize fields into sections
    fieldsets = (
        ("", {
            'fields': ('user', 'gym', 'workout_type', 'scheduled_at', 'body_weight', 'duration_minutes', 'burned_calories', 'heart_rate')
        }),
    )

    def list_workout_type(self, obj):
        return ", ".join([all_workout_type.name for all_workout_type in obj.workout_type.all()])


class GymAccessLogAdmin(admin.ModelAdmin):  # Or use admin.StackedInline for vertical layout
    # model = GymAccessLog
    list_display_links = None
    list_display = (
        'gym__name', 
        'gym__owner__first_name', 
        'gym__owner__last_name', 
        'gym__owner__email', 
        'user__first_name',
        'user__last_name',
        'access_date',
        'amount',
        'settled_status',
        'settled_on'
    )
    # fields = ('gym_access_id', 'user', 'gym', 'device_id', 'access_date')
    ordering = ('-access_date',)

    search_fields = ('gym__name', 'gym__owner__first_name', 'gym__owner__last_name','gym__owner__email','user__first_name','user__last_name',)
    list_filter = ('settled_status',)
    list_editable = ('settled_status',)
    # readonly_fields = ('access_date',)

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(WorkoutSchedule, WorkoutScheduleAdmin)
admin.site.register(GymAccessLog, GymAccessLogAdmin)