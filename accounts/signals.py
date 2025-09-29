from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # Create profile for new users
    if created:
        Profile.objects.create(
            user=instance,
            display_name=(instance.get_full_name() or instance.username)
        )
    else:
        # Ensure a profile exists for existing users too
        Profile.objects.get_or_create(
            user=instance,
            defaults={"display_name": (instance.get_full_name() or instance.username)}
        )
