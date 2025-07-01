import random
import datetime
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from django.conf import settings
from .utils import send_mail_async
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count
from .utils import get_or_create_cart
import json
from django.utils import timezone
from decimal import Decimal
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import models as dj_models
from django.db.models import Case, When, Value, IntegerField
from django.views.decorators.csrf import ensure_csrf_cookie
import uuid
from .models import (
    PartnerSlider, AdvertisementSlide,
    Brand, Category, Product, ProductType, CustomerReview, Blog, ContactMessage, ContactInfo, User, Wish,
    CartItem, DiscountCode, DiscountCodeUse, Order, OrderItem, PasswordResetOTP, Cart, UserDeviceToken, HomePageBanner,
    ProductAttribute, ProductVariant, ProductAttributeValue, SubCategory
)
from .serializers import (
    PartnerSliderSerializer, AdvertisementSlideSerializer,
    BrandSerializer, CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    CustomerReviewSerializer, BlogSerializer, UserSerializer,
    UserRegisterSerializer, UserLoginSerializer, UserUpdateSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, VerifyOtpSerializer, UpdatePasswordSerializer, MobileCartSerializer,
    DiscountCodeSerializer, WishItemSerializer, OrderSerializer, DeviceTokenSerializer
)
from django.contrib import messages


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'perpage'
    max_page_size = 100


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


@ensure_csrf_cookie
def products(request):
    all_brands = Brand.objects.all().order_by("name")
    all_categories = Category.objects.prefetch_related(
        'subcategories').all().order_by("name")
    all_attributes = (ProductAttribute.objects
                      .prefetch_related("values")
                      .order_by("name"))

    brand_ids = [int(x) for x in request.GET.getlist("brand")]
    category_ids = [int(x) for x in request.GET.getlist("category")]
    subcategory_ids = [int(x) for x in request.GET.getlist("subcategory")]
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    ordering = request.GET.get("ordering")
    q = request.GET.get("q", "").strip()

    attr_filters = {}
    for key, vals in request.GET.lists():
        if key.startswith("attr_"):
            try:
                attr_id = int(key.split("_", 1)[1])
                attr_filters[attr_id] = [int(v) for v in vals]
            except ValueError:
                continue

    qs = Product.objects.all()

    if q:
        qs = qs.filter(
            Q(code__iexact=q) |
            Q(title__icontains=q)
        )

    if brand_ids:
        qs = qs.filter(brand_id__in=brand_ids)

    if subcategory_ids:
        qs = qs.filter(subcategories__id__in=subcategory_ids).distinct()

    if min_price:
        qs = qs.filter(price__gte=min_price)
    if max_price:
        qs = qs.filter(price__lte=max_price)

    for value_ids in attr_filters.values():
        qs = qs.filter(variants__attribute_values__id__in=value_ids)

    qs = qs.distinct().annotate(
        _prio=Case(
            When(priority__isnull=False, then="priority"),
            default=Value(999999), output_field=IntegerField()
        )
    )

    if ordering == "price_asc":
        qs = qs.order_by("price")
    elif ordering == "price_desc":
        qs = qs.order_by("-price")
    else:
        qs = qs.order_by("_prio", "-created_at")

    paginator = Paginator(qs, 8)
    page_obj = paginator.get_page(request.GET.get("page"))

    session_user_id = request.session.get("user_id")
    wish_ids = (set(Wish.objects
                    .filter(user_id=session_user_id)
                    .values_list("product_id", flat=True))
                if session_user_id else set())

    return render(request, "products.html", {
        "page_obj": page_obj,
        "brands": all_brands,
        "categories": all_categories,
        "attributes": all_attributes,
        "wish_ids": wish_ids,
        "selected_brands":    brand_ids,
        "categories": all_categories,
        "selected_categories":  category_ids,
        "selected_subcategories": subcategory_ids,
        "selected_attr_vals": sum(attr_filters.values(), []),
    })


