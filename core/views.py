import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Donor, Blog, BlogCategory, Comment
from .forms import  *
from django.contrib.auth import login as auth_login, authenticate
from django.http import JsonResponse
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from datetime import timedelta
from django.db.models import Count, Max
from django.contrib import messages

# views.py
def home(request):
    latest_blogs = Blog.objects.all().order_by('-created_at')[:9]
    categories = BlogCategory.objects.all()
    
    context = {
        'latest_blogs': latest_blogs,
        'categories': categories,
    }
    return render(request, 'home.html', context)



def blog_list(request):
    blogs = Blog.objects.all().order_by('-created_at')
    categories = BlogCategory.objects.all()
    
    # Search functionality
    search_query = request.GET.get('q')
    category = request.GET.get('category')
    
    if search_query:
        blogs = blogs.filter(title__icontains=search_query) | blogs.filter(tags__icontains=search_query)
    
    if category:
        blogs = blogs.filter(category__slug=category)
    
    # Pagination
    paginator = Paginator(blogs, 9)  # 9 blogs per page (3x3 grid)
    page = request.GET.get('page')
    blogs = paginator.get_page(page)
    
    context = {
        'blogs': blogs,
        'categories': categories,
        'search_query': search_query,
        'current_category': category,
    }
    return render(request, 'blog.html', context)

