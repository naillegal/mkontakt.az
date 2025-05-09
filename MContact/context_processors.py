from .models import ContactInfo, Brand, User


def contact_info_processor(request):
    return {
        "contact_info": ContactInfo.objects.first(),
        "footer_brands": Brand.objects.order_by("-created_at")[:5],
    }


def user_context(request):
    if request.path.startswith("/admin"):
        return {}

    uid = request.session.get("user_id")
    custom_user = None
    if uid:
        try:
            custom_user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            pass

    return {
        "user": custom_user
    }
