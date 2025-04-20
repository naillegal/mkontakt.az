from .models import ContactInfo, Brand, User


def contact_info_processor(request):
    return {
        'contact_info': ContactInfo.objects.first(),
        'footer_brands': Brand.objects.all().order_by('-created_at')[:5],
    }


def current_user(request):
    uid = request.session.get("user_id")
    if uid:
        try:
            return {"current_user": User.objects.get(pk=uid)}
        except User.DoesNotExist:
            pass
    return {"current_user": None}