def blog_detail(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    comments = Comment.objects.filter(blog=blog).order_by('-created_at')
    recent_posts = Blog.objects.exclude(id=blog.id).order_by('-created_at')[:5]
    categories = BlogCategory.objects.all()
    
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.blog = blog
            comment.user = request.user
            comment.save()
            return redirect('blog_detail', slug=slug)
    else:
        comment_form = CommentForm()
    
    context = {
        'blog': blog,
        'comments': comments,
        'comment_form': comment_form,
        'recent_posts': recent_posts,
        'categories': categories,
    }
    return render(request, 'blog_detail.html', context)

@login_required
def add_comment(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            comment.user = request.user
            comment.save()
    return redirect('blog_detail', slug=slug)




#-------------------hospital_views----------------------------------------#


def hospital_register(request):
    if request.method == 'POST':
        form = HospitalRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('hospital_login')
    else:
        form = HospitalRegistrationForm()
    return render(request, 'hospital/register.html', {'form': form})

def hospital_login(request):
    if request.method == 'GET':
        next_page = request.GET.get('next', '')  # Default to an empty string if not provided
        context = {'next': next_page}
        return render(request, 'hospital/login.html', context)

    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)

    if user and hasattr(user, 'hospital_profile'):
        auth_login(request, user)

        # Ensure 'next_page' is valid; fallback to 'hospital_home' if not
        next_page = request.POST.get('next')
        if not next_page or not next_page.strip():
            next_page = 'hospital_home'  # Provide a valid default URL name
        return redirect(next_page)

    # Handle login failure
    context = {
        'error': 'Invalid email or password',
        'next': request.POST.get('next', '')  # Ensure a default if 'next' is None
    }
    return render(request, 'hospital/login.html', context)


@login_required
def hospital_home(request):
    # Get the hospital profile
    hospital = request.user.hospital_profile

    # Get recent messages to this hospital
    recent_messages = Message.objects.filter(
        recipient=request.user
    ).order_by('-timestamp')[:5]

    # Get recent blood requests for this hospital
    recent_blood_requests = BloodRequest.objects.filter(
        hospital=hospital
    ).order_by('-created_at')[:5]

    # Get the count of available donors
    available_donors = Donor.objects.filter(
        is_active=True,
        district=hospital.district
    ).count()

    # Get the count of pending blood requests
    pending_requests = BloodRequest.objects.filter(
        hospital=hospital,
        status='pending'
    ).count()

    # Get the count of total blood requests
    total_blood_requests = BloodRequest.objects.filter(
        hospital=hospital
    ).count()

    # Calculate success rate (assuming 'fulfilled' status means success)
    fulfilled_requests = BloodRequest.objects.filter(
        hospital=hospital,
        status='fulfilled'
    ).count()
    success_rate = (fulfilled_requests / total_blood_requests * 100) if total_blood_requests > 0 else 0

    context = {
        'recent_messages': recent_messages,
        'recent_blood_requests': recent_blood_requests,
        'available_donors': available_donors,
        'pending_requests': pending_requests,
        'total_blood_requests': total_blood_requests,
        'success_rate': round(success_rate, 2),
    }
    return render(request, 'hospital/hospital_home.html', context)


@login_required
def hospital_profile(request):
    try:
        hospital = request.user.hospital_profile
    except Hospital.DoesNotExist:
        hospital = None

    context = {'hospital': hospital}
    return render(request, 'hospital/profile.html', context)


@login_required
def edit_hospital_profile(request):
    try:
        hospital = request.user.hospital_profile
    except Hospital.DoesNotExist:
        return redirect('hospital_profile')  # Redirect if no profile exists

    if request.method == 'POST':
        form = HospitalProfileForm(request.POST, request.FILES, instance=hospital)
        if form.is_valid():
            form.save()
            return redirect('hospital_profile')
    else:
        form = HospitalProfileForm(instance=hospital)

    context = {'form': form}
    return render(request, 'hospital/edit_profile.html', context)

@login_required
def hospital_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


#blood request views

@login_required
def blood_donor_list(request):
    # Start with all blood donors
    donors = Donor.objects.filter(is_blood_donor=True, is_active=True)
    
    # Filter out ineligible donors
    eligible_donors = [donor for donor in donors if donor.is_eligible_to_donate()]
    donors = Donor.objects.filter(id__in=[donor.id for donor in eligible_donors])
    
    # Apply additional filters
    blood_group = request.GET.get('blood_group')
    if blood_group:
        donors = donors.filter(blood_group=blood_group)
    
    district = request.GET.get('district')
    if district:
        donors = donors.filter(district=district)
    
    context = {
        'donors': donors,
        'blood_groups': Donor.BLOOD_GROUP_CHOICES,
        'districts': Donor.PLACE_CHOICES
    }
    return render(request, 'hospital/blood_donor_list.html', context)



@login_required
def blood_request_list(request):
    current_date = timezone.now().date()
    
    # Active blood requests
    active_requests = BloodRequest.objects.filter(
        hospital=request.user.hospital_profile,
        status__in=['pending', 'approved', 'processing'],
        required_by__gte=current_date
    ).order_by('-created_at')
    
    # Historical requests
    history_requests = BloodRequest.objects.filter(
        hospital=request.user.hospital_profile
    ).exclude(
        status__in=['pending', 'approved', 'processing'],
        required_by__gte=current_date
    ).order_by('-created_at')
    
    # Annotate active requests
    active_requests = active_requests.annotate(
        response_count=Count('donorresponse', distinct=True),
        help_count=Count('donorhelp', distinct=True)
    )
    
    context = {
        'requests': active_requests,
        'history_requests': history_requests,
    }
    
    return render(request, 'hospital/blood_request_list.html', context)



@login_required
def blood_request_detail(request, request_id):
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    
    if blood_request.hospital != request.user.hospital_profile:
        messages.error(request, "You don't have permission to view this request.")
        return redirect('blood_request_list')

    # Get matching donors and counts
    matching_donors = Donor.objects.filter(
        blood_group=blood_request.blood_group,
        district=blood_request.hospital.district,
        is_active=True
    )
    response_count = DonorResponse.objects.filter(blood_request=blood_request).count()
    help_count = DonorHelp.objects.filter(blood_request=blood_request).count()

    # Get responses and helps for display
    responses = DonorResponse.objects.filter(blood_request=blood_request).select_related('donor')
    helps = DonorHelp.objects.filter(blood_request=blood_request).select_related('donor')
    
    # Get existing donations
    donations = BloodDonation.objects.filter(blood_request=blood_request).select_related('donor')

    # Handle donation form submission
    if request.method == 'POST':
        if 'blood_received' in request.POST:
            if request.POST['blood_received'] == 'yes':
                # Show donation form instead of immediately marking as fulfilled
                context = {
                    'request': blood_request,
                    'matching_donors': matching_donors,
                    'response_count': response_count,
                    'help_count': help_count,
                    'responses': responses,
                    'helps': helps,
                    'donations': donations,
                    'show_donation_form': True,
                    'donor_choices': DonorResponse.objects.filter(
                        blood_request=blood_request,
                        status='accepted'
                    ).select_related('donor'),
                    'units_required': range(blood_request.units_required)
                }
                return render(request, 'hospital/blood_request_detail.html', context)
            else:
                blood_request.last_checked = timezone.now().date()
                blood_request.save()
                messages.info(request, "We'll check again tomorrow about blood receipt.")
        
        elif 'submit_donations' in request.POST:
            donor_ids = request.POST.getlist('donor')
            dates = request.POST.getlist('donation_date')
            
            if len(donor_ids) != blood_request.units_required:
                messages.error(request, f"Please select exactly {blood_request.units_required} donors.")
            else:
                try:
                    # Create donation records
                    for donor_id, date in zip(donor_ids, dates):
                        BloodDonation.objects.create(
                            blood_request=blood_request,
                            donor_id=donor_id,
                            donation_date=date
                        )
                    
                    # Update request status
                    blood_request.blood_received = True
                    blood_request.status = 'fulfilled'
                    blood_request.save()
                    messages.success(request, "Blood donations recorded and request marked as fulfilled.")
                except Exception as e:
                    messages.error(request, f"Error recording donations: {str(e)}")

    # Auto-update status to processing if enough responses
    if response_count >= blood_request.units_required and blood_request.status == 'pending':
        blood_request.status = 'processing'
        blood_request.save()
        messages.success(request, "Status automatically updated to Processing as required units have been matched.")

    # Check for expired requests
    if blood_request.required_by < timezone.now().date() and blood_request.status in ['pending', 'processing']:
        blood_request.status = 'expired'
        blood_request.save()
        messages.warning(request, "This blood request has expired.")

    # Determine if we should show the blood receipt question
    show_blood_received = (
        blood_request.status == 'processing' and
        not blood_request.blood_received and 
        blood_request.required_by >= timezone.now().date() and
        (blood_request.last_checked is None or 
         (timezone.now().date() - blood_request.last_checked) >= timedelta(days=1))
    )

    context = {
        'request': blood_request,
        'matching_donors': matching_donors,
        'response_count': response_count,
        'help_count': help_count,
        'responses': responses,
        'helps': helps,
        'donations': donations,
        'show_blood_received': show_blood_received,
        'show_donation_form': False  # Default value
    }
    return render(request, 'hospital/blood_request_detail.html', context)


@require_POST
def cancel_blood_request(request, request_id):
    blood_request = get_object_or_404(BloodRequest, id=request_id, hospital=request.user.hospital_profile)
    if blood_request.status in ['pending', 'processing']:
        blood_request.status = 'cancelled'
        blood_request.save()
        messages.success(request, 'Blood request cancelled successfully.')
    else:
        messages.error(request, 'This request cannot be cancelled.')
    return redirect('blood_request_list')

@require_POST
def edit_blood_request(request, request_id):
    blood_request = get_object_or_404(BloodRequest, id=request_id, hospital=request.user.hospital_profile)
    if blood_request.status != 'pending':
        messages.error(request, 'Only pending requests can be edited.')
        return redirect('blood_request_detail', request_id=request_id)
    
    form = BloodRequestForm(request.POST, instance=blood_request)
    if form.is_valid():
        form.save()
        messages.success(request, 'Blood request updated successfully.')
        return redirect('blood_request_detail', request_id=request_id)
    
    messages.error(request, 'Please correct the errors below.')
    return redirect('blood_request_detail', request_id=request_id)

def get_blood_request_form(request, request_id):
    blood_request = get_object_or_404(BloodRequest, id=request_id, hospital=request.user.hospital_profile)
    form = BloodRequestForm(instance=blood_request)
    form_html = render_to_string('hospital/blood_request_form.html', {'form': form}, request=request)
    return JsonResponse({'form_html': form_html})


@login_required
def get_donor_contact(request, donor_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
        
    donor = get_object_or_404(Donor, id=donor_id)
    request_id = request.POST.get('request_id')
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    
    # Security check
    if blood_request.hospital != request.user.hospital_profile:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Record contact attempt
    DonorContact.objects.create(
        donor=donor,
        blood_request=blood_request,
        hospital=request.user.hospital_profile
    )
    
    return JsonResponse({
        'phone': donor.phone_number,
        'name': donor.get_name()
    })





@login_required
def mark_request_success(request, request_id):
    if request.method == 'POST':
        blood_request = get_object_or_404(BloodRequest, id=request_id)
        
        # Security check
        if blood_request.hospital != request.user.hospital_profile:
            messages.error(request, "You don't have permission to update this request.")
            return redirect('blood_request_list')
        
        if blood_request.status not in ['pending', 'processing']:
            messages.error(request, "Only pending or processing requests can be marked as successful.")
            return redirect('blood_request_detail', request_id=request_id)
        
        blood_request.status = 'success'
        blood_request.save()
        
        messages.success(request, "Blood request has been marked as successful.")
        return redirect('blood_request_list')
    
    return redirect('blood_request_detail', request_id=request_id)


@login_required
def create_blood_request(request):
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.hospital = request.user.hospital_profile
            blood_request.save()
            messages.success(request, 'Blood request created successfully!')
            return redirect('blood_request_list')
    else:
        form = BloodRequestForm()
    
    return render(request, 'hospital/create_blood_request.html', {'form': form})



@login_required
def all_blogs(request):
    blogs = Blog.objects.all().order_by('-created_at')
    search_query = request.GET.get('q')
    if search_query:
        blogs = blogs.filter(title__icontains=search_query) | blogs.filter(tags__icontains=search_query)
    paginator = Paginator(blogs, 8)  # 8 blogs per page
    page = request.GET.get('page')
    blogs = paginator.get_page(page)
    return render(request, 'hospital/all_blogs.html', {'blogs': blogs})


@login_required
def my_blogs(request):
    blogs = Blog.objects.filter(author=request.user.hospital_profile).order_by('-likes')
    return render(request, 'hospital/my_blogs.html', {'blogs': blogs})


@login_required
def add_blog(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user.hospital_profile
            blog.save()
            messages.success(request, "Blog added successfully!")
            return redirect('my_blogs')
    else:
        form = BlogForm()
    return render(request, 'hospital/add_blog.html', {'form': form})

@login_required
def like_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    if request.user in blog.dislikes.all():
        blog.dislikes.remove(request.user)
    if request.user not in blog.likes.all():
        blog.likes.add(request.user)
    else:
        blog.likes.remove(request.user)
    return redirect('blog_detail',slug=blog.slug)

@login_required
def dislike_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    
    # If the user has already liked the post, remove them from likes
    if request.user in blog.likes.all():
        blog.likes.remove(request.user)
    
    # Toggle dislike: add if not already disliked, remove if already disliked
    if request.user not in blog.dislikes.all():
        blog.dislikes.add(request.user)
    else:
        blog.dislikes.remove(request.user)
    
    # Redirect to the same page or a specific page
    return redirect('blog_detail',slug=blog.slug)



@login_required
def contact_donor(request, donor_id):
    """
    View to contact a specific donor
    """
    donor = get_object_or_404(Donor, id=donor_id)
    hospital = request.user.hospital_profile  # Assuming hospital user has a profile

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = donor.user
            message.sender_type = 'hospital'
            message.save()

            # Create notification
            MessageNotification.objects.create(
                user=donor.user, 
                message=message
            )

            messages.success(request, 'Message sent successfully to donor')
            return redirect('blood_donor_list')
    else:
        form = MessageForm()

    context = {
        'donor': donor,
        'form': form,
        'hospital': hospital
    }
    return render(request, 'messaging/contact_donor.html', context)





@login_required
def view_message_thread(request, message_id):
    """
    View to see full message thread
    """
    base_message = get_object_or_404(Message, id=message_id)
    
    # Get all messages in this thread (between these two users)
    message_thread = Message.objects.filter(
        (models.Q(sender=base_message.sender, recipient=base_message.recipient) | 
         models.Q(sender=base_message.recipient, recipient=base_message.sender))
    ).order_by('timestamp')

    context = {
        'message_thread': message_thread,
        'base_message': base_message
    }
    return render(request, 'messaging/message_thread.html', context)


#-----------------------------------------------------------------
@login_required
def donor_chat(request, donor_id):
    # Ensure only hospital users can access this view
    if not hasattr(request.user, 'hospital_profile'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Unauthorized access'})
        messages.error(request, 'Unauthorized access')
        return redirect('home')

    donor = get_object_or_404(Donor, id=donor_id)
    hospital = request.user.hospital_profile

    if request.method == 'POST':
        message_content = request.POST.get('message')
        context_type = request.POST.get('context_type')
        context_id = request.POST.get('context_id')
        
        if message_content:
            # Create the message
            new_message = Message(
                sender=request.user,
                recipient=donor.user,
                content=message_content,
                sender_type='hospital'
            )
            
            # Context related variables to pass to the response
            context_display_text = None
            context_class = None
            
            # Handle message context if provided
            if context_type != 'none' and context_id:
                try:
                    # Parse the context ID format (blood_123 or organ_123)
                    context_parts = context_id.split('_')
                    if len(context_parts) == 2:
                        context_prefix, actual_id = context_parts
                        actual_id = int(actual_id)
                        
                        if context_prefix == 'blood':
                            blood_request = BloodRequest.objects.get(id=actual_id)
                            new_message.blood_request = blood_request
                            context_display_text = f"Blood Request: {blood_request.patient_name} ({blood_request.blood_group})"
                            context_class = "blood-context"
                            
                            # Also create a donor contact record
                            donor_contact = DonorContact.objects.create(
                                donor=donor,
                                blood_request=blood_request,
                                hospital=hospital
                            )
                            new_message.donor_contact = donor_contact
                            
                        elif context_prefix == 'organ':
                            # Add logic for organ requests
                            organ_request = OrganRequest.objects.get(id=actual_id)
                            new_message.organ_request = organ_request
                            context_display_text = f"Organ Request: {organ_request.patient_name} - {organ_request.organ_type.name}"
                            context_class = "organ-context"
                    
                except (ValueError, BloodRequest.DoesNotExist, OrganRequest.DoesNotExist) as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': f"Couldn't link request: {str(e)}"})
                    messages.warning(request, f"Couldn't link request: {str(e)}")
            
            # Save the message
            new_message.save()
            
            # If this is an AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message_id': new_message.id,
                    'message_content': new_message.content,
                    'timestamp': new_message.timestamp.strftime('%H:%M'),
                    'context_display_text': context_display_text,
                    'context_class': context_class
                })
            
            # Otherwise, redirect with success message
            messages.success(request, 'Message sent successfully')
            return redirect(f"{request.path}?tab=messages")
    
    # If not POST or after handling POST, redirect back to donor_detail
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    return redirect('donor_detail', donor_id=donor_id)

@login_required
def view_all_messages(request):
    """
    View to display all chat threads
    """
    # If hospital, get donors they've chatted with
    if hasattr(request.user, 'hospital_profile'):
        # Get unique donors the hospital has messaged
        chat_threads = Message.objects.filter(
            sender=request.user
        ).values('recipient__donor_profile__id', 'recipient__donor_profile__blood_group', 'recipient__username').distinct()
    
    # If donor, get hospitals they've chatted with
    elif hasattr(request.user, 'donor_profile'):
        # Get unique hospitals the donor has messaged
        chat_threads = Message.objects.filter(
            sender=request.user
        ).values('recipient__hospital_profile__id', 'recipient__hospital_profile__name', 'recipient__username').distinct()
    
    context = {
        'chat_threads': chat_threads
    }
    return render(request, 'messaging/all_messages.html', context)

# views.py
@login_required
def hospital_all_messages(request):
    if not hasattr(request.user, 'hospital_profile'):
        messages.error(request, 'Unauthorized access')
        return redirect('home')

    # Fetch chat threads where the hospital has messaged donors
    chat_threads = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).filter(
        recipient__donor_profile__isnull=False  # Ensure the recipient is a donor
    ).values(
        'recipient__donor_profile__id',
        'recipient__donor_profile__blood_group',
        'recipient__username',
        'recipient__first_name',  # Add first name
        'recipient__last_name',   # Add last name
    ).annotate(
        latest_message_time=Max('timestamp'),
        unread_count=Count('id', filter=Q(status='unread') & Q(recipient=request.user))
    ).order_by('-latest_message_time')

    context = {
        'chat_threads': chat_threads
    }
    return render(request, 'messaging/hospital_all_messages.html', context)
# views.py
@login_required
def donor_all_messages(request):
    if not hasattr(request.user, 'donor_profile'):
        messages.error(request, 'Unauthorized access')
        return redirect('home')

    # Get active chat ID from URL parameter
    active_chat = request.GET.get('chat')

    # Get all messages involving this user
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).filter(
        Q(sender__hospital_profile__isnull=False) | 
        Q(recipient__hospital_profile__isnull=False)
    ).order_by('-timestamp')

    # Create a dictionary to store hospital data
    hospital_threads = {}

    for message in all_messages:
        # Determine if the hospital is sender or recipient
        if hasattr(message.sender, 'hospital_profile'):
            hospital = message.sender.hospital_profile
            is_incoming = True
        else:
            hospital = message.recipient.hospital_profile
            is_incoming = False

        # If this hospital isn't in our dict yet, initialize it
        if hospital.id not in hospital_threads:
            hospital_threads[hospital.id] = {
                'hospital_id': hospital.id,
                'hospital_name': hospital.name,
                'district': hospital.district,
                'profile_picture': hospital.profile_picture.url if hospital.profile_picture else None,
                'last_message': message.content,
                'last_message_time': message.timestamp,
                'unread_count': 0
            }

        # Count unread messages for incoming messages
        if is_incoming and message.status == 'unread':
            hospital_threads[hospital.id]['unread_count'] += 1

    # Convert dictionary to list and sort by last message time
    chat_threads = list(hospital_threads.values())
    chat_threads.sort(key=lambda x: x['last_message_time'], reverse=True)

    # If there's an active chat, get its messages
    active_chat_messages = []
    active_hospital = None
    if active_chat:
        active_hospital = get_object_or_404(Hospital, id=active_chat)
        active_chat_messages = Message.objects.filter(
            Q(sender=request.user, recipient=active_hospital.user) |
            Q(recipient=request.user, sender=active_hospital.user)
        ).order_by('timestamp')
        
        # Mark messages as read
        active_chat_messages.filter(recipient=request.user, status='unread').update(status='read')

    context = {
        'chat_threads': chat_threads,
        'active_chat': active_chat,
        'active_hospital': active_hospital,
        'active_chat_messages': active_chat_messages,
        'donor': request.user.donor_profile,
    }
    return render(request, 'messaging/donor_all_messages.html', context)

