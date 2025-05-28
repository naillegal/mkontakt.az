import random
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .utils import send_mail_async
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .utils import get_or_create_cart
import json
from django.utils import timezone
from decimal import Decimal
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import models as dj_models
from django.views.decorators.csrf import ensure_csrf_cookie
import uuid
from .models import (
    PartnerSlider, AdvertisementSlide,
    Brand, Category, Product, ProductType, CustomerReview, Blog, ContactMessage, ContactInfo, User, Wish,
    CartItem, DiscountCode, DiscountCodeUse, Order, OrderItem, PasswordResetOTP, Cart
)
from .serializers import (
    PartnerSliderSerializer, AdvertisementSlideSerializer,
    BrandSerializer, CategorySerializer, ProductTypeSerializer, ProductSerializer,
    CustomerReviewSerializer, BlogSerializer, UserSerializer,
    UserRegisterSerializer, UserLoginSerializer, UserUpdateSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, VerifyOtpSerializer, UpdatePasswordSerializer, MobileCartSerializer,
    DiscountCodeSerializer, WishItemSerializer, OrderSerializer
)
from django.contrib import messages


def about_us(request):
    return render(request, 'about-us.html')


def rules(request):
    return render(request, 'rules.html')


def forget_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(
                request, "Bu e-mail ilə istifadəçi qeydiyyatda deyil.")
            return redirect("MContact:forget-password")

        code = f"{random.randint(0, 9999):04d}"
        PasswordResetOTP.objects.filter(user=user).delete()
        PasswordResetOTP.objects.create(user=user, code=code)

        send_mail_async(
            subject="MContact – Şifrə yeniləmə üçün OTP kodu",
            message=f"Şifrə yeniləmə kodunuz: {code}. Kod 5 dəqiqə qüvvədədir.",
            recipient_list=[email],
            fail_silently=False,
        )

        request.session["reset_email"] = email
        messages.success(request, "OTP kodu e-poçtunuza göndərildi.")
        return redirect("MContact:otp")

    return render(request, "forget-password.html")


def otp(request):
    email = request.session.get("reset_email")
    if not email:
        return redirect("MContact:forget-password")

    if request.method == "POST":
        code = request.POST.get("otp_code", "").strip()
        try:
            pr = PasswordResetOTP.objects.get(user__email=email, code=code)
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, "OTP kodu yanlışdır.")
            return redirect("MContact:otp")

        if pr.is_expired():
            pr.delete()
            messages.error(request, "OTP kodunun vaxtı bitib.")
            return redirect("MContact:forget-password")

        request.session["otp_verified"] = True
        pr.delete()
        return redirect("MContact:new-password")

    return render(request, "otp.html")


def new_password(request):
    if not request.session.get("otp_verified"):
        return redirect("MContact:forget-password")

    email = request.session.get("reset_email")
    user = get_object_or_404(User, email=email)

    if request.method == "POST":
        pw1 = request.POST.get("password", "").strip()
        pw2 = request.POST.get("confirm_password", "").strip()

        if pw1 != pw2:
            messages.error(request, "Şifrələr uyğun gəlmir.")
            return redirect("MContact:new-password")

        user.password = pw1
        user.save()

        for k in ("reset_email", "otp_verified"):
            if k in request.session:
                del request.session[k]

        messages.success(
            request, "Parolunuz yeniləndi. Zəhmət olmasa yenidən daxil olun.")
        return redirect("MContact:login")

    return render(request, "new-password.html")


