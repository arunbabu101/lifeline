from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import *
from django.core.exceptions import ValidationError
from datetime import date
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm


class DonorAuthForm(AuthenticationForm):
    username = forms.EmailField(
        required=True, 
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class DonorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    district = forms.ChoiceField(
        choices=Donor.PLACE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    blood_group = forms.ChoiceField(
        choices=Donor.BLOOD_GROUP_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    weight = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    last_donated = forms.ChoiceField(
        choices=Donor.LAST_DONATED_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'district', 'blood_group', 'weight', 'last_donated', 'password1', 'password2']

    def clean_first_name(self):
        value = self.cleaned_data.get('first_name')
        if not re.match(r'^[a-zA-Z]+$', value):
            raise ValidationError("First name must contain only letters.")
        if len(value.strip()) < 4:
            raise ValidationError("First name must be at least 4 characters long.")
        return value.strip()

    def clean_last_name(self):
        value = self.cleaned_data.get('last_name')
        if not re.match(r'^[a-zA-Z]+$', value):
            raise ValidationError("Last name must contain only letters.")
        if len(value.strip()) < 2:
            raise ValidationError("Last name must be at least 2 characters long.")
        return value.strip()
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(username=email).exists():
            raise ValidationError("This email is already registered.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            raise ValidationError("Phone number must be 10 digits.")
        return phone

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight < 30 or weight > 200:
            raise ValidationError("Enter a valid weight between 30 and 200 kg.")
        return weight
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Set username as email
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Donor.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                district=self.cleaned_data['district'],
                blood_group=self.cleaned_data['blood_group'],
                weight=self.cleaned_data['weight'],
                last_donated=self.cleaned_data['last_donated'],
                is_blood_donor=True
            )
        return user

class DonorForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = ['district', 'blood_group', 'phone', 'weight', 'last_donated']
        widgets = {
            'district': forms.Select(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control'}),
            'last_donated': forms.Select(attrs={'class': 'form-control'})
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }



class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DonorUpdateForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = ['phone', 'district', 'weight', 'last_donated', 'profile_pic']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-select'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control'}),
            'last_donated': forms.Select(attrs={'class': 'form-select'}),
        }


#hospital forms

class HospitalRegistrationForm(UserCreationForm):
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    district = forms.ChoiceField(
        choices=Hospital.DISTRICT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    manager_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    manager_phone = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['name', 'email', 'district', 'phone', 'manager_name', 'manager_phone', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            raise ValidationError("Phone number must be 10 digits")
        if Hospital.objects.filter(phone=phone).exists():
            raise ValidationError("This phone number is already registered")
        return phone

    def clean_manager_phone(self):
        phone = self.cleaned_data.get('manager_phone')
        if not phone.isdigit() or len(phone) != 10:
            raise ValidationError("Manager's phone number must be 10 digits")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Hospital.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                district=self.cleaned_data['district'],
                phone=self.cleaned_data['phone'],
                email=self.cleaned_data['email'],
                manager_name=self.cleaned_data['manager_name'],
                manager_phone=self.cleaned_data['manager_phone']
            )
        return user

class HospitalProfileForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ['profile_picture', 'name', 'district', 'phone', 'email', 'manager_name', 'manager_phone']
        widgets = {
            'district': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'manager_name': forms.TextInput(attrs={'class': 'form-control'}),
            'manager_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

#blood requesting

class BloodRequestForm(forms.ModelForm):
    required_by = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': date.today().isoformat(),  # Set min attribute for frontend validation
        })
    )

    class Meta:
        model = BloodRequest
        fields = ['blood_group', 'units_required', 'patient_name', 'patient_age', 
                  'patient_gender', 'required_by', 'reason']
        widgets = {
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'units_required': forms.NumberInput(attrs={'class': 'form-control'}),
            'patient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'patient_gender': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_patient_age(self):
        patient_age = self.cleaned_data.get('patient_age')
        if patient_age > 101:
            raise ValidationError('Patient age must be less than or equal to 101.')
        return patient_age
    
    def clean_required_by(self):
        required_by = self.cleaned_data.get('required_by')
        if required_by < date.today():
            raise ValidationError('Required by date cannot be in the past.')
        return required_by

class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'category', 'featured_image', 'content', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'featured_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
        }



class MessageForm(forms.ModelForm):
    """
    Form for sending messages
    """
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 4, 
            'placeholder': 'Type your message here...'
        }),
        max_length=1000,
        required=True
    )

    class Meta:
        model = Message
        fields = ['content']

    def clean_content(self):
        content = self.cleaned_data['content']
        if len(content.strip()) == 0:
            raise forms.ValidationError("Message cannot be empty")
        return content
    


class OrganDonorRegistrationForm(forms.ModelForm):
    organs = forms.ModelMultipleChoiceField(
        queryset=OrganType.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = OrganDonor
        fields = ['organs']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Group organs by category for better organization
        self.fields['organs'].queryset = OrganType.objects.filter(is_active=True).order_by('category', 'name')

class KidneyDiseaseForm(forms.Form):
    age = forms.IntegerField(label="Age", min_value=1)
    gender = forms.ChoiceField(label="Gender", choices=[(0, "Female"), (1, "Male")])
    diabetic = forms.ChoiceField(label="Diabetic", choices=[(0, "No"), (1, "Yes")])
    smoker = forms.ChoiceField(label="Smoker", choices=[(0, "No"), (1, "Yes")])
    drinker = forms.ChoiceField(label="Drinker", choices=[(0, "No"), (1, "Yes")])
    bmi = forms.FloatField(label="BMI", min_value=10, max_value=50)
    family_history = forms.ChoiceField(label="Family History", choices=[(0, "No"), (1, "Yes")])



class PasswordResetForm(DjangoPasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your registered email'}),
        label="Email"
    )

class SetPasswordForm(DjangoSetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}),
        label="New Password"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}),
        label="Confirm New Password"
    )