@login_required
def donor_hospital_chat(request, hospital_id):
    """View for donor to chat with a specific hospital"""
    # Ensure only donor users can access this view
    if not hasattr(request.user, 'donor_profile'):
        messages.error(request, 'Unauthorized access')
        return redirect('home')

    hospital = get_object_or_404(Hospital, id=hospital_id)
    donor = request.user.donor_profile

    # Get messages between this donor and hospital
    message_thread = Message.objects.filter(
        (Q(sender=request.user, recipient=hospital.user) | 
         Q(sender=hospital.user, recipient=request.user))
    ).order_by('timestamp')

    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content:
            Message.objects.create(
                sender=request.user,
                recipient=hospital.user,
                content=message_content,
                sender_type='donor' if hasattr(request.user, 'donor_profile') else 'hospital'
            )
            messages.success(request, 'Message sent successfully')
            return redirect('donor_hospital_chat', hospital_id=hospital_id)

    context = {
        'hospital': hospital,
        'donor': donor,
        'messages': message_thread,
    }
    return render(request, 'messaging/donor_hospital_chat.html', context)

#-------------------------------------------------------------------------
#-------------------------------------------------------------------------
#-------------------------------------------------------------------------
#-----------------------Donor_views---------------------------------------



def donor_register(request):
    if request.method == 'POST':
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('donor_login')
    else:
        form = DonorRegistrationForm()
    
    return render(request, 'donor/register.html', {'form': form})

