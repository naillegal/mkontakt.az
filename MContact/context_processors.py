from .models import ContactInfo, Brand, User


def contact_info_processor(request):
    return {
        'contact_info': ContactInfo.objects.first(),
        'footer_brands': Brand.objects.all().order_by('-created_at')[:5],
    }

def user_context(request):
    uid = request.session.get("user_id")
    print("user_id from session:", uid)
    if uid:
        try:
            user = User.objects.get(pk=uid)
            print("user from DB:", user)
            return {"user": user}
        except User.DoesNotExist:
            pass
    return {"user": None}

