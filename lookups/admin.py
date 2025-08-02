from django.contrib import admin

from .models import WorkoutType, ExerciseName, GymFeature
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


admin.site.register(WorkoutType, WorkoutTypeAdmin)
admin.site.register(ExerciseName, ExerciseNameAdmin)
admin.site.register(GymFeature, GymFeatureAdmin)