def donor_login(request):
    if request.method == 'GET':
        next_page = request.GET.get('next')
        context = {'next': next_page}
        return render(request, 'donor/login.html', context)
    
    username = request.POST.get('username')
    password = request.POST.get('password')

    # Check if the username exists
    if not User.objects.filter(username=username).exists():
        context = {
            'error': 'User does not exist',
            'next': request.POST.get('next')
        }
        return render(request, 'donor/login.html', context)

    # If the username exists, authenticate the user
    user = authenticate(username=username, password=password)
    if user and hasattr(user, 'donor_profile'):
        auth_login(request, user)
        next_page = request.POST.get('next', 'donor_home')
        return redirect(next_page)
    else:
        context = {
            'error': 'Incorrect password',
            'next': request.POST.get('next')
        }
        return render(request, 'donor/login.html', context)
    
@login_required
def donor_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def donor_home(request):
    latest_blogs = Blog.objects.all().order_by('-created_at')[:9]
    
    # Get recent messages to this donor
    recent_messages = Message.objects.filter(
        recipient=request.user
    ).order_by('-timestamp')[:5]
    
    context = {
        'latest_blogs': latest_blogs,
        'recent_messages': recent_messages
    }
    return render(request, 'donor/donor_home.html', context)

@login_required
def donor_profile(request):
    donor = request.user.donor_profile

    # Fetch organ donation history (completed donations)
    organ_donation_history = OrganRequest.objects.filter(
        status='fulfilled',
        matched_donor__donor=donor
    ).select_related('hospital', 'organ_type').order_by('-updated_at')

    # Fetch blood donation history
    blood_donation_history = BloodDonation.objects.filter(
        donor=donor
    ).select_related('blood_request').order_by('-donation_date')

    context = {
        'organ_donation_history': organ_donation_history,
        'blood_donation_history': blood_donation_history,
        'donor': donor,
    }
    return render(request, 'donor/profile.html', context)


@login_required
def edit_donor_profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        donor_form = DonorUpdateForm(request.POST, request.FILES, instance=request.user.donor_profile)
        
        if user_form.is_valid() and donor_form.is_valid():
            user_form.save()
            donor_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('donor_profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        donor_form = DonorUpdateForm(instance=request.user.donor_profile)
    
    context = {
        'user_form': user_form,
        'donor_form': donor_form
    }
    return render(request, 'donor/edit_profile.html', context)



#-----------Donor_blood________________

@login_required
def donor_blood_requests(request):
    donor = request.user.donor_profile
    current_date = timezone.now()
    
    # Get active matching blood requests
    matching_requests = BloodRequest.objects.filter(
        blood_group=donor.blood_group,
        status='pending',
        required_by__gte=current_date
    ).order_by('required_by')
    
    # Get active district requests with different blood group
    district_requests = BloodRequest.objects.filter(
        hospital__district=donor.district,
        status='pending',
        required_by__gte=current_date
    ).exclude(
        blood_group=donor.blood_group
    ).order_by('required_by')
    
    # Get expired requests
    expired_requests = BloodRequest.objects.filter(
        required_by__lt=current_date,
        status='pending'
    ).order_by('-required_by')
    
    # Get responded requests
    responded_requests = BloodRequest.objects.filter(
        donorresponse__donor=donor
    ).select_related('hospital').order_by('-donorresponse__created_at')
    
    # Get helped requests
    helped_requests = BloodRequest.objects.filter(
        donorhelp__donor=donor
    ).select_related('hospital').order_by('-donorhelp__created_at')
    
    context = {
        'matching_requests': matching_requests,
        'district_requests': district_requests,
        'expired_requests': expired_requests,
        'responded_requests': responded_requests,
        'helped_requests': helped_requests
    }
    return render(request, 'donor/blood_requests.html', context)

@login_required
def respond_to_request(request, request_id):
    if request.method == 'POST':
        donor = request.user.donor_profile
        blood_request = get_object_or_404(BloodRequest, id=request_id)
        
        if not donor.is_eligible_to_donate():
            return JsonResponse({
                'status': 'error',
                'message': f'You will be eligible to donate after {donor.days_until_eligible()} days'
            }, status=400)
        
        # Create donor response if not already exists
        DonorResponse.objects.get_or_create(
            donor=donor,
            blood_request=blood_request,
            defaults={'status': 'pending'}
        )
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)



@login_required
def offer_help(request, request_id):
    if request.method == 'POST':
        blood_request = get_object_or_404(BloodRequest, id=request_id)
        DonorHelp.objects.create(
            donor=request.user.donor_profile,
            blood_request=blood_request,
            message=request.POST.get('message', '')
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)



#----------------------------------------organ donation-------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------




