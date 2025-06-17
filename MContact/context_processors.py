from .models import ContactInfo, Brand, User, SiteConfiguration
from .utils import get_or_create_cart

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


def site_config(request):
    config = SiteConfiguration.objects.first()
    return {
        "site_config": config
    }

def cart_item_count(request):
    try:
        cart = get_or_create_cart(request)
        return {"cart_count": cart.items.count()}
    except Exception:
        return {"cart_count": 0}