@ensure_csrf_cookie
def product_detail(request, slug):
    product_item = get_object_or_404(Product, slug=slug)

    prio = list(Product.objects
                .exclude(id=product_item.id)
                .filter(priority__isnull=False)
                .order_by('priority'))
    others = list(Product.objects
                  .exclude(id=product_item.id)
                  .filter(priority__isnull=True)
                  .order_by('?'))
    other_products = (prio + others)[:3]

    session_user_id = request.session.get("user_id")
    wish_ids = set(Wish.objects.filter(user_id=session_user_id)
                   .values_list("product_id", flat=True)) if session_user_id else set()

    attributes = ProductAttribute.objects.filter(
        values__product_variants__product=product_item
    ).distinct().prefetch_related(
        'values'
    )

    return render(request, 'products-detail.html', {
        'product': product_item,
        'other_products': other_products,
        'wish_ids': wish_ids,
        'attributes': attributes,
    })


class BrandListCreateAPIView(generics.ListCreateAPIView):
    queryset = Brand.objects.all().order_by('name')
    serializer_class = BrandSerializer


class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    parser_classes = (MultiPartParser, FormParser)


# class ProductTypeListCreateAPIView(generics.ListCreateAPIView):
#     queryset = ProductType.objects.all().order_by('id')
#     serializer_class = ProductTypeSerializer


class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductListSerializer
    pagination_class = CustomPageNumberPagination

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class ProductRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    lookup_field = "pk"

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


