from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


# class UserProfileManager(models.Manager):
#     def get_queryset(self):
#         return super(UserProfileManager, self).get_queryset().filter(institution='UCSD')


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution = models.CharField(max_length=100, default='')
    lab = models.CharField(max_length=100, default='')

    # UCSD = UserProfileManager()

    def __str__(self):
        return self.user.username


def create_profile(new_user, new_institution, new_lab):
    user_profile = UserProfile.objects.create(user=new_user, institution=new_institution, lab=new_lab)
    user_profile.save()

# post_save.connect(create_profile, sender=User)