def products(request):
    all_brands = Brand.objects.all().order_by('name')
    all_categories = Category.objects.all().order_by('name')

    brand_ids = request.GET.getlist('brand')
    category_ids = request.GET.getlist('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    ordering = request.GET.get('ordering')

    product_qs = Product.objects.all()

    if brand_ids:
        product_qs = product_qs.filter(brand__id__in=brand_ids)

    if category_ids:
        product_qs = product_qs.filter(
            categories__id__in=category_ids).distinct()

    if min_price:
        product_qs = product_qs.filter(price__gte=min_price)
    if max_price:
        product_qs = product_qs.filter(price__lte=max_price)

    if ordering == 'price_asc':
        product_qs = product_qs.order_by('price')
    elif ordering == 'price_desc':
        product_qs = product_qs.order_by('-price')

    paginator = Paginator(product_qs, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    session_user_id = request.session.get("user_id")
    if session_user_id:
        wish_ids = set(
            Wish.objects.filter(user_id=session_user_id)
                        .values_list("product_id", flat=True)
        )
    else:
        wish_ids = set()

    context = {
        'page_obj': page_obj,
        'brands': all_brands,
        'categories': all_categories,
        "wish_ids": wish_ids,
    }
    return render(request, 'products.html', context)


def product_detail(request, slug):
    product_item = get_object_or_404(Product, slug=slug)
    other_products = Product.objects.exclude(
        id=product_item.id).order_by('-created_at')[:3]

    session_user_id = request.session.get("user_id")
    if session_user_id:
        wish_ids = set(
            Wish.objects.filter(user_id=session_user_id)
                        .values_list("product_id", flat=True)
        )
    else:
        wish_ids = set()

    context = {
        'product': product_item,
        'other_products': other_products,
        "wish_ids": wish_ids,
    }
    return render(request, 'products-detail.html', context)


class BrandListCreateAPIView(generics.ListCreateAPIView):
    queryset = Brand.objects.all().order_by('name')
    serializer_class = BrandSerializer


class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    parser_classes = (MultiPartParser, FormParser)


class ProductTypeListCreateAPIView(generics.ListCreateAPIView):
    queryset = ProductType.objects.all().order_by('id')
    serializer_class = ProductTypeSerializer


class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class ProductRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'pk'

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


def index(request):
    partners = PartnerSlider.objects.all().order_by('created_at')
    advertisement_slides = AdvertisementSlide.objects.all().order_by('created_at')
    recent_products = Product.objects.all().order_by('-created_at')[:6]
    recent_categories = Category.objects.all().order_by('-created_at')[:3]
    random_products = Product.objects.order_by('?')[:6]
    customer_reviews = CustomerReview.objects.all()

    session_user_id = request.session.get("user_id")
    if session_user_id:
        wish_ids = set(
            Wish.objects
                .filter(user_id=session_user_id)
                .values_list("product_id", flat=True)
        )
    else:
        wish_ids = set()

    context = {
        'partners': partners,
        'advertisement_slides': advertisement_slides,
        'slider_title': '',
        'recent_products': recent_products,
        'recent_categories': recent_categories,
        'random_products': random_products,
        'customer_reviews': customer_reviews,
        'wish_ids': wish_ids,
    }
    return render(request, 'index.html', context)


class PartnerSliderListCreateAPIView(generics.ListCreateAPIView):
    queryset = PartnerSlider.objects.all().order_by('created_at')
    serializer_class = PartnerSliderSerializer
    parser_classes = (MultiPartParser, FormParser)


class AdvertisementSlideListAPIView(generics.ListAPIView):
    queryset = AdvertisementSlide.objects.all().order_by('created_at')
    serializer_class = AdvertisementSlideSerializer


class CustomerReviewListCreateAPIView(generics.ListCreateAPIView):
    queryset = CustomerReview.objects.all().order_by('-created_at')
    serializer_class = CustomerReviewSerializer


def blog_list(request):
    blog_qs = Blog.objects.all()
    paginator = Paginator(blog_qs, 12)
    page = request.GET.get('page')
    try:
        blogs = paginator.page(page)
    except PageNotAnInteger:
        blogs = paginator.page(1)
    except EmptyPage:
        blogs = paginator.page(paginator.num_pages)
    context = {
        'blogs': blogs,
    }
    return render(request, 'blog.html', context)


def blog_detail(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    context = {
        'blog': blog,
    }
    return render(request, 'blog-detail.html', context)


class BlogListCreateAPIView(generics.ListCreateAPIView):
    queryset = Blog.objects.all().order_by('-created_at')
    serializer_class = BlogSerializer


class BlogRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    lookup_field = 'slug'


def contact(request):
    contact_info = ContactInfo.objects.first()
    return render(request, 'contact.html', {'contact_info': contact_info})


def contact_submit(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        company = request.POST.get("company", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        message_text = request.POST.get("message", "").strip()

        errors = {}
        if not name:
            errors["name"] = "Ad daxil etmək mütləqdir."
        if not phone:
            errors["phone"] = "Telefon daxil etmək mütləqdir."

        if errors:
            for field, error in errors.items():
                messages.error(request, error)
            return redirect('MContact:contact')

        ContactMessage.objects.create(
            name=name,
            company=company,
            email=email,
            phone=phone,
            message=message_text,
        )
        messages.success(request, "Mesajınız uğurla göndərildi!")
        return redirect('MContact:contact')

    return redirect('MContact:contact')


class UserRegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer


class UserLoginAPIView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Yanlış email və ya parol."}, status=status.HTTP_400_BAD_REQUEST)

        if user.password != password:
            return Response({"detail": "Yanlış email və ya parol."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "detail": "Login uğurlu oldu.",
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


def register(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        birth_date = request.POST.get("birth_date", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        terms = request.POST.get("terms")
        image = request.FILES.get("image")

        errors = {}
        if not full_name:
            errors["full_name"] = "Ad soyad daxil etmək mütləqdir."
        if not email:
            errors["email"] = "E-poçt daxil etmək mütləqdir."
        if not phone:
            errors["phone"] = "Telefon nömrəsi daxil etmək mütləqdir."
        if not birth_date:
            errors["birth_date"] = "Doğum tarixi daxil etmək mütləqdir."
        if not password:
            errors["password"] = "Parol daxil etmək mütləqdir."
        if password != confirm_password:
            errors["confirm_password"] = "Parollar uyğunsuzdur."
        if not terms:
            errors["terms"] = "İstifadə qaydalarını qəbul etmək vacibdir."

        if errors:
            for error in errors.values():
                messages.error(request, error)
            return redirect('MContact:register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Bu email artıq istifadə olunur.")
            return redirect('MContact:register')

        user = User.objects.create(
            full_name=full_name,
            email=email,
            phone=phone,
            birth_date=birth_date,
            password=password,
            image=image,
        )

        request.session['user_id'] = user.id
        messages.success(
            request, "Qeydiyyat uğurla tamamlandı və sistemə daxil olundu!")
        return redirect('MContact:index')
    return render(request, 'register.html')

@ensure_csrf_cookie
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Yanlış email və ya parol.")
            return redirect('MContact:login')

        if user.password != password:
            messages.error(request, "Yanlış email və ya parol.")
            return redirect('MContact:login')

        request.session['user_id'] = user.id
        messages.success(request, "Login uğurlu oldu.")
        return redirect('MContact:index')

    return render(request, 'login.html')


def edit_profile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Əvvəlcə daxil olun.")
        return redirect('MContact:login')

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        birth_date = request.POST.get("birth_date", "").strip()
        image = request.FILES.get("image")

        if full_name:
            user.full_name = full_name
        if email:
            if User.objects.exclude(id=user.id).filter(email=email).exists():
                messages.error(request, "Bu email artıq istifadə olunur.")
                return redirect('MContact:edit_profile')
            user.email = email
        if phone:
            user.phone = phone
        if birth_date:
            user.birth_date = birth_date
        if image:
            user.image = image

        user.save()
        messages.success(request, "Profil məlumatlarınız uğurla yeniləndi!")
        return redirect('MContact:edit_profile')

    return render(request, 'edit-profile.html', {'user': user})


class UserProfileUpdateAPIView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    queryset = User.objects.all()
    http_method_names = ["post", "put", "patch"]

    def get_object(self):
        user_id = (
            self.request.data.get("id")
            or self.request.query_params.get("id")
        )
        if not user_id:
            raise ValidationError({"id": "İstifadəçi ID göndərilməlidir."})
        return get_object_or_404(User, pk=user_id)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


def change_password(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Əvvəlcə daxil olun.")
        return redirect("MContact:login")

    user = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        old_password = request.POST.get("old_password", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm = request.POST.get("confirm_password", "").strip()

        if new_password != confirm:
            messages.error(request, "Yeni parol və təkrarı eyni olmalıdır.")
            return redirect("MContact:change_password")

        if user.password != old_password:
            messages.error(request, "Köhnə parol yanlışdır.")
            return redirect("MContact:change_password")

        user.password = new_password
        user.save()
        messages.success(request, "Parolunuz uğurla yeniləndi!")
        return redirect("MContact:change_password")

    return render(request, "change-password.html")


class ChangePasswordAPIView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = get_object_or_404(User, pk=data["id"])
        if user.password != data["old_password"]:
            raise ValidationError({"old_password": "Köhnə parol yanlışdır."})

        user.password = data["new_password"]
        user.save()
        return Response({"detail": "Parol uğurla yeniləndi."},
                        status=status.HTTP_200_OK)


def toggle_wishlist(request, product_id):
    session_user_id = request.session.get("user_id")
    if not session_user_id:
        return redirect(f"/login/?next={request.path}")

    product = get_object_or_404(Product, pk=product_id)
    wish_qs = Wish.objects.filter(user_id=session_user_id, product=product)

    if wish_qs.exists():
        wish_qs.delete()
        in_wishlist = False
    else:
        Wish.objects.create(user_id=session_user_id, product=product)
        in_wishlist = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"in_wishlist": in_wishlist})
    return redirect(request.META.get("HTTP_REFERER", "/products/"))


def wishlist_view(request):
    session_user_id = request.session.get("user_id")
    if not session_user_id:
        return redirect(f"/login/?next=/wishlist/")

    wishes = (
        Wish.objects
            .filter(user_id=session_user_id)
            .select_related("product")
            .order_by("-created_at")
    )
    wish_ids = set(wishes.values_list("product_id", flat=True))
    return render(request, "wishlist.html", {
        "wishes": wishes,
        "wish_ids": wish_ids,
    })


@require_POST
def cart_add(request, product_id):
    data = json.loads(request.body or '{}')
    qty = int(data.get('quantity', 1))
    product = get_object_or_404(Product, pk=product_id)
    cart = get_or_create_cart(request)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': qty}
    )
    if not created:
        item.quantity += qty
        item.save()

    return JsonResponse({
        'ok': True,
        'count': cart.items.count(),
        'item_quantity': item.quantity
    })


def cart_view(request):
    cart = get_or_create_cart(request)
    paginator = Paginator(cart.items.select_related(
        "product"), 3)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {
        "cart": cart,
        "page_obj": page_obj,
        "discount_amount": cart.get_discount_code_amount(),
    }
    return render(request, "cart.html", context)


@require_POST
def cart_update(request):
    import json
    data = json.loads(request.body)
    action = data.get("action")
    item_id = data.get("item_id")
    ids = data.get("ids", [])

    cart = get_or_create_cart(request)

    if action == "delete_selected":
        cart.items.filter(id__in=ids).delete()
    elif action in ("inc", "dec"):
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.quantity = max(1, item.quantity + (1 if action == "inc" else -1))
        item.save()
    elif action == "delete_one":
        cart.items.filter(id=item_id).delete()

    return JsonResponse({"ok": True})


@require_POST
def apply_discount(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse(
            {"error": "Endirim kodunu istifadə etmək üçün əvvəlcə daxil olun."},
            status=400
        )

    cart = get_or_create_cart(request)

    code_txt = request.POST.get("code", "").strip().upper()

    try:
        code = DiscountCode.objects.get(code=code_txt, active=True)
        if code.expires_at and code.expires_at < timezone.now():
            raise DiscountCode.DoesNotExist
    except DiscountCode.DoesNotExist:
        return JsonResponse(
            {"error": "Kod tapılmadı və ya deaktivdir."},
            status=400
        )

    already_used = Order.objects.filter(
        user_id=user_id,
        discount_code__iexact=code_txt
    ).exists()

    if already_used:
        return JsonResponse(
            {"error": "Bu endirim kodundan artıq istifadə etmisiniz."},
            status=400
        )

    DiscountCodeUse.objects.update_or_create(
        cart=cart, defaults={"code": code})

    return JsonResponse(
        {
            "ok": True,
            "percent": code.percent,
            "amount": cart.get_discount_code_amount()
        }
    )


@require_POST
def order_create(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.error(request, "Səbət boşdur")
        return redirect("MContact:cart")

    full_name = request.POST["full_name"].strip()
    phone = request.POST["phone"].strip()
    address = request.POST["address"].strip()
    date = request.POST["delivery_date"]
    time = request.POST["delivery_time"]

    order = Order.objects.create(
        user_id=request.session.get("user_id"),
        full_name=full_name,
        phone=phone,
        address=address,
        delivery_date=date,
        delivery_time=time,
        discount_code=getattr(cart.discountcodeuse, "code", None).code if hasattr(
            cart, "discountcodeuse") else "",
        discount_amount=cart.get_discount_code_amount(),
        product_discount=cart.product_discount,
        subtotal=cart.raw_total,
        total=cart.grand_total,
    )
    for item in cart.items.select_related("product"):
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            unit_price=item.product.price,
        )
    cart.delete()
    messages.success(request, "Sifarişiniz qeydə alındı!")
    return redirect("MContact:index")


def order_view(request):
    cart = get_or_create_cart(request)
    session_user_id = request.session.get('user_id')
    current_user = None
    if session_user_id:
        current_user = get_object_or_404(User, pk=session_user_id)
    return render(request, 'order.html', {
        'cart': cart,
        'discount_amount': cart.get_discount_code_amount(),
        'current_user': current_user,
    })


def logout_view(request):
    request.session.flush()
    messages.success(request, "Çıxış etdiniz.")
    return redirect('MContact:index')


class LogoutAPIView(APIView):
    def post(self, request):
        request.session.flush()
        return Response({"detail": "Çıxış etdiniz."}, status=status.HTTP_200_OK)


class ForgotPasswordAPIView(APIView):
    serializer_class = ForgotPasswordSerializer

    @swagger_auto_schema(
        operation_summary="Şifrə sıfırlama üçün OTP göndər",
        operation_description="Verilmiş e‑mail ünvanına 4 rəqəmli OTP kodu göndərir.",
        request_body=ForgotPasswordSerializer,
        responses={
            200: openapi.Response(
                description="OK",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Bad Request")
        },
    )
    def post(self, request):
        s = self.serializer_class(data=request.data)
        s.is_valid(raise_exception=True)
        email = s.validated_data["email"].lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Bu e-mail mövcud deyil."}, status=400)

        PasswordResetOTP.objects.filter(user=user).delete()
        code = f"{random.randint(0,9999):04d}"
        PasswordResetOTP.objects.create(user=user, code=code)

        send_mail_async(
            subject="MContact – Şifrə yeniləmə üçün OTP kodu",
            message=f"Şifrə yeniləmə kodunuz: {code}. Kod 5 dəqiqə qüvvədədir.",
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"detail": "OTP kodu göndərildi."})


class VerifyOtpAPIView(APIView):
    serializer_class = VerifyOtpSerializer

    @swagger_auto_schema(
        operation_summary="OTP kodunu yoxla",
        operation_description="E‑mail və kodu qəbul edib yoxlayır.",
        request_body=VerifyOtpSerializer,
        responses={
            200: openapi.Response(
                description="OTP təsdiqləndi",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'detail': openapi.Schema(
                        type=openapi.TYPE_STRING)}
                )
            ),
            400: openapi.Response(description="Kod yanlışdır və ya vaxtı bitib")
        },
    )
    def post(self, request):
        s = self.serializer_class(data=request.data)
        s.is_valid(raise_exception=True)
        email = s.validated_data["email"].lower()
        code = s.validated_data["otp_code"]

        try:
            pr = PasswordResetOTP.objects.get(user__email=email, code=code)
        except PasswordResetOTP.DoesNotExist:
            return Response({"detail": "OTP kodu yanlışdır."}, status=400)

        if pr.is_expired():
            pr.delete()
            return Response({"detail": "OTP kodunun vaxtı bitib."}, status=400)

        pr.delete()
        return Response({"detail": "OTP təsdiqləndi."})


class UpdatePasswordAPIView(APIView):
    serializer_class = UpdatePasswordSerializer

    @swagger_auto_schema(
        operation_summary="Yeni parol təyin et",
        operation_description="E‑mail ünvanı üçün yeni parol təyin edir.",
        request_body=UpdatePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Parol yeniləndi",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'detail': openapi.Schema(
                        type=openapi.TYPE_STRING)}
                )
            ),
            400: openapi.Response(description="Xəta: istifadəçi tapılmadı")
        },
    )
    def post(self, request):
        s = self.serializer_class(data=request.data)
        s.is_valid(raise_exception=True)
        email = s.validated_data["email"].lower()
        new_pw = s.validated_data["new_password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "İstifadəçi tapılmadı."}, status=400)

        user.password = new_pw
        user.save()
        return Response({"detail": "Parol yeniləndi."})


class MobileCartView(APIView):
    parser_classes = [JSONParser]

    def _get_or_create_cart(self, *, user_id, session_key):
        cart = None
        if user_id:
            cart, _ = Cart.objects.get_or_create(user_id=user_id)
            if session_key:
                try:
                    anon = Cart.objects.get(
                        session_key=session_key, user__isnull=True)
                    for it in anon.items.all():
                        CartItem.objects.update_or_create(
                            cart=cart,
                            product=it.product,
                            defaults={"quantity": dj_models.F(
                                "quantity") + it.quantity},
                        )
                    anon.delete()
                except Cart.DoesNotExist:
                    pass
            return cart, session_key
        if not session_key:
            session_key = uuid.uuid4().hex
        cart, _ = Cart.objects.get_or_create(
            session_key=session_key, user=None)
        return cart, session_key

    @swagger_auto_schema(
        operation_summary="Səbətə məhsul əlavə et",
        operation_description="product_id göndərərək istifadəçinin səbətinə məhsul əlavə edir və ya mövcuddursa miqdarı artırır.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='(Optional) Login olmuş istifadəçi ID-si'
                ),
                'session_key': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='(Optional) Qonaq istifadəçi üçün session açarı'
                ),
                'product_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='(Required) Əlavə ediləcək məhsulun ID-si'
                ),
                'quantity': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='(Optional) Əlavə ediləcək miqdar, default 1',
                    default=1
                ),
            },
            required=['product_id'],
        ),
        responses={
            200: openapi.Response(
                description="Uğurlu cavab, səbət məlumatı",
                schema=MobileCartSerializer()
            ),
            400: openapi.Response(description="product_id yoxdursa və ya başqa xəta")
        }
    )
    def post(self, request):
        data = request.data
        user_id = data.get("user_id")
        session_key = data.get("session_key")
        product_id = data.get("product_id")
        qty = int(data.get("quantity", 1))

        if not product_id:
            return Response({"detail": "product_id göndərilməlidir."}, status=400)

        product = get_object_or_404(Product, pk=product_id)
        cart, session_key = self._get_or_create_cart(
            user_id=user_id, session_key=session_key)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": qty},
        )
        if not created:
            item.quantity += qty
            item.save()

        ser = MobileCartSerializer(cart, context={"request": request})
        return Response({"session_key": session_key, "cart": ser.data}, status=200)

    @swagger_auto_schema(
        operation_summary="Səbəti əldə et",
        manual_parameters=[
            openapi.Parameter(
                'user_id', openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description='Login olmuş istifadəçi ID-si, varsa'
            ),
            openapi.Parameter(
                'session_key', openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Qonaq istifadəçi üçün session açarı'
            ),
        ],
        responses={200: openapi.Response(
            description="Səbət məlumatı",
            schema=MobileCartSerializer()
        )}
    )
    def get(self, request):
        user_id = request.query_params.get("user_id")
        session_key = request.query_params.get("session_key")

        cart, session_key = self._get_or_create_cart(
            user_id=user_id, session_key=session_key)
        ser = MobileCartSerializer(cart, context={"request": request})
        return Response({"session_key": session_key, "cart": ser.data}, status=200)

    @swagger_auto_schema(
        operation_summary="Səbətdən məhsul sil",
        operation_description="`product_id` göndərərək həmin məhsulu cart-dan silir və yenilənmiş cart məlumatını qaytarır.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='(Optional) Login olmuş istifadəçi ID-si'
                ),
                'session_key': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='(Optional) Qonaq istifadəçi üçün session açarı'
                ),
                'product_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='(Required) Səbətdən silinəcək məhsulun ID-si'
                ),
            },
            required=['product_id'],
        ),
        responses={
            200: openapi.Response(
                description="Uğurlu cavab, yenilənmiş cart məlumatı",
                schema=MobileCartSerializer()
            ),
            400: openapi.Response(description="product_id göndərilməyibsə və ya başqa xəta")
        }
    )
    def delete(self, request):
        data = request.data
        user_id = data.get("user_id")
        session_key = data.get("session_key")
        product_id = data.get("product_id")

        if not product_id:
            return Response({"detail": "product_id göndərilməlidir."}, status=400)

        cart, session_key = self._get_or_create_cart(
            user_id=user_id, session_key=session_key
        )

        CartItem.objects.filter(cart=cart, product_id=product_id).delete()

        ser = MobileCartSerializer(cart, context={"request": request})
        return Response(
            {"session_key": session_key, "cart": ser.data},
            status=200
        )