@login_required
def register_organ_donor(request):
    if request.method == 'GET':
        # Pass organ types to template for rendering
        organ_types = OrganType.objects.filter(is_active=True).order_by('category', 'name')
        return render(request, 'organ_donation/register.html', {'organ_types': organ_types})
    
    elif request.method == 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                selected_organs = data.get('organs', [])
                
                if not selected_organs:
                    return JsonResponse({
                        'success': False,
                        'message': 'Please select at least one organ or tissue to donate.'
                    })
                
                # Convert string IDs to integers
                selected_organs = [int(id) for id in selected_organs]
                
                # Get or create organ donor profile
                organ_donor, created = OrganDonor.objects.get_or_create(
                    donor=request.user.donor_profile,
                    defaults={'agreed_to_donate': True}
                )
                
                # Get organ types and update selection
                organ_types = OrganType.objects.filter(id__in=selected_organs, is_active=True)
                organ_donor.organs.set(organ_types)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Registration successful!'
                })
                
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid data format.'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'An error occurred: {str(e)}'
                })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })

@login_required
def matching_organ_requests(request):
    donor = request.user.donor_profile
    try:
        organ_donor = OrganDonor.objects.get(donor=donor)
    except OrganDonor.DoesNotExist:
        messages.error(request, "You need to register as an organ donor first.")
        return redirect('register_organ_donor')

    current_date = timezone.now()
    
    # List of non-repeatable organs
    NON_REPEATABLE_ORGANS = ['Kidney', 'Liver', 'Pancreas', 'Intestine']
    
    # Get organs the donor has already donated
    donated_organs = OrganRequest.objects.filter(
        matched_donor=organ_donor,
        status='fulfilled'
    ).values_list('organ_type__name', flat=True).distinct()
    
    # Filter out non-repeatable organs if the donor has already donated them
    excluded_organs = []
    for organ in donated_organs:
        if organ in NON_REPEATABLE_ORGANS:
            excluded_organs.append(organ)
    
    # Get matching requests based on blood group and registered organs
    matching_requests = OrganRequest.objects.filter(
        patient_blood_group=donor.blood_group,
        organ_type__in=organ_donor.organs.all(),
        status='pending',
        hospital__district=donor.district  # Prioritize local requests
    ).exclude(
        organ_type__name__in=excluded_organs  # Exclude non-repeatable organs
    ).select_related('hospital', 'organ_type').order_by('-urgency_level', 'created_at')
    
    # Get other district requests
    other_district_requests = OrganRequest.objects.filter(
        patient_blood_group=donor.blood_group,
        organ_type__in=organ_donor.organs.all(),
        status='pending'
    ).exclude(
        hospital__district=donor.district
    ).exclude(
        organ_type__name__in=excluded_organs  # Exclude non-repeatable organs
    ).select_related('hospital', 'organ_type').order_by('-urgency_level', 'created_at')
    
    # Get requests where this donor is matched
    matched_requests = OrganRequest.objects.filter(
        status='matched',
        matched_donor=organ_donor
    ).select_related('hospital', 'organ_type').order_by('-updated_at')
    
    # Get requests where this donor has fulfilled (completed donations)
    completed_donations = OrganRequest.objects.filter(
        status='fulfilled',
        matched_donor=organ_donor
    ).select_related('hospital', 'organ_type').order_by('-updated_at')
    
    context = {
        'matching_requests': matching_requests,
        'other_district_requests': other_district_requests,
        'matched_requests': matched_requests,
        'completed_donations': completed_donations,
        'donor': donor,
        'organ_donor': organ_donor
    }
    return render(request, 'organ_donation/matching_requests.html', context)



from django.views.decorators.http import require_http_methods

@login_required
@require_http_methods(["GET", "POST"])
def create_organ_request(request):
    # Check if user is associated with a hospital
    try:
        hospital = request.user.hospital_profile
    except Hospital.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Access denied. Only hospital users can create organ requests.'
        })

    if request.method == 'GET':
        # Get active organ types and blood group choices for the form
        context = {
            'organ_types': OrganType.objects.filter(is_active=True).order_by('category', 'name'),
            'blood_group_choices': Donor.BLOOD_GROUP_CHOICES,
        }
        return render(request, 'organ_donation/create_request.html', context)
    
    elif request.method == 'POST':
        try:
            # Create new organ request
            organ_request = OrganRequest(
                hospital=hospital,
                organ_type_id=request.POST.get('organ_type'),
                patient_name=request.POST.get('patient_name'),
                patient_age=request.POST.get('patient_age'),
                patient_blood_group=request.POST.get('patient_blood_group'),
                urgency_level=request.POST.get('urgency_level'),
                medical_notes=request.POST.get('medical_notes'),
                status='pending'
            )
            organ_request.save()

            return JsonResponse({
                'success': True,
                'message': 'Organ request created successfully!'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating request: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })


@login_required
def organ_request_list(request):
    # Active organ requests
    active_requests = OrganRequest.objects.filter(
        hospital=request.user.hospital_profile,
        status__in=['pending', 'matched'],
    ).order_by('-created_at')
    
    # Historical requests (fulfilled or cancelled)
    history_requests = OrganRequest.objects.filter(
        hospital=request.user.hospital_profile,
        status__in=['fulfilled', 'cancelled']
    ).order_by('-created_at')
    
    context = {
        'requests': active_requests,
        'history_requests': history_requests,
    }
    
    return render(request, 'organ_donation/organ_request_list.html', context)



from datetime import datetime
@login_required
def organ_request_detail(request, request_id):
    """
    View function for displaying the details of a specific organ request.
    Includes matching donors and request statistics.
    """
    # Get the organ request or return 404
    organ_request = get_object_or_404(OrganRequest, id=request_id)

    # Ensure the user has permission to view this request
    if organ_request.hospital != request.user.hospital_profile:
        messages.error(request, "You don't have permission to view this request.")
        return redirect('organ_request_list')

    # Get all donors who have already donated or been matched for the same organ type
    excluded_donors = OrganRequest.objects.filter(
        organ_type=organ_request.organ_type,
        status='fulfilled'
    ).values_list('matched_donor', flat=True)

    # Filter matching donors based on organ type, blood group, and exclude donors who have already donated
    matching_donors = OrganDonor.objects.filter(
        organs=organ_request.organ_type,  # Match organ type
        donor__blood_group=organ_request.patient_blood_group,  # Match blood group
        is_active=True,
        agreed_to_donate=True
    ).exclude(
        id__in=excluded_donors  # Exclude donors who have already donated
    ).select_related('donor')  # Include related Donor objects

    # Automatically update status to Matched if there are matching donors and status is pending
    if matching_donors.count() > 0 and organ_request.status == 'pending':
        organ_request.status = 'matched'
        organ_request.save()

    # Calculate statistics
    stats = {
        'potential_matches_count': matching_donors.count(),
        'days_active': (datetime.now().date() - organ_request.created_at.date()).days
    }

    context = {
        'organ_request': organ_request,
        'matching_donors': matching_donors,
        'stats': stats,
    }

    return render(request, 'organ_donation/organ_request_detail.html', context)

