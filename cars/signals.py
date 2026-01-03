from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import CarImage

@receiver(post_delete, sender=CarImage)
def cleanup_car_image(sender, instance, **kwargs):
    """
    Deletes the file from Cloudinary/Storage when the image object is deleted.
    """
    if instance.image:
        try:
            # save=False prevents Django from trying to save the model again
            instance.image.delete(save=False)
        except Exception as e:
            # Log error but don't crash the deletion process
            print(f"Error deleting image file: {e}")

@receiver(pre_save, sender=CarImage)
def cleanup_pre_update(sender, instance, **kwargs):
    """
    If the image is being updated (replaced with a new one), 
    delete the old file from storage to prevent orphans.
    """
    if not instance.pk:
        return # It's a new object, nothing to replace

    try:
        old_instance = CarImage.objects.get(pk=instance.pk)
        old_image = old_instance.image
        new_image = instance.image

        # If there was an image, and it's different from the new one
        if old_image and old_image != new_image:
            old_image.delete(save=False)
            
    except CarImage.DoesNotExist:
        pass # Object not found, nothing to do