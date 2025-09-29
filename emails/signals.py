from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import EmailTemplate
from .snapshot import render_html_to_snapshot_content
from django.core.files.base import ContentFile

def _needs_snapshot(instance: EmailTemplate, old_html: str | None) -> bool:
    # Generate if missing OR body changed
    if not instance.snapshot:
        return True
    if old_html is None:
        return False
    return (instance.body_html or "").strip() != (old_html or "").strip()

@receiver(pre_save, sender=EmailTemplate)
def _cache_old_html(sender, instance: EmailTemplate, **kwargs):
    # Cache previous HTML so we can compare in post_save
    if instance.pk:
        try:
            prev = EmailTemplate.objects.only("body_html", "snapshot").get(pk=instance.pk)
            instance._old_body_html = prev.body_html
        except EmailTemplate.DoesNotExist:
            instance._old_body_html = None
    else:
        instance._old_body_html = None

@receiver(post_save, sender=EmailTemplate)
def generate_snapshot_after_save(sender, instance: EmailTemplate, created, **kwargs):
    try:
        old_html = getattr(instance, "_old_body_html", None)
        if _needs_snapshot(instance, old_html):
            content: ContentFile = render_html_to_snapshot_content(instance.body_html or "")
            # Give it a stable but unique-ish name
            filename = f"template_{instance.pk}.png"
            instance.snapshot.save(filename, content, save=True)
    except Exception as e:
        # Don’t crash the request if snapshot fails; log it
        import logging
        logging.getLogger(__name__).exception("Snapshot generation failed: %s", e)