@login_required
def update_organ_request_status(request, request_id):
    """
    View function for fulfilling an organ request by selecting a donor.
    """
    # Get the organ request or return 404
    organ_request = get_object_or_404(OrganRequest, id=request_id)

    # Ensure the user has permission to update this request
    if organ_request.hospital != request.user.hospital_profile:
        messages.error(request, "You don't have permission to update this request.")
        return redirect('organ_request_list')

    if request.method == 'POST':
        donor_id = request.POST.get('donor_id')

        # Validate donor
        try:
            donor = OrganDonor.objects.get(id=donor_id)
        except OrganDonor.DoesNotExist:
            messages.error(request, "Invalid donor selected.")
            return redirect('organ_request_detail', request_id=request_id)

        # Update the organ request
        organ_request.matched_donor = donor
        organ_request.status = 'fulfilled'
        organ_request.save()

        # Add a success message
        messages.success(request, "Organ request status updated to Fulfilled.")
        return redirect('organ_request_detail', request_id=request_id)

    # If not a POST request, redirect to the detail page
    return redirect('organ_request_detail', request_id=request_id)

@require_POST
@login_required
def edit_organ_request(request, request_id):
    """
    Handle the editing of an organ request.
    Allows editing of pending and matched requests.
    """
    organ_request = get_object_or_404(
        OrganRequest,
        id=request_id,
        hospital=request.user.hospital_profile
    )
   
    # Allow editing for both pending and matched statuses
    if organ_request.status not in ['pending', 'matched']:
        messages.error(request, 'Only pending or matched requests can be edited.')
        return redirect('organ_request_detail', request_id=request_id)
   
    try:
        # Get form data with validation
        patient_name = request.POST.get('patient_name', '').strip()
        if not patient_name:
            raise ValueError("Patient name cannot be empty")
            
        patient_age = int(request.POST.get('patient_age', 0))
        if not (0 <= patient_age <= 120):
            raise ValueError("Patient age must be between 0 and 120")
            
        medical_notes = request.POST.get('medical_notes', '').strip()
        urgency_level = int(request.POST.get('urgency_level', 1))
        if urgency_level not in [1, 2, 3]:
            raise ValueError("Invalid urgency level")
            
        # Get blood group and validate
        patient_blood_group = request.POST.get('patient_blood_group')
        valid_blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if patient_blood_group not in valid_blood_groups:
            raise ValueError("Invalid blood group")
        
        # Update fields
        organ_request.patient_name = patient_name
        organ_request.patient_age = patient_age
        organ_request.medical_notes = medical_notes
        organ_request.urgency_level = urgency_level
        organ_request.patient_blood_group = patient_blood_group
       
        organ_request.save()
        messages.success(request, 'Organ request updated successfully.')
       
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Error updating request: {str(e)}')
   
    return redirect('organ_request_detail', request_id=request_id)

@require_POST
@login_required
def cancel_organ_request(request, request_id):
    """
    Handle the cancellation of an organ request.
    Allows cancellation of pending and matched requests.
    """
    organ_request = get_object_or_404(
        OrganRequest,
        id=request_id,
        hospital=request.user.hospital_profile
    )
   
    # Allow cancellation for both pending and matched statuses
    if organ_request.status in ['pending', 'matched']:
        try:
            organ_request.status = 'cancelled'
            organ_request.save()
            messages.success(request, 'Organ request cancelled successfully.')
        except Exception as e:
            messages.error(request, f'Error cancelling request: {str(e)}')
    else:
        messages.error(request, 'Only pending or matched requests can be cancelled.')
   
    return redirect('organ_request_list')

@require_POST
@login_required
def match_organ_donor(request, request_id):
    """
    Handle matching a donor to an organ request.
    Updates both the request and donor status.
    """
    organ_request = get_object_or_404(OrganRequest, 
                                    id=request_id,
                                    hospital=request.user.hospital_profile)
    
    if organ_request.status != 'pending':
        messages.error(request, 'Only pending requests can be matched with donors.')
        return redirect('organ_request_detail', request_id=request_id)
    
    donor_id = request.POST.get('donor_id')
    
    try:
        donor = OrganDonor.objects.get(id=donor_id, status='pending')
        
        # Update request and donor status
        organ_request.status = 'matched'
        organ_request.matched_donor = donor
        organ_request.save()
        
        messages.success(request, 'Donor matched successfully.')
        
    except OrganDonor.DoesNotExist:
        messages.error(request, 'Selected donor is no longer available.')
    except Exception as e:
        messages.error(request, f'Error matching donor: {str(e)}')
    
    return redirect('organ_request_detail', request_id=request_id)

from django.http import HttpResponse
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from io import BytesIO

def download_certificate(request, donation_id):
    # Fetch the donation details
    donation = OrganRequest.objects.get(id=donation_id)

    # Create a BytesIO buffer to store the PDF
    buffer = BytesIO()

    # Create the PDF object with landscape orientation
    pdf = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()

    # Custom styles for the certificate
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Title'],
        fontSize=36,  # Larger font size for the title
        alignment=1,  # Center alignment
        spaceAfter=20,
        textColor=colors.darkblue,  # Dark blue color for the title
    )
    donor_style = ParagraphStyle(
        name='DonorStyle',
        parent=styles['BodyText'],
        fontSize=24,  # Larger font size for the donor name
        alignment=1,  # Center alignment
        spaceAfter=20,
        textColor=colors.darkgreen,  # Dark green color for the donor name
    )
    details_style = ParagraphStyle(
        name='DetailsStyle',
        parent=styles['BodyText'],
        fontSize=18,  # Larger font size for details
        alignment=1,  # Center alignment
        spaceAfter=10,
    )
    appreciation_style = ParagraphStyle(
        name='AppreciationStyle',
        parent=styles['BodyText'],
        fontSize=16,  # Larger font size for the appreciation note
        alignment=1,  # Center alignment
        spaceAfter=20,
        textColor=colors.darkblue,  # Dark blue color for the appreciation note
        leading=20,  # Line spacing for better readability
    )
    signature_style = ParagraphStyle(
        name='SignatureStyle',
        parent=styles['BodyText'],
        fontSize=14,  # Font size for the signature
        alignment=1,  # Center alignment
        spaceBefore=20,
    )

    # Content for the certificate
    content = []

    # Add a decorative header (optional)
    header_text = "Certificate of Appreciation"
    header = Paragraph(header_text, title_style)
    content.append(header)
    content.append(Spacer(1, 40))

    # Add the donor's name
    donor = donation.matched_donor.donor  # Access the Donor object
    user = donor.user  # Access the associated User object
    donor_name = Paragraph(f"<b>Presented to:</b> {user.first_name} {user.last_name}", donor_style)
    content.append(donor_name)
    content.append(Spacer(1, 30))

    # Add the organ donated
    organ_donated = Paragraph(f"<b>Organ Donated:</b> {donation.organ_type.name}", details_style)
    content.append(organ_donated)
    content.append(Spacer(1, 15))

    # Add the hospital name
    hospital_name = Paragraph(f"<b>Hospital:</b> {donation.hospital.name}", details_style)
    content.append(hospital_name)
    content.append(Spacer(1, 15))

    # Add the donation date
    donation_date = Paragraph(f"<b>Donation Date:</b> {donation.updated_at.strftime('%B %d, %Y')}", details_style)
    content.append(donation_date)
    content.append(Spacer(1, 30))

    # Add an appreciation note
    appreciation_note = Paragraph(
        "We sincerely appreciate your selfless act of organ donation. Your contribution has made a significant impact on someone's life. Thank you for your generosity and kindness.",
        appreciation_style
    )
    content.append(appreciation_note)

    # Add a signature section
    signature_line = "___________________________"
    signature_text = Paragraph(f"<b>{signature_line}</b><br/><br/><b>Authorized Signature</b>", signature_style)
    content.append(signature_text)

    # Build the PDF
    pdf.build(content)

    # File response with the PDF
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="donation_certificate_{donation.id}.pdf"'
    return response