class DiscountCodeListCreateAPIView(generics.ListCreateAPIView):
    queryset = DiscountCode.objects.all().order_by('-id')
    serializer_class = DiscountCodeSerializer

    @swagger_auto_schema(
        operation_summary="Yenis DiscountCode yarat",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['code', 'percent'],
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, example='TEST10'),
                'percent': openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
                'active': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                'expires_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', example='2025-05-18T10:29:09.240Z'),
            },
            example={
                "code": "TEST10",
                "percent": 10,
                "active": True,
                "expires_at": "2025-05-18T10:29:09.240Z"
            }
        ),
        responses={201: openapi.Response(
            'Yaradıldı', DiscountCodeSerializer())}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CalculateDiscountPercentageAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="Discount dəyərinin hesablanması",
        operation_description=(
            "Bu endpoint `code` və `value` qəbul edir, `percent` faizini, verilən value-ya tətbiq edib "
            "yenilənmiş dəyəri qaytarır"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["code", "value"],
            properties={
                "code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Discount code (məsələn: TEST10)",
                    example="TEST10"
                ),
                "value": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Əsas dəyər (məsələn: 5)",
                    example=5
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Uğurlu, yeni dəyər",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING),
                        "new_value": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {
                        "detail": "Discount applied successfully.",
                        "new_value": "4.50"
                    }
                }
            ),
            400: openapi.Response(description="Yanlış sorğu", examples={
                "application/json": {"detail": "Both code and value are required."}
            }),
            404: openapi.Response(description="Kod tapılmadı", examples={
                "application/json": {"detail": "Discount code not found."}
            }),
        }
    )
    def post(self, request):
        code = request.data.get("code")
        value = request.data.get("value")
        if not code or value is None:
            return Response(
                {"detail": "Both code and value are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            provided = Decimal(str(value))
        except Exception:
            return Response(
                {"detail": "Value must be a number."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            discount = DiscountCode.objects.get(code=code)
        except DiscountCode.DoesNotExist:
            return Response(
                {"detail": "Discount code not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        if not discount.active:
            return Response(
                {"detail": "Discount code is not active."},
                status=status.HTTP_400_BAD_REQUEST
            )
        frac = Decimal(discount.percent) / Decimal('100')
        new_value = provided - (provided * frac)
        if new_value < 0:
            new_value = Decimal('0')
        return Response({
            "detail": "Discount applied successfully.",
            "new_value": str(new_value.quantize(Decimal('0.01')))
        }, status=status.HTTP_200_OK)


class WishlistAPIView(APIView):
    parser_classes = [JSONParser]

    @swagger_auto_schema(
        operation_summary="Wishlist-i əldə et",
        manual_parameters=[
            openapi.Parameter(
                'user_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                description='(Required) İstifadəçi ID-si'
            )
        ],
        responses={200: openapi.Response(
            description="Wishlist məlumatı",
            schema=WishItemSerializer(many=True)
        ),
            400: openapi.Response(description="user_id göndərilməlidir")}
    )
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {"detail": "user_id göndərilməlidir."},
                status=status.HTTP_400_BAD_REQUEST
            )
        get_object_or_404(User, pk=user_id)
        qs = Wish.objects.filter(user_id=user_id).select_related('product')
        ser = WishItemSerializer(qs, many=True, context={'request': request})
        return Response(ser.data, status=200)

    @swagger_auto_schema(
        operation_summary="Wishlist-ə məhsul əlavə et",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id', 'product_id'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=42),
            }
        ),
        responses={
            201: openapi.Response(
                description="Yeni wish yaradıldı",
                schema=WishItemSerializer()
            ),
            400: openapi.Response(description="user_id və product_id mütləqdir"),
            404: openapi.Response(description="User və ya Product tapılmadı")
        }
    )
    def post(self, request):
        user_id = request.data.get('user_id')
        product_id = request.data.get('product_id')
        if not user_id or not product_id:
            return Response(
                {"detail": "user_id və product_id mütləqdir."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = get_object_or_404(User, pk=user_id)
        product = get_object_or_404(Product, pk=product_id)

        wish, created = Wish.objects.get_or_create(user=user, product=product)
        if not created:
            return Response(
                {"detail": "Artıq wishlist-də mövcuddur."},
                status=status.HTTP_200_OK
            )

        ser = WishItemSerializer(wish, context={'request': request})
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Wishlist-dən məhsul sil",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id', 'product_id'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=42),
            }
        ),
        responses={
            200: openapi.Response(
                description="Yenilənmiş wishlist",
                schema=WishItemSerializer(many=True)
            ),
            400: openapi.Response(description="user_id və product_id mütləqdir"),
            404: openapi.Response(description="User və ya Product tapılmadı")
        }
    )
    def delete(self, request):
        user_id = request.data.get('user_id')
        product_id = request.data.get('product_id')
        if not user_id or not product_id:
            return Response(
                {"detail": "user_id və product_id mütləqdir."},
                status=status.HTTP_400_BAD_REQUEST
            )
        get_object_or_404(User, pk=user_id)
        get_object_or_404(Product, pk=product_id)

        Wish.objects.filter(user_id=user_id, product_id=product_id).delete()

        qs = Wish.objects.filter(user_id=user_id).select_related('product')
        ser = WishItemSerializer(qs, many=True, context={'request': request})
        return Response(ser.data, status=200)


class MobileOrderView(APIView):
    parser_classes = [JSONParser]

    def _get_cart_by_key(self, user_id, session_key):
        view = MobileCartView()
        return view._get_or_create_cart(user_id=user_id, session_key=session_key)

    @swagger_auto_schema(
        operation_summary="Mobil sifariş yarat",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "full_name", "phone", "address",
                "delivery_date", "delivery_time"
            ],
            properties={
                "user_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="(Optional) Login user"),
                "session_key": openapi.Schema(type=openapi.TYPE_STRING, description="(Optional) Guest session"),
                "full_name": openapi.Schema(type=openapi.TYPE_STRING, example="Elvin Məmmədov"),
                "phone": openapi.Schema(type=openapi.TYPE_STRING, example="+994551234567"),
                "address": openapi.Schema(type=openapi.TYPE_STRING, example="Bakı, Nərimanov r., …"),
                "delivery_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-05-20"),
                "delivery_time": openapi.Schema(type=openapi.TYPE_STRING, format="time", example="14:30"),
            }
        ),
        responses={
            201: openapi.Response("Yaradıldı", OrderSerializer()),
            400: openapi.Response(description="Cart boşdur və ya payload-da field çatmır")
        }
    )
    def post(self, request):
        data = request.data
        user_id = data.get("user_id")
        session_key = data.get("session_key")

        cart, session_key = self._get_cart_by_key(
            user_id=user_id, session_key=session_key)

        if not cart.items.exists():
            return Response({"detail": "Səbət boşdur."}, status=400)

        required = ("full_name", "phone", "address",
                    "delivery_date", "delivery_time")
        if not all(data.get(f) for f in required):
            return Response({"detail": "Bütün tələb olunan sahələr göndərilməlidir."}, status=400)

        order = Order.objects.create(
            user_id=user_id,
            full_name=data["full_name"],
            phone=data["phone"],
            address=data["address"],
            delivery_date=data["delivery_date"],
            delivery_time=data["delivery_time"],
            discount_code=getattr(cart.discountcodeuse, "code", None).code if hasattr(
                cart, "discountcodeuse") else "",
            discount_amount=cart.get_discount_code_amount(),
            product_discount=cart.product_discount,
            subtotal=cart.raw_total,
            total=cart.grand_total,
        )

        for item in cart.items.select_related("product"):
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.product.price
            )

        cart.delete()

        ser = OrderSerializer(order)
        return Response(ser.data, status=201)

    class _FivePerPage(PageNumberPagination):
        page_size = 5

    @swagger_auto_schema(
        operation_summary="Sifarişləri paginate et(5)",
        manual_parameters=[
            openapi.Parameter(
                "user_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                description="(Optional) Yalnız bu istifadəçinin sifarişləri"
            ),
            openapi.Parameter(
                "page", openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                description="Səhifə nömrəsi (default 1)"
            ),
        ],
        responses={200: openapi.Response("OK", OrderSerializer(many=True))}
    )
    def get(self, request):
        user_id = request.query_params.get("user_id")
        qs = Order.objects.all().order_by("-created_at")
        if user_id:
            qs = qs.filter(user_id=user_id)

        paginator = self._FivePerPage()
        page = paginator.paginate_queryset(qs, request)
        ser = OrderSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'perpage'
    max_page_size = 100


class CategoryProductsAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        get_object_or_404(Category, pk=category_id)
        return (
            Product.objects
                   .filter(categories__id=category_id)
                   .distinct()
                   .order_by('-created_at')
        )