def index(request):
    partners = PartnerSlider.objects.all().order_by('created_at')
    advertisement_slides = AdvertisementSlide.objects.all().order_by('created_at')

    prio = list(Product.objects.filter(priority__isnull=False)
                .order_by('priority')[:6])
    rest = list(Product.objects.filter(priority__isnull=True)
                .order_by('-created_at')[:6 - len(prio)])
    recent_products = prio + rest

    prio_all = list(Product.objects.filter(priority__isnull=False)
                    .order_by('priority'))
    others = list(Product.objects.filter(priority__isnull=True)
                  .order_by('?'))
    random_products = (prio_all + others)[:6]

    recent_categories = Category.objects.all().order_by('-created_at')[:3]
    customer_reviews = CustomerReview.objects.all()

    session_user_id = request.session.get("user_id")
    wish_ids = set(Wish.objects.filter(user_id=session_user_id)
                   .values_list("product_id", flat=True)) if session_user_id else set()

    banner = HomePageBanner.objects.order_by('-created_at').first()

    context = {
        'partners': partners,
        'advertisement_slides': advertisement_slides,
        'slider_title': '',
        'recent_products': recent_products,
        'recent_categories': recent_categories,
        'random_products': random_products,
        'customer_reviews': customer_reviews,
        'wish_ids': wish_ids,
        'banner': banner,
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


@method_decorator(ensure_csrf_cookie, name="dispatch")
class RegisterAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="Qeydiyyat üçün OTP kodu göndər",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "full_name", "email", "phone", "birth_date", "password"
            ],
            properties={
                "full_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Ad Soyad"
                ),
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="E-poçt ünvanı"
                ),
                "phone": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Telefon nömrəsi"
                ),
                "birth_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Doğum tarixi (YYYY-MM-DD)"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="password",
                    description="Parol"
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="OTP kodu göndərildi",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Validation Error")
        },
    )
    def post(self, request):
        data = request.data
        full_name = data.get("full_name", "").strip()
        email = data.get("email", "").strip().lower()
        phone = data.get("phone", "").strip()
        birth_date = data.get("birth_date", "").strip()
        password = data.get("password", "").strip()

        errors = {}
        if not full_name:
            errors["full_name"] = "Ad Soyad mütləqdir."
        if not email:
            errors["email"] = "E-poçt mütləqdir."
        if not phone:
            errors["phone"] = "Telefon mütləqdir."
        if not birth_date:
            errors["birth_date"] = "Doğum tarixi mütləqdir."
        if not password:
            errors["password"] = "Parol mütləqdir."
        if User.objects.filter(email=email).exists():
            errors["email"] = "Bu e-poçt artıq istifadə olunub."

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        code = f"{random.randint(0, 9999):04d}"
        request.session['reg_full_name'] = full_name
        request.session['reg_email'] = email
        request.session['reg_phone'] = phone
        request.session['reg_birth_date'] = birth_date
        request.session['reg_password'] = password
        request.session['reg_otp_expected'] = code
        request.session['reg_otp_sent'] = True

        send_mail_async(
            subject="MContact – Qeydiyyat OTP kodu",
            message=f"Sizin Qeydiyyat OTP kodunuz: {code}",
            recipient_list=[email],
            fail_silently=False
        )

        return Response({"detail": "OTP kod email-ə göndərildi."}, status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class RegisterOTPAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="Qeydiyyatı tamamlamaq üçün OTP kodunu yoxla",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "otp_code"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="E-poçt ünvanı"
                ),
                "otp_code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="4 rəqəmli OTP kodu"
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description="User yaradıldı",
                schema=UserSerializer()
            ),
            400: openapi.Response(description="Validation Error")
        },
    )
    def post(self, request):
        data = request.data
        email = data.get("email", "").strip().lower()
        otp_input = data.get("otp_code", "").strip()

        expected = request.session.get('reg_otp_expected')
        sess_email = request.session.get('reg_email')
        if not expected or email != sess_email:
            return Response(
                {"detail": "Bu emaildə qeydiyyat mərhələsi başlamayıb."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp_input != expected:
            return Response(
                {"otp_code": "Yanlış OTP kodu."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create(
            full_name=request.session.pop('reg_full_name'),
            email=request.session.pop('reg_email'),
            phone=request.session.pop('reg_phone'),
            birth_date=request.session.pop('reg_birth_date'),
            password=request.session.pop('reg_password'),
        )
        for k in ('reg_otp_expected', 'reg_otp_sent'):
            request.session.pop(k, None)

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


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


class UserRetrieveAPIView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'pk'


@ensure_csrf_cookie
def register(request):
    if request.method == "POST":
        if not request.session.get('otp_sent'):
            full_name = request.POST.get("full_name", "").strip()
            email = request.POST.get("email", "").strip().lower()
            phone = request.POST.get("phone", "").strip()
            birth_date = request.POST.get("birth_date", "").strip()
            password = request.POST.get("password", "").strip()
            confirm = request.POST.get("confirm_password", "").strip()
            terms = request.POST.get("terms")

            errors = {}
            if not full_name:
                errors["full_name"] = "Ad soyad mütləqdir."
            if not email:
                errors["email"] = "E-poçt mütləqdir."
            if not phone:
                errors["phone"] = "Telefon mütləqdir."
            if not birth_date:
                errors["birth_date"] = "Doğum tarixi mütləqdir."
            if not password:
                errors["password"] = "Parol mütləqdir."
            if password != confirm:
                errors["confirm_password"] = "Şifrələr uyğun deyil."
            if not terms:
                errors["terms"] = "Qaydaları qəbul etməlisiniz."
            if User.objects.filter(email=email).exists():
                errors["email_exists"] = "Bu e-poçt artıq qeydiyyatdan keçib."

            if errors:
                for e in errors.values():
                    messages.error(request, e)
                return redirect('MContact:register')

            code = f"{random.randint(0, 9999):04d}"
            request.session['register_full_name'] = full_name
            request.session['register_email'] = email
            request.session['register_phone'] = phone
            request.session['register_birth_date'] = birth_date
            request.session['register_password'] = password
            request.session['otp_code_expected'] = code
            request.session['otp_sent'] = True

            send_mail_async(
                subject="MContact – Qeydiyyat üçün OTP",
                message=f"Sizin Qeydiyyat OTP kodunuz: {code}",
                from_email=None,
                recipient_list=[email],
                fail_silently=False
            )

            messages.success(request, "E-poçtunuza 4 rəqəmli kod göndərildi.")
            return redirect('MContact:register-otp')

        otp_received = request.POST.get("otp_code", "").strip()
        expected = request.session.get('otp_code_expected')

        if otp_received != expected:
            messages.error(request, "OTP kodu yanlışdır.")
            return redirect('MContact:register-otp')

        user = User.objects.create(
            full_name=request.session.pop('register_full_name'),
            email=request.session.pop('register_email'),
            phone=request.session.pop('register_phone'),
            birth_date=request.session.pop('register_birth_date'),
            password=request.session.pop('register_password'),
        )
        for k in ('otp_code_expected', 'otp_sent'):
            request.session.pop(k, None)

        request.session['user_id'] = user.id
        messages.success(
            request, "Qeydiyyat uğurla tamamlandı və daxil oldunuz.")
        return redirect('MContact:index')

    return render(request, 'register.html')


@ensure_csrf_cookie
def register_otp(request):
    if not request.session.get('otp_sent') or not request.session.get('register_email'):
        return redirect('MContact:register')

    if request.method == "POST":
        otp_received = request.POST.get("otp_code", "").strip()
        expected = request.session.get('otp_code_expected')

        if otp_received != expected:
            messages.error(request, "OTP kodu yanlışdır.")
            return redirect('MContact:register-otp')

        user = User.objects.create(
            full_name=request.session.pop('register_full_name'),
            email=request.session.pop('register_email'),
            phone=request.session.pop('register_phone'),
            birth_date=request.session.pop('register_birth_date'),
            password=request.session.pop('register_password'),
        )
        for k in ('otp_code_expected', 'otp_sent'):
            request.session.pop(k, None)

        request.session['user_id'] = user.id
        messages.success(request, "Qeydiyyat tamamlandı və daxil oldunuz.")
        return redirect('MContact:index')

    return render(request, 'register-otp.html')


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
        return redirect(f"/giriş/?next={request.path}")

    try:
        user = User.objects.get(pk=session_user_id)
    except User.DoesNotExist:
        del request.session["user_id"]
        return redirect(f"/giriş/?next={request.path}")

    product = get_object_or_404(Product, pk=product_id)
    wish_qs = Wish.objects.filter(user=user, product=product)

    if wish_qs.exists():
        wish_qs.delete()
        in_wishlist = False
    else:
        Wish.objects.create(user=user, product=product)
        in_wishlist = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"in_wishlist": in_wishlist})
    return redirect(request.META.get("HTTP_REFERER", "/məhsullar/"))


def wishlist_view(request):
    session_user_id = request.session.get("user_id")
    if not session_user_id:
        return redirect(f"/giriş/?next=/istək-siyahısı/")

    try:
        user = User.objects.get(pk=session_user_id)
    except User.DoesNotExist:
        del request.session["user_id"]
        return redirect(f"/giriş/?next=/istək-siyahısı/")

    wishes = (
        Wish.objects
            .filter(user=user)
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
    data = json.loads(request.body.decode() or "{}")
    quantity = int(data.get("quantity", 1))
    attr_values = data.get("attr_values", {})
    selected_ids = [int(v) for v in attr_values.values()]

    product = get_object_or_404(Product, pk=product_id)

    variant = None
    if selected_ids:
        wanted = set(selected_ids)
        for v in (ProductVariant.objects
                  .filter(product=product, is_active=True)
                  .prefetch_related("attribute_values")):
            vals = set(v.attribute_values.values_list("id", flat=True))
            if vals == wanted:
                variant = v
                break
    if variant is None and selected_ids:
        variant = ProductVariant.objects.create(product=product)
        variant.attribute_values.set(selected_ids)

    cart = get_or_create_cart(request)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        variant=variant,
        defaults={"quantity": quantity},
    )
    if not created:
        item.quantity += quantity
        item.save()

    return JsonResponse({
        "ok": True,
        "count": cart.items.count(),
        "item_quantity": item.quantity
    })


def cart_view(request):
    cart = get_or_create_cart(request)
    cart.items.filter(product__is_active=False).delete()

    paginator = Paginator(
        cart.items.select_related("product", "variant").prefetch_related(
            "variant__attribute_values__attribute"
        ),
        3
    )
    page_obj = paginator.get_page(request.GET.get("page"))

    shipping_fee = Decimal('0.00') if cart.grand_total >= Decimal(
        '200.00') else Decimal('10.00')
    final_total = cart.grand_total + shipping_fee

    context = {
        "cart": cart,
        "page_obj": page_obj,
        "discount_amount": cart.get_discount_code_amount(),
        "shipping_fee": shipping_fee,
        "final_total": final_total,
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
    cart.items.filter(product__is_active=False).delete()

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

    full_name = request.POST.get("full_name", "").strip()
    phone = request.POST.get("phone", "").strip()
    address = request.POST.get("address", "").strip()
    date_str = request.POST.get("delivery_date", "").strip()
    time_str = request.POST.get("delivery_time", "").strip()

    try:
        dt_naive = datetime.datetime.strptime(
            f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
        )
    except ValueError:
        messages.error(request, "Tarix və ya vaxt formatı yanlışdır.")
        return redirect("MContact:order")

    tz = timezone.get_current_timezone()
    dt_aware = timezone.make_aware(dt_naive, tz)

    now = timezone.now()
    if dt_aware < now:
        messages.error(
            request,
            "Çatdırılma tarixi və vaxtı keçmiş ola bilməz."
        )
        return redirect("MContact:order")

    shipping_fee = Decimal('0.00') if cart.grand_total >= Decimal(
        '200.00') else Decimal('10.00')
    order_total = cart.grand_total + shipping_fee

    order = Order.objects.create(
        user_id=request.session.get("user_id"),
        full_name=full_name,
        phone=phone,
        address=address,
        delivery_date=date_str,
        delivery_time=time_str,
        discount_code=getattr(cart, "discountcodeuse",
                              None) and cart.discountcodeuse.code or "",
        discount_amount=cart.get_discount_code_amount(),
        product_discount=cart.product_discount,
        category_discount=cart.category_discount,
        subtotal=cart.raw_total,
        total=order_total,
    )
    for item in cart.items.select_related("product", "variant"):
        OrderItem.objects.create(
            order=order,
            product=item.product,
            variant=item.variant,
            quantity=item.quantity,
            unit_price=item.product.price,
        )
    cart.delete()

    send_mail_async(
        subject="MContact – Yeni sifariş var",
        message=(
            f"Yeni sifariş #{order.pk} alındı.\n\n"
            "Sifariş detalları üçün admin panelə daxil olun."
        ),
        recipient_list=[settings.DEFAULT_FROM_EMAIL],
        fail_silently=False
    )

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
        code = f"{random.randint(0, 9999):04d}"
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

    @swagger_auto_schema(
        operation_summary="Mobil sifariş yarat",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "full_name", "phone", "address",
                "delivery_date", "delivery_time",
                "subtotal", "total", "items"
            ],
            properties={
                "user_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="(Optional) Login olmuş istifadəçi ID-si"
                ),
                "session_key": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="(Optional) Qonaq istifadəçi üçün session açarı"
                ),
                "full_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Müştərinin tam adı",
                    example="Elvin Məmmədov"
                ),
                "phone": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Müştərinin telefon nömrəsi",
                    example="+994551234567"
                ),
                "address": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Çatdırılma ünvanı",
                    example="Bakı, Nərimanov"
                ),
                "delivery_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Çatdırılma tarixi (YYYY-MM-DD)",
                    example="2025-06-10"
                ),
                "delivery_time": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="time",
                    description="Çatdırılma vaxtı (HH:MM)",
                    example="14:30"
                ),
                "discount_code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Endirim kodu (mövcud ola bilər və ya boş)",
                    example="TEST10"
                ),
                "discount_amount": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Endirim məbləği (decimal formatda)",
                    example="5.00"
                ),
                "product_discount": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Məhsul endirimi (decimal formatda)",
                    example="10.00"
                ),
                "subtotal": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Əsas məbləğ (decimal formatda)",
                    example="100.00"
                ),
                "total": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Ümumi məbləğ (decimal formatda)",
                    example="85.00"
                ),
                "items": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="Sifarişə daxil olan məhsulların siyahısı",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=["product_id", "quantity", "unit_price"],
                        properties={
                            "product_id": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="Məhsulun ID-si",
                                example=42
                            ),
                            "quantity": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="Miqdar",
                                example=2
                            ),
                            "unit_price": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Vahid qiymət (decimal formatda)",
                                example="15.50"
                            ),
                        }
                    )
                ),
            }
        ),
        responses={
            201: openapi.Response(
                description="Sifariş uğurla yaradıldı",
                schema=OrderSerializer()
            ),
            400: openapi.Response(description="Bad Request"),
            404: openapi.Response(description="Product tapılmadı")
        }
    )
    def post(self, request, *args, **kwargs):
        data = request.data

        user_id = data.get("user_id", None)
        session_key = data.get("session_key", None)

        full_name = data.get("full_name", "").strip()
        phone = data.get("phone", "").strip()
        address = data.get("address", "").strip()
        delivery_date = data.get("delivery_date", "").strip()
        delivery_time = data.get("delivery_time", "").strip()
        subtotal = data.get("subtotal", None)
        total = data.get("total", None)

        missing_fields = []
        if not full_name:
            missing_fields.append("full_name")
        if not phone:
            missing_fields.append("phone")
        if not address:
            missing_fields.append("address")
        if not delivery_date:
            missing_fields.append("delivery_date")
        if not delivery_time:
            missing_fields.append("delivery_time")
        if subtotal is None:
            missing_fields.append("subtotal")
        if total is None:
            missing_fields.append("total")

        if missing_fields:
            return Response(
                {"detail": f"Tələb olunan sahələr çatışmır: {', '.join(missing_fields)}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        discount_code = data.get("discount_code", "").strip()
        discount_amount_str = data.get("discount_amount", None)
        product_discount_str = data.get("product_discount", None)

        try:
            discount_amount = (
                Decimal(discount_amount_str) if discount_amount_str is not None else Decimal(
                    "0.00")
            )
        except Exception:
            return Response(
                {"detail": "discount_amount sahəsi doğru formatda deyil. Məsələn: \"5.00\"."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product_discount = (
                Decimal(product_discount_str) if product_discount_str is not None else Decimal(
                    "0.00")
            )
        except Exception:
            return Response(
                {"detail": "product_discount sahəsi doğru formatda deyil. Məsələn: \"10.00\"."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            subtotal_dec = Decimal(str(subtotal))
        except Exception:
            return Response(
                {"detail": "subtotal sahəsi doğru formatda deyil. Məsələn: \"100.00\"."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            total_dec = Decimal(str(total))
        except Exception:
            return Response(
                {"detail": "total sahəsi doğru formatda deyil. Məsələn: \"85.00\"."},
                status=status.HTTP_400_BAD_REQUEST
            )

        items = data.get("items", None)
        if not items or not isinstance(items, list):
            return Response(
                {"detail": "items siyahısı göndərilməlidir və ən azı bir məhsul olmalıdır."},
                status=status.HTTP_400_BAD_REQUEST
            )

        parsed_items = []
        for idx, itm in enumerate(items, start=1):
            pid = itm.get("product_id", None)
            qty = itm.get("quantity", None)
            unit_price = itm.get("unit_price", None)

            missing = []
            if pid is None:
                missing.append("product_id")
            if qty is None:
                missing.append("quantity")
            if unit_price is None:
                missing.append("unit_price")

            if missing:
                return Response(
                    {"detail": f"items[{idx}] içində çatışmayan sahələr: {', '.join(missing)}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                product_obj = Product.objects.get(pk=pid)
            except Product.DoesNotExist:
                return Response(
                    {"detail": f"items[{idx}] içində product_id='{pid}' tapılmadı."},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                qty_int = int(qty)
                if qty_int < 1:
                    raise ValueError()
            except Exception:
                return Response(
                    {"detail": f"items[{idx}] içində quantity düzgün deyil. Tam ədəd olmalıdır."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                unit_price_dec = Decimal(str(unit_price))
            except Exception:
                return Response(
                    {"detail": f"items[{idx}] içində unit_price düzgün formatda deyil. Məsələn: \"15.50\"."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            parsed_items.append({
                "product": product_obj,
                "quantity": qty_int,
                "unit_price": unit_price_dec,
            })

        order = Order.objects.create(
            user_id=user_id,
            full_name=full_name,
            phone=phone,
            address=address,
            delivery_date=delivery_date,
            delivery_time=delivery_time,
            discount_code=discount_code if discount_code else "",
            discount_amount=discount_amount,
            product_discount=product_discount,
            subtotal=subtotal_dec,
            total=total_dec,
            created_at=timezone.now()
        )

        for itm in parsed_items:
            OrderItem.objects.create(
                order=order,
                product=itm["product"],
                quantity=itm["quantity"],
                unit_price=itm["unit_price"]
            )

        serialized_order = OrderSerializer(order)
        return Response(serialized_order.data, status=status.HTTP_201_CREATED)


class CategoryProductsAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        subcat_id = self.kwargs['subcategory_id']
        get_object_or_404(SubCategory, pk=subcat_id)
        return Product.objects.filter(subcategories__id=subcat_id).distinct()


class RegisterDeviceTokenAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="Cihaz tokenini qeyd et / yenilə",
        operation_description=(
            "Mobil tərəfdən gələn FCM registration token-i və platform (android/ios) "
            "bu endpoint-ə POST edilməlidir. "
            "Əgər token artıq mövcuddursa, yalnız user və platform yenilənəcək."
        ),
        request_body=DeviceTokenSerializer,
        responses={
            201: openapi.Response(
                description="Token uğurla yadda saxlanıldı",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"detail": "Token qeyd edildi."}
                }
            ),
            400: openapi.Response(description="Yanlış sorğu"),
            401: openapi.Response(description="Authentication tələb olunur"),
        },
    )
    def post(self, request):
        serializer = DeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        platform = serializer.validated_data["platform"]

        UserDeviceToken.objects.filter(
            token=token).exclude(user=request.user).delete()

        UserDeviceToken.objects.update_or_create(
            token=token,
            defaults={"user": request.user, "platform": platform},
        )
        return Response({"detail": "Token qeyd edildi."}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Cihaz tokenini sil",
        operation_description=(
            "Token-i DELETE edərək silmək üçündür. "
            "Body-ə yalnız token string göndərin."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["token"],
            properties={
                "token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Silinəcək FCM registration token"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Token uğurla silindi",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"detail": "Token silindi."}
                }
            ),
            400: openapi.Response(description="token göndərilməyib"),
            401: openapi.Response(description="Authentication tələb olunur"),
        },
    )
    def delete(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "token göndərilməlidir."}, status=status.HTTP_400_BAD_REQUEST)

        UserDeviceToken.objects.filter(user=request.user, token=token).delete()
        return Response({"detail": "Token silindi."}, status=status.HTTP_200_OK)