@login_required
def organ_donor_list(request):
    # Start with all active organ donors
    organ_donors = OrganDonor.objects.filter(is_active=True, agreed_to_donate=True)
    
    # Apply filters
    blood_group = request.GET.get('blood_group')
    district = request.GET.get('district')
    organ_type = request.GET.get('organ_type')
    tissue_type = request.GET.get('tissue_type')
    
    if blood_group:
        organ_donors = organ_donors.filter(donor__blood_group=blood_group)
    
    if district:
        organ_donors = organ_donors.filter(donor__district=district)
    
    if organ_type:
        organ_donors = organ_donors.filter(organs__id=organ_type)
    
    if tissue_type:
        organ_donors = organ_donors.filter(organs__id=tissue_type)
    
    # Get unique organ types for the filter dropdown
    organ_types = OrganType.objects.filter(category='organ').distinct()
    tissue_types = OrganType.objects.filter(category='tissue').distinct()

    
    context = {
        'organ_donors': organ_donors,
        'blood_groups': Donor.BLOOD_GROUP_CHOICES,
        'districts': Donor.PLACE_CHOICES,
        'organ_types': organ_types,
        'tissue_types': tissue_types,
    }
    return render(request, 'hospital/organ_donor_list.html', context)



@login_required
def donor_detail(request, donor_id):
    # Ensure only hospital users can access this view
    if not hasattr(request.user, 'hospital_profile'):
        messages.error(request, 'Unauthorized access')
        return redirect('home')
    
    # Get the donor object
    donor = get_object_or_404(Donor, id=donor_id)
    
    # Get associated organ donor profile if it exists
    organ_donor = OrganDonor.objects.filter(donor=donor).first()
    
    # Get donation history
    blood_donations = BloodDonation.objects.filter(donor=donor).order_by('-donation_date')
    
    # Get matched organ requests (only if organ_donor exists)
    matched_requests = []
    active_organ_requests = []
    
    if organ_donor:
        matched_requests = OrganRequest.objects.filter(
            matched_donor=organ_donor
        ).order_by('-updated_at')
        
        # Get active organ requests that might be relevant for this donor
        hospital = request.user.hospital_profile
        active_organ_requests = OrganRequest.objects.filter(
            hospital=hospital,
            status__in=['pending'],
            patient_blood_group=donor.blood_group
        )
        
        # Only filter by organ types if the donor has registered organs
        if organ_donor.organs.exists():
            active_organ_requests = active_organ_requests.filter(
                organ_type__in=organ_donor.organs.all()
            )
    
    # Get active blood requests that this hospital has which might be relevant for this donor
    hospital = request.user.hospital_profile
    active_blood_requests = BloodRequest.objects.filter(
        hospital=hospital, 
        status__in=['pending', 'processing'],
        blood_group=donor.blood_group
    )
    
    # Get message thread between hospital and donor
    messages_thread = Message.objects.filter(
        (Q(sender=request.user, recipient=donor.user) | 
         Q(sender=donor.user, recipient=request.user))
    ).order_by('timestamp')
    
    # Count unread messages
    unread_count = messages_thread.filter(
        recipient=request.user,
        status='unread'
    ).count()
    
    # Mark messages as read when viewing the detail page
    messages_thread.filter(
        recipient=request.user,
        status='unread'
    ).update(status='read')
    
    context = {
        'donor': donor,
        'organ_donor': organ_donor,
        'blood_donations': blood_donations,
        'matched_requests': matched_requests,
        'active_blood_requests': active_blood_requests,
        'active_organ_requests': active_organ_requests,
        'messages_thread': messages_thread,
        'unread_count': unread_count,
    }
    
    return render(request, 'hospital/donor_detail.html', context)


from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import letter

