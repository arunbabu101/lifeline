from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import *


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_email', 'blood_group', 'district', 'is_blood_donor', 'phone')
    list_filter = ('is_blood_donor', 'blood_group', 'district')
    search_fields = ('user__username', 'user__email', 'phone')
    ordering = ('user__username',)

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    






@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'phone', 'email', 'manager_name', 'is_active')
    list_filter = ('district', 'is_active')
    search_fields = ('name', 'email', 'phone', 'manager_name')
    ordering = ('name',)

@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'author','total_likes', 'category', 'created_at', 'is_featured', 'views_count')
    list_filter = ('category', 'is_featured', 'created_at')
    search_fields = ('title','tags', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    raw_id_fields = ('author',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'blog', 'created_at', 'comment_excerpt')
    list_filter = ('created_at',)
    search_fields = ('content', 'user__username', 'blog__title')
    raw_id_fields = ('user', 'blog')

    def comment_excerpt(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    comment_excerpt.short_description = 'Comment'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'blog')


class OrganRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'hospital', 'organ_type', 'patient_name', 'patient_age', 'patient_blood_group', 'urgency_level', 'status', 'matched_donor', 'created_at')
    list_filter = ('status', 'urgency_level', 'patient_blood_group', 'organ_type', 'hospital')
    search_fields = ('patient_name', 'hospital__name', 'organ_type__name', 'matched_donor__name')
    ordering = ('-created_at',)

admin.site.register(OrganRequest, OrganRequestAdmin)


class OrganTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
admin.site.register(OrganType, OrganTypeAdmin)




class OrganDonorAdmin(admin.ModelAdmin):
    list_filter = ('is_active',)
admin.site.register(OrganDonor, OrganDonorAdmin)


@admin.register(BloodDonation)
class BloodDonationAdmin(admin.ModelAdmin):
    list_display = ('donor', 'blood_request', 'donation_date', 'created_at')
    list_filter = ('donation_date', 'blood_request__blood_group')
    search_fields = ('donor__name', 'blood_request__blood_group')