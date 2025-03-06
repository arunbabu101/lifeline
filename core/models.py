from django.db import models
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.contrib.auth.models import User
import re
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

# Validators
def validate_password(value):
    if len(value) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    if not re.search(r'[A-Z]', value):
        raise ValidationError('Password must contain at least one uppercase letter.')
    if not re.search(r'[0-9]', value):
        raise ValidationError('Password must contain at least one digit.')
    if not re.search(r'[\W_]', value):
        raise ValidationError('Password must contain at least one special character.')

def validate_weight(value):
    if value <= 45 or value > 150:
        raise ValidationError('Weight must be between 45 and 150 kg.')

class Donor(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    PLACE_CHOICES = [
        ('Alappuzha','Alappuzha'),
        ('Ernakulam','Ernakulam'),
        ('Idukki','Idukki'),
        ('Kannur','Kannur'),
        ('Kasaragod','Kasaragod'),
        ('Kollam','Kollam'),
        ('Kozhikode','Kozhikode'),
        ('Kottayam','Kottayam'),
        ('Malappuram','Malappuram'),
        ('Palakkad','Palakkad'),
        ('Pathanamthitta','Pathanamthitta'),
        ('Thiruvananthapuram','Thiruvananthapuram'),
        ('Thrissur','Thrissur'),
        ('Wayanad','Wayanad'),
    ]

    LAST_DONATED_CHOICES = [
        (1, '1 week'),
        (2, '2 weeks'),
        (3, '3 weeks'),
        (4, '4 weeks'),
        (5, '5 weeks'),
        (6, '6 weeks'),
        (7, '7 weeks'),
        (8, '8 weeks'),
    ]

    # Basic User Information (Similar to Customer model)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')
    profile_pic = models.ImageField(upload_to='donor_profile_pics/', null=True, blank=True)
    phone = models.CharField(max_length=10, unique=True)
    district = models.CharField(max_length=100, choices=PLACE_CHOICES)
    
    # Blood Donor Specific Fields
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    is_blood_donor = models.BooleanField(default=True)  # Changed default to True
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[validate_weight],
        help_text="Weight must be between 45 and 150 kg"
    )
    last_donated = models.IntegerField(
        choices=LAST_DONATED_CHOICES,
        help_text="Number of weeks since last donation"
    )
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def get_last_donated_date(self):
        """Get the actual last donation date from BloodDonation records or registration data"""
        latest_donation = self.blooddonation_set.order_by('-donation_date').first()
        
        if latest_donation:
            return latest_donation.donation_date
        else:
            # If no donations recorded, calculate from registration data
            weeks_ago = self.last_donated
            return timezone.now().date() - timedelta(weeks=weeks_ago)

    def is_eligible_to_donate(self):
        """Check if donor is eligible based on 56-day restriction"""
        last_donation_date = self.get_last_donated_date()
        days_since_donation = (timezone.now().date() - last_donation_date).days
        return days_since_donation >= 56

    def update_last_donated_weeks(self):
        """Update the last_donated field based on most recent BloodDonation"""
        latest_donation = self.blooddonation_set.order_by('-donation_date').first()
        if latest_donation:
            days_since_donation = (timezone.now().date() - latest_donation.donation_date).days
            weeks_since_donation = days_since_donation // 7
            
            # Ensure weeks_since_donation is within the valid range (1-8 weeks)
            if weeks_since_donation < 1:
                weeks_since_donation = 1  # Minimum 1 week
            elif weeks_since_donation > 8:
                weeks_since_donation = 8  # Maximum 8 weeks
            
            # Update the last_donated field
            self.last_donated = weeks_since_donation
            self.save()

    def clean(self):
        super().clean()
        if self.is_blood_donor:
            if not self.weight:
                raise ValidationError({'weight': 'Weight is required for blood donors'})
            if not self.last_donated:
                raise ValidationError({'last_donated': 'Last donated time is required for blood donors'})

    @property
    def get_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def get_id(self):
        return self.user.id
        
    def __str__(self):
        return self.get_name

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blood Donor'
        verbose_name_plural = 'Blood Donors'


# Hospital model
class Hospital(models.Model):
    DISTRICT_CHOICES = Donor.PLACE_CHOICES

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hospital_profile',default=1)
    profile_picture = models.ImageField(upload_to='hospital_profiles/', null=True, blank=True)
    name = models.CharField(max_length=255)
    district = models.CharField(choices=DISTRICT_CHOICES, max_length=100)
    phone = models.CharField(max_length=10, unique=True)
    email = models.EmailField(unique=True)
    manager_name = models.CharField(max_length=255,default="david")
    manager_phone = models.CharField(max_length=10,default=9999999999)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Hospital'
        verbose_name_plural = 'Hospitals'

# BlogCategory model
class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Blog Categories"