@login_required
def download_blood_requests_pdf(request):
    # Fetch blood requests for the logged-in hospital
    blood_requests = BloodRequest.objects.filter(hospital=request.user.hospital_profile)

    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="blood_requests.pdf"'

    # Create the PDF object
    pdf = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Add a title
    elements.append(Paragraph("Blood Requests Report", styles['Title']))

    # Prepare data for the table
    data = [['Patient Name', 'Blood Group', 'Units Required', 'Status', 'Created At']]
    for request in blood_requests:
        data.append([
            request.patient_name,
            request.blood_group,
            request.units_required,
            request.status,
            request.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    # Create the table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Add the table to the elements
    elements.append(table)

    # Build the PDF
    pdf.build(elements)
    return response


@login_required
def download_organ_requests_pdf(request):
    # Fetch organ requests for the logged-in hospital
    organ_requests = OrganRequest.objects.filter(hospital=request.user.hospital_profile)

    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="organ_requests.pdf"'

    # Create the PDF object
    pdf = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Add a title
    elements.append(Paragraph("Organ Requests Report", styles['Title']))

    # Prepare data for the table
    data = [['Patient Name', 'Organ Type', 'Blood Group', 'Urgency Level', 'Status', 'Created At']]
    for request in organ_requests:
        data.append([
            request.patient_name,
            request.organ_type.name,
            request.patient_blood_group,
            request.get_urgency_level_display(),
            request.status,
            request.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    # Create the table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Add the table to the elements
    elements.append(table)

    # Build the PDF
    pdf.build(elements)
    return response

import json
import os
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key with fallback for direct setting
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client if API key is available
groq_client = None
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    print("WARNING: GROQ_API_KEY is missing! Chatbot functionality will be limited.")



@require_http_methods(["GET", "POST"])
def chatbot(request):
    """Handle chatbot requests - GET for resetting chat, POST for processing messages."""
    
    # Reset chat history on GET request
    if request.method == 'GET':
        request.session['chat_history'] = []
        return JsonResponse({'status': 'Chat history reset'})
    
    # Process chat message on POST
    try:
        # Read JSON request body
        data = json.loads(request.body.decode('utf-8'))  
        user_input = data.get('user_input', '').strip()
        
        if not user_input:
            return JsonResponse({'response': 'Please enter a valid message.'})
        
        # Initialize chat history if not present
        if 'chat_history' not in request.session:
            request.session['chat_history'] = []
        
        chat_history = request.session['chat_history']
        
        # Add user message to history
        chat_history.append({"role": "user", "content": user_input})
        
        # Define system prompt with extremely strict boundaries
        SYSTEM_PROMPT = """
        You are a highly specialized chatbot ONLY for blood donation and organ donation information.
        
        CRITICAL INSTRUCTION: You must STRICTLY follow these rules:
        
        1. ONLY answer questions directly related to blood donation and organ donation.
        
        2. For ANY question not DIRECTLY about donation (including greetings only, small talk, 
           geography, general medicine, world facts, etc.), ALWAYS respond EXACTLY with:
           "I'm sorry, I can only provide information about blood and organ donation. If you have 
           questions about donation, I'm happy to help!"
        
        3. DO NOT answer questions about:
           - Geography, countries, cities, or capitals
           - General medical advice unrelated to donation
           - Current events or news
           - Technology, science, or other topics
           - ANY topic not specifically about blood or organ donation
        
        4. Even if a question seems innocent or simple, if it's not directly about 
           donation, use the standard response.
           
        5. For basic greetings like "hi" or "hello", you may briefly introduce yourself 
           and ask how you can help with donation information.
        
        This is a ZERO TOLERANCE policy. Any deviation will result in immediate termination.
        """
        
        # Construct messages for Groq API
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history
        
        # Add a forced classification step
        classification_prompt = {
            "role": "user", 
            "content": f"""
            Analyze if this question is STRICTLY related to blood donation or organ donation: "{user_input}"
            
            If there is ANY doubt, classify as UNRELATED.
            Respond with EXACTLY ONE WORD, either "RELATED" or "UNRELATED":
            """
        }
        
        # Call Groq API for classification
        try:
            if groq_client:
                classification = groq_client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, classification_prompt],
                    max_tokens=10,
                    temperature=0.0
                )
                
                classification_result = classification.choices[0].message.content.strip().upper()
                
                # Force default response for unrelated topics
            if "UNRELATED" in classification_result or not "RELATED" in classification_result:
                standard_response = "I'm sorry, I can only provide information about blood and organ donation. If you have questions about donation, I'm happy to help!"
                
                # Add response to history
                chat_history.append({"role": "assistant", "content": standard_response})
                request.session['chat_history'] = chat_history
                
                return JsonResponse({'response': standard_response})
            
            # Continue with regular processing for related questions
            if groq_client:
                chat_completion = groq_client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=messages,
                    max_tokens=500,
                    temperature=0.2  # Even lower temperature
                )
                response = chat_completion.choices[0].message.content
            else:
                response = "I'm not fully operational right now. Please check back later."
            
        except Exception as e:
            print(f"Error with Groq API: {str(e)}")
            response = "I'm having trouble processing your request. Please try again with a question about blood or organ donation."
        
        # Add bot response to history
        chat_history.append({"role": "assistant", "content": response})
        
        # Keep history manageable
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
        
        request.session['chat_history'] = chat_history
        
        return JsonResponse({'response': response})
        
    except json.JSONDecodeError:
        return JsonResponse({'response': 'There was an error processing your request.'}, status=400)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({'response': 'An unexpected error occurred.'}, status=500)

# Optional: Add a simple page to test the chatbot
def chatbot_test_page(request):
    """Render a simple test page for the chatbot."""
    return render(request, 'chatbot_test.html')


import os
import joblib
import numpy as np
import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse
from .forms import KidneyDiseaseForm

# Load the model and scaler
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "core", "model", "kidney_disease_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "core", "model", "scaler.pkl")

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

def predict_kidney_disease_view(request):
    prediction = None
    probability = None
    suggestions = []

    if request.method == "POST":
        form = KidneyDiseaseForm(request.POST)
        if form.is_valid():
            # Extract cleaned data from the form
            age = form.cleaned_data["age"]
            gender = int(form.cleaned_data["gender"])
            diabetic = int(form.cleaned_data["diabetic"])
            smoker = int(form.cleaned_data["smoker"])
            drinker = int(form.cleaned_data["drinker"])
            bmi = form.cleaned_data["bmi"]
            family_history = int(form.cleaned_data["family_history"])

            # Prepare input for the model
            input_data = np.array([[age, gender, diabetic, smoker, drinker, bmi, family_history]])
            input_df = pd.DataFrame(input_data, columns=[
                "Age", "Gender", "Diabetic", "Smoker", "Drinker", "BMI", "FamilyHistoryKidneyDisease"
            ])

            # Scale the input
            input_scaled = scaler.transform(input_df)

            # Make prediction
            prediction_result = model.predict(input_scaled)[0]
            model_probability = model.predict_proba(input_scaled)[:, 1][0] * 100  # Probability

            # Risk analysis
            risk_factors = {
                "Age": age > 50,
                "Gender": gender == 1,
                "Diabetic": diabetic == 1,
                "Smoker": smoker == 1,
                "Drinker": drinker == 1,
                "High BMI": bmi > 30,
                "Family History": family_history == 1
            }
            num_risk_factors = sum(risk_factors.values())
            factor_contribution = (num_risk_factors / len(risk_factors)) * 100  # Risk contribution

            # Adjust final probability based on risk factors
            final_probability = (model_probability * 0.6) + (factor_contribution * 0.4)
            prediction = "High Risk" if final_probability > 50 else "Low Risk"
            probability = round(final_probability, 2)

            # Provide suggestions based on risk factors
            if risk_factors["Age"]:
                suggestions.append("Consider regular kidney screenings due to your age.")
            if risk_factors["Diabetic"]:
                suggestions.append("If you are diabetic, managing your blood sugar can help reduce the risk.")
            if risk_factors["Smoker"]:
                suggestions.append("Quitting smoking can greatly reduce your kidney disease risk.")
            if risk_factors["Drinker"]:
                suggestions.append("Limiting alcohol consumption is recommended for kidney health.")
            if risk_factors["High BMI"]:
                suggestions.append("Maintaining a healthy weight through diet and exercise can help.")
            if risk_factors["Family History"]:
                suggestions.append("Regular check-ups are crucial due to family history.")
            
            # For AJAX requests, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "prediction": prediction,
                    "probability": probability,
                    "suggestions": suggestions
                })
        else:
            # If the form is not valid and it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"error": "Invalid form data"}, status=400)
            
            # If it's a regular request
            return render(request, "predict.html", {"form": form})

    else:
        form = KidneyDiseaseForm()

    return render(request, "predict.html", {
        "form": form,
        "prediction": prediction,
        "probability": probability,
        "suggestions": suggestions
    })



from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings

def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            # Check if user exists with this email
            user_exists = User.objects.filter(email=email).exists()
            
            if not user_exists:
                messages.error(request, "This email is not registered in our system.")
                return render(request=request, template_name="password_reset.html", context={"form": form})
            
            # If user exists, send email
            user = User.objects.get(email=email)
            
            # Check if user is donor or hospital
            user_type = None
            try:
                donor = user.donor_profile
                user_type = "donor"
            except:
                try:
                    hospital = user.hospital_profile
                    user_type = "hospital"
                except:
                    pass
            
            # Generate token and encoded user ID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build password reset link
            reset_url = request.build_absolute_uri(f'/password-reset-confirm/{uid}/{token}/')
            
            # Create email content
            subject = "Password Reset Request"
            email_template_name = "password_reset_email.html"
            context = {
                "email": user.email,
                "user_type": user_type,
                "reset_url": reset_url,
                "site_name": "Blood Donation System",
            }
            email_content = render_to_string(email_template_name, context)
            
            try:
                send_mail(subject, email_content, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)
                return redirect("password_reset_done")
            except BadHeaderError:
                return HttpResponse("Invalid header found.")
            
    else:
        form = PasswordResetForm()
    return render(request=request, template_name="password_reset.html", context={"form": form})

def password_reset_done(request):
    return render(request=request, template_name="password_reset_done.html")

def password_reset_confirm(request, uidb64, token):
    try:
        # Decode the user ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    # Check if the token is valid
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                # Save the new password
                form.save()
                messages.success(request, "Your password has been changed successfully!")
                return redirect("password_reset_complete")
        else:
            form = SetPasswordForm(user)
        return render(request, "password_reset_confirm.html", {"form": form})
    else:
        # If token is invalid or expired
        messages.error(request, "The password reset link is invalid or has expired.")
        return redirect("password_reset")

def password_reset_complete(request):
    return render(request=request, template_name="password_reset_complete.html")