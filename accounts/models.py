from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extending our User model so we can store extra fields"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution = models.CharField(max_length=100, default='')
    lab = models.CharField(max_length=100, default='')

    def __str__(self):
        return self.user.username


def create_profile(new_user, new_institution, new_lab):
    """Using the new User object created when a new user registers, we store extra info as a UserProfile"""
    user_profile = UserProfile.objects.create(user=new_user, institution=new_institution, lab=new_lab)
    user_profile.save()