# Blog model
class Blog(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True)
    featured_image = models.ImageField(upload_to='blog_images/')
    content = RichTextField()
    author = models.ForeignKey(Hospital, on_delete=models.CASCADE)  # Changed to Donor model
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    tags = models.CharField(max_length=200, help_text="Comma separated tags")
    views = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(User, related_name='blog_likes', blank=True, default=0)
    dislikes = models.ManyToManyField(User, related_name='blog_dislikes', blank=True, default=0)

    def total_likes(self):
        return self.likes.count()

    def total_dislikes(self):
        return self.dislikes.count()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

# Comment model
class Comment(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Changed to Donor model
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.blog.title}'

#blood donations

class BloodRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='blood_requests')
    blood_group = models.CharField(max_length=3, choices=Donor.BLOOD_GROUP_CHOICES)
    units_required = models.PositiveIntegerField()
    patient_name = models.CharField(max_length=100)
    patient_age = models.PositiveIntegerField(max_length=3)
    patient_gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    required_by = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    blood_received = models.BooleanField(default=False)  # Default to False, meaning not received
    last_checked = models.DateField(null = True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.hospital.name} - {self.blood_group} - {self.status}"
    

class DonorResponse(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    blood_request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined')
    ], default='pending')

    class Meta:
        unique_together = ('donor', 'blood_request')

class DonorHelp(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    blood_request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True)

    class Meta:
        unique_together = ('donor', 'blood_request')


class BloodDonation(models.Model):

    blood_request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='donations')
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    donation_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blood_request', 'donor')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update donor's last_donated field after saving donation
        self.donor.update_last_donated_weeks()

    def __str__(self):
        return f"{self.donor.get_name()} - {self.blood_request.blood_group} - {self.donation_date}"
    

# Models to track donor contacts
class DonorContact(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    blood_request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    contacted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-contacted_at']



class Message(models.Model):
    """
    Model to handle messages between hospitals and donors
    """
    SENDER_TYPES = (
        ('hospital', 'Hospital'),
        ('donor', 'Donor')
    )

    STATUS_CHOICES = (
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived')
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unread')
    
    # Optional foreign keys to track context
    blood_request = models.ForeignKey('BloodRequest', on_delete=models.SET_NULL, null=True, blank=True)
    donor_contact = models.ForeignKey('DonorContact', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username} at {self.timestamp}"

class MessageNotification(models.Model):
    """
    Model to handle message notifications for users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'message')

    def __str__(self):
        return f"Notification for {self.user.username} about message {self.message.id}"
    

#-------------------------------------------------Organ donation ---------------------





class OrganType(models.Model):
    CATEGORY_CHOICES = [
        ('organ', 'Organ'),
        ('tissue', 'Tissue'),
        ('stem_cell', 'Stem Cell')
    ]

    ORGAN_CHOICES = [
        ('Kidney', 'Kidney'),
        ('Liver', 'Liver'),
        ('Pancreas', 'Pancreas'),
        ('Intestine', 'Intestine')
    ]

    TISSUE_CHOICES = [
        ('Bone marrow', 'Bone marrow'),
        ('Bone', 'Bone'),
        ('Corneas', 'Corneas'),
        ('Skin', 'Skin'),
        ('Tendons', 'Tendons'),
        ('Ligaments', 'Ligaments'),
        ('Cartilage', 'Cartilage'),
        ('Blood vessels', 'Blood vessels'),
        ('Nerves', 'Nerves')
    ]

    STEM_CELL_CHOICES = [
        ('Cord Blood Stem Cells', 'Cord Blood Stem Cells'),
        ('Peripheral Blood Stem Cells', 'Peripheral Blood Stem Cells'),
        ('Bone Marrow Stem Cells', 'Bone Marrow Stem Cells')
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

class OrganDonor(models.Model):
    donor = models.OneToOneField(Donor, on_delete=models.CASCADE, related_name='Organdonor')
    organs = models.ManyToManyField(OrganType, related_name='donors')
    is_active = models.BooleanField(default=True)
    agreed_to_donate = models.BooleanField(default=False)
    registration_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Organ Donor: {self.donor.get_name}"

class OrganRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('matched', 'Matched'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled')
    ]
    
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    organ_type = models.ForeignKey(OrganType, on_delete=models.CASCADE)
    patient_name = models.CharField(max_length=100)
    patient_age = models.PositiveIntegerField()
    patient_blood_group = models.CharField(max_length=3, choices=Donor.BLOOD_GROUP_CHOICES)
    urgency_level = models.IntegerField(choices=[(1, 'Normal'), (2, 'Urgent'), (3, 'Critical')])
    medical_notes = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    matched_donor = models.ForeignKey(OrganDonor, on_delete=models.SET_NULL, null=True, blank=True, related_name='matched_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.organ_type.name} request for {self.patient_name} at {self.hospital.name}"