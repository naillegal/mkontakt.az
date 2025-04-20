import uuid
from .models import Cart, CartItem

def get_or_create_cart(request):
    if request.session.session_key is None:
        request.session.create()

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(
            user_id=request.session["user_id"])
        sess_key = request.session.get("cart_session_key")
        if sess_key and Cart.objects.filter(session_key=sess_key).exists():
            sess_cart = Cart.objects.get(session_key=sess_key)
            for item in sess_cart.items.all():
                CartItem.objects.update_or_create(
                    cart=cart, product=item.product,
                    defaults={"quantity": item.quantity},
                )
            sess_cart.delete()
            request.session.pop("cart_session_key")
        return cart
    sess_key = request.session.get("cart_session_key")
    if not sess_key:
        sess_key = uuid.uuid4().hex
        request.session["cart_session_key"] = sess_key
    cart, _ = Cart.objects.get_or_create(session_key=sess_key)
    return cart
