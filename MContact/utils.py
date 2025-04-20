import uuid
from .models import Cart, CartItem


def get_or_create_cart(request):
    if not request.session.session_key:
        request.session.create()

    user_id = request.session.get('user_id')
    if user_id:
        cart, _ = Cart.objects.get_or_create(user_id=user_id)

        sess_key = request.session.get('cart_session_key')
        if sess_key:
            try:
                anon_cart = Cart.objects.get(session_key=sess_key)
            except Cart.DoesNotExist:
                anon_cart = None

            if anon_cart:
                for item in anon_cart.items.all():
                    CartItem.objects.update_or_create(
                        cart=cart,
                        product=item.product,
                        defaults={'quantity': item.quantity},
                    )
                anon_cart.delete()
            request.session.pop('cart_session_key', None)

        return cart

    sess_key = request.session.get('cart_session_key')
    if not sess_key:
        sess_key = uuid.uuid4().hex
        request.session['cart_session_key'] = sess_key

    cart, _ = Cart.objects.get_or_create(session_key=sess_key)
    return cart
