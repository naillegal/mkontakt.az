import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from django.core.mail import send_mail as django_send_mail
from django.conf import settings        
from .models import Cart, CartItem
from firebase_admin import messaging
from .models import UserDeviceToken

logger = logging.getLogger(__name__)   

_executor = ThreadPoolExecutor(max_workers=2)


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


def send_mail_async(subject, message, recipient_list, **kwargs):
    from_email = kwargs.pop("from_email", settings.EMAIL_HOST_USER)

    def _task():
        try:
            django_send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                **kwargs,
            )
            logger.info("Email sent to %s", recipient_list)
        except Exception:
            logger.exception("FAILED to send email to %s", recipient_list)

    _executor.submit(_task)


def send_push_notification(token, title, body, data=None):
    notification = messaging.Notification(
        title=title,
        body=body
    )

    android_config = messaging.AndroidConfig(
        priority="high"
    )
    apns_config = messaging.APNSConfig(
        headers={
            "apns-priority": "10"
        }
    )

    message = messaging.Message(
        notification=notification,
        data=data or {},
        android=android_config,
        apns=apns_config,
        token=token
    )

    response = messaging.send(message)
    return response 


def send_notification_to_user(user, title, body, data=None):
    for tok in user.device_tokens.values_list("token", flat=True):
        try:
            send_push_notification(tok, title, body, data)
        except Exception:
            logger.exception("Push failed for %s", tok)

def broadcast_notification(title, body, data=None):
    for tok in UserDeviceToken.objects.values_list("token", flat=True):
        try:
            send_push_notification(tok, title, body, data)
        except Exception:
            continue