from django.contrib import admin
from .models import SubscriptionPlan, PlanDetails, UserSubscription, UserSubscriptionHistory, DicountCoupon

# Register your models here.

class PlanDetailsInline(admin.TabularInline):  # Or use admin.StackedInline for vertical layout
    model = PlanDetails
    extra = 0  # Number of empty forms to display
    fields = ('icon', 'details', 'position', 'status',)
    ordering = ('position',)


class SubscriptionPlanAdmin(admin.ModelAdmin):
    # model = Gym
    # Show these columns in the admin list view
    list_display = (
        'name', 
        'plan_type',
        'session_count', 
        'price', 
        'currency',
        'duration_in_days',
        'premim_type',
        'position',
        'status'
    )

    inlines = [PlanDetailsInline]  # Add inline here

    # Enable filters in the sidebar
    list_filter = ('name', 'plan_type', 'currency', 'duration_in_days', 'premim_type', 'status')

    # Make fields searchable
    search_fields = ('name', 'details', 'plan_type', 'currency', )

    list_editable = ('position', 'status')

    # Automatically set read-only fields
    # readonly_fields = ('created_at',)

    ordering = ('position',)

    # Optional: organize fields into sections
    fieldsets = (
        ("", {
            'fields': ('name', 'details', 'plan_type', 'session_count', 'price', 'currency', 'duration_in_days', 'premim_type', 'position', 'status')
        }),
    )


class UserSubscriptionHistoryAdmin(admin.ModelAdmin):
   
    # Show these columns in the admin list view
    list_display = (
        'order_id', 
        'user',
        'plan', 
        'per_session_price',
        'total_paid', 
        'currency',
        'payment_status',
        'created_at'
    )

    # Enable filters in the sidebar
    list_filter = ('user', 'plan', 'duration_in_days', 'payment_status')

    # Make fields searchable
    search_fields = ('order_id', 'user', 'plan', 'currency', )

    # Automatically set read-only fields
    readonly_fields = ('created_at',)

    ordering = ('-created_at',)

    # Optional: organize fields into sections
    fieldsets = (
        ("", {
            'fields': ('order_id', 'user', 'plan', 'per_session_price', 'discount_amount', 'tax', 'total_paid', 'currency', 'sessions_count', 'duration_in_days', 'expire_on', 'payment_status', 'created_at')
        }),
    )


class UserSubscriptionAdmin(admin.ModelAdmin):
   
    # Show these columns in the admin list view
    list_display = (
        'user', 
        'plan',
        'start_date',
        'expire_on', 
        'sessions_left',
        'is_active',
    )

    # Enable filters in the sidebar
    list_filter = ('user', 'plan', 'is_active',)

    # Make fields searchable
    search_fields = ('user', 'plan',)

    # Automatically set read-only fields
    # readonly_fields = ('created_at',)

    ordering = ('-start_date',)

    # Optional: organize fields into sections
    fieldsets = (
        ("", {
            'fields': ('user', 'plan', 'start_date', 'expire_on', 'sessions_left', 'is_active',)
        }),
    )


# gym Review
class DicountCouponAdmin(admin.ModelAdmin):
    # list_display_links = None
    list_display = (
        'coupon_code',
        'percentage',
        'status',
    )

    # Make fields searchable
    search_fields = ('coupon_code',)
    list_filter = ('status',)

    # list_editable = ('status',)
    ordering = ('-created_at',)


admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(UserSubscriptionHistory, UserSubscriptionHistoryAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)
admin.site.register(DicountCoupon, DicountCouponAdmin)