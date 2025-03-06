from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('blogs/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('blog/<slug:slug>/add_comment/', views.add_comment, name='add_comment'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path("predict/", views.predict_kidney_disease_view, name="predict_kidney_disease"),




    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),


    # Donor Authentication URLs
    path('donor_home/', views.donor_home, name='donor_home'),
    path('donor/signup/', views.donor_register, name='donor_register'),
    path('donor/login/', views.donor_login, name='donor_login'),
    path('donor/profile/', views.donor_profile, name='donor_profile'),
    path('donor/profile/edit/', views.edit_donor_profile, name='edit_donor_profile'),
    path('donor/logout/', views.donor_logout, name='donor_logout'),
    path('donor/blood-requests/', views.donor_blood_requests, name='donor_blood_requests'),
    path('donor/respond-to-request/<int:request_id>/', views.respond_to_request, name='respond_to_request'),
    path('donor/offer-help/<int:request_id>/', views.offer_help, name='offer_help'),


    #hospital

    path('hospital/signup/', views.hospital_register, name='hospital_register'),
    path('hospital/login/', views.hospital_login, name='hospital_login'),
    path('hospital/home/', views.hospital_home, name='hospital_home'),
    path('profile/', views.hospital_profile, name='hospital_profile'),
    path('download-blood-requests-pdf/', views.download_blood_requests_pdf, name='download_blood_requests_pdf'),
    path('download-organ-requests-pdf/', views.download_organ_requests_pdf, name='download_organ_requests_pdf'),
    path('download-certificate/<int:donation_id>/', views.download_certificate, name='download_certificate'),
    path('profile/edit/', views.edit_hospital_profile, name='edit_hospital_profile'),
    path('hospital/blood-donors/', views.blood_donor_list, name='blood_donor_list'),
    path('hospital/blood-requests/', views.blood_request_list, name='blood_request_list'),
    path('hospital/organ-donors/', views.organ_donor_list, name='organ_donor_list'),
    path('blood-request/<int:request_id>/', views.blood_request_detail, name='blood_request_detail'),
    path('hospital/blood-requests/create/', views.create_blood_request, name='create_blood_request'),
    path('hospital/logout/', views.hospital_logout, name='hospital_logout'),
    path('blood-request/<int:request_id>/edit/', views.edit_blood_request, name='edit_blood_request'),
    path('blood-request/<int:request_id>/cancel/', views.cancel_blood_request, name='cancel_blood_request'),
    path('contact-donor/<int:donor_id>/', views.contact_donor, name='contact_donor'),
    path('donor_detail/<int:donor_id>/', views.donor_detail, name='donor_detail'),

    
    path('hospital/messages/', views.hospital_all_messages, name='hospital_all_messages'),
    path('donor-chat/<int:donor_id>/', views.donor_chat, name='donor_chat'),

    path('donor/messages/', views.donor_all_messages, name='donor_all_messages'),
    path('hospital-chat/<int:hospital_id>/', views.donor_hospital_chat, name='donor_hospital_chat'),

    #blood donation

    path('blogs/all/', views.all_blogs, name='all_blogs'),
    path('blogs/my/', views.my_blogs, name='my_blogs'),
    path('blogs/add/', views.add_blog, name='add_blog'),
    path('blogs/like/<int:blog_id>/', views.like_blog, name='like_blog'),
    path('blog/dislike_blog/<int:blog_id>/', views.dislike_blog, name='dislike_blog'),

    #-----organ donation---------
    path('organ-donation/register/', views.register_organ_donor, name='register_organ_donor'),
    path('organ-donation/matching-requests/', views.matching_organ_requests, name='matching_organ_requests'),
    path('create-organ-request/', views.create_organ_request, name='create_organ_request'),
    path('organ_request_list/', views.organ_request_list, name='organ_request_list'),
    path('organ-request/<int:request_id>/', views.organ_request_detail, name='organ_request_detail'),
    path('organ-request/<int:request_id>/edit/', views.edit_organ_request, name='edit_organ_request'),
    path('organ-request/<int:request_id>/cancel/', views.cancel_organ_request, name='cancel_organ_request'),
    path('match-request/<int:request_id>/match/', views.match_organ_donor, name='match_organ_request'),
    path('organ_request/<int:request_id>/update_status/', views.update_organ_request_status, name='update_organ_request_status'),




    
    # Hospital URLs



]
