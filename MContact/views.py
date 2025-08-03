import random
from datetime import datetime
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
from .utils import get_or_create_cart
import json
from django.utils import timezone
from decimal import Decimal
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import models as dj_models
from django.db.models import Case, When, Value, IntegerField, Prefetch, Count, Exists, OuterRef, BooleanField
from django.views.decorators.csrf import ensure_csrf_cookie
import uuid
from .models import (
    PartnerSlider, AdvertisementSlide,
    Brand, Category, Product, ProductType, CustomerReview, Blog, ContactMessage, ContactInfo, User, Wish,
    CartItem, DiscountCode, DiscountCodeUse, Order, OrderItem, PasswordResetOTP, Cart, UserDeviceToken, HomePageBanner,
    ProductAttribute, ProductVariant, ProductAttributeValue, SubCategory, RegistrationOTP, PushNotification, Branch
)
from .serializers import (
    PartnerSliderSerializer, AdvertisementSlideSerializer,
    BrandSerializer, CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    CustomerReviewSerializer, BlogSerializer, UserSerializer,
    UserRegisterSerializer, UserLoginSerializer, UserUpdateSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, VerifyOtpSerializer, UpdatePasswordSerializer, MobileCartSerializer,
    DiscountCodeSerializer, WishItemSerializer, OrderSerializer, DeviceTokenSerializer,
    ProductFilterRequestSerializer, ProductFilterResponseSerializer, ProductAttributeSerializer, AttributeNameSerializer, AttributeValueSerializer
)
from django.contrib import messages

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "perpage"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)

        try:
            self.page = paginator.page(page_number)
            return list(self.page)
        except (PageNotAnInteger, EmptyPage):
            self.page = None
            self._paginator = paginator            
            self._requested_number = int(page_number) if str(page_number).isdigit() else 1
            return []

    def get_next_link(self):
        if self.page is None:
            return None
        return super().get_next_link()

    def get_previous_link(self):
        if self.page is None:
            return None
        return super().get_previous_link()

    def get_paginated_response(self, data):
        if self.page is not None:
            total_pages = self.page.paginator.num_pages
            total_items = self.page.paginator.count
            current_page = self.page.number
        else:
            total_pages = self._paginator.num_pages
            total_items = self._paginator.count
            current_page = self._requested_number

        return Response({
            "page":       current_page,
            "perpage":    self.get_page_size(self.request),
            "total_pages": total_pages,
            "total_items": total_items,
            "results":    data,
            "next":       self.get_next_link(),
            "previous":   self.get_previous_link(),
        })

    def get_paginated_response(self, data):
        total_pages = (self.page.paginator.num_pages
                       if hasattr(self.page, 'paginator') else 0)
        total_items = (self.page.paginator.count
                       if hasattr(self.page, 'paginator') else 0)
        current_page = (self.page.number
                        if hasattr(self.page, 'number') else 1)

        return Response({
            'page': current_page,
            'perpage': self.get_page_size(self.request),
            'total_pages': total_pages,
            'total_items': total_items,
            'results': data,
            'next': None if not data else self.get_next_link(),
            'previous': self.get_previous_link(),
        })


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

    paginator = Paginator(qs, 24)
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
    other_products = (prio + others)[:12]

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
    serializer_class = ProductListSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        qs = Product.objects.all().order_by("-created_at")
        session_user_id = self.request.session.get("user_id")
        if session_user_id:
            wishlist_qs = Wish.objects.filter(
                user_id=session_user_id,
                product_id=OuterRef('pk')
            )
            qs = qs.annotate(in_wishlist=Exists(wishlist_qs))
        else:
            qs = qs.annotate(in_wishlist=Value(
                False, output_field=BooleanField()))
        return qs


class ProductRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    lookup_field = "pk"

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="user_id",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description="(Optional) İstifadəçi ID‑si — wishlist annotasiyası üçün"
            )
        ],
        responses={
            200: ProductDetailSerializer(),
            400: "Yanlış user_id"
        }
    )
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("user_id")
        if user_id is not None:
            try:
                uid = int(user_id)
            except ValueError:
                raise ValidationError({"user_id": "Integer olmalıdır."})
            if not User.objects.filter(pk=uid).exists():
                raise ValidationError(
                    {"user_id": "Belə bir istifadəçi tapılmadı."})
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = Product.objects.all()
        user_id = self.request.query_params.get("user_id")
        if not user_id:
            user_id = self.request.session.get("user_id")

        if user_id:
            wishlist_qs = Wish.objects.filter(
                user_id=user_id,
                product_id=OuterRef("pk")
            )
            qs = qs.annotate(in_wishlist=Exists(wishlist_qs))
        else:
            qs = qs.annotate(
                in_wishlist=Value(False, output_field=BooleanField())
            )
        return qs


def index(request):
    partners = PartnerSlider.objects.select_related(
        'brand').all().order_by('created_at')
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

    banners = HomePageBanner.objects.order_by('-created_at')

    context = {
        'partners': partners,
        'advertisement_slides': advertisement_slides,
        'slider_title': '',
        'recent_products': recent_products,
        'recent_categories': recent_categories,
        'random_products': random_products,
        'customer_reviews': customer_reviews,
        'wish_ids': wish_ids,
        'banners': banners,
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
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'contact.html', {'contact_info': contact_info, "branches": branches})


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


class RegisterAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="Qeydiyyat üçün OTP kodu göndər",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["full_name", "email", "phone", "birth_date", "password"],
            properties={
                "full_name": openapi.Schema(type=openapi.TYPE_STRING, description="Ad Soyad"),
                "email": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="E-poçt ünvanı"),
                "phone": openapi.Schema(type=openapi.TYPE_STRING, description="Telefon nömrəsi"),
                "birth_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Doğum tarixi (YYYY-MM-DD və ya DD.MM.YYYY)"
                ),
                "password": openapi.Schema(type=openapi.TYPE_STRING, format="password", description="Parol"),
            }
        ),
        responses={
            200: openapi.Response(
                description="OTP kod email-ə göndərildi",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING,
                                                 example="OTP kod email-ə göndərildi.")
                    }
                )
            ),
            400: openapi.Response(description="Validation Error — daxil edilmiş məlumatlarda səhv var")
        }
    )
    def post(self, request):
        full_name = request.data.get("full_name", "").strip()
        email = request.data.get("email", "").strip().lower()
        phone = request.data.get("phone", "").strip()
        birth_str = request.data.get("birth_date", "").strip()
        password = request.data.get("password", "").strip()

        errors = {}
        if not full_name:
            errors["full_name"] = "Ad Soyad mütləqdir."
        if not email:
            errors["email"] = "E-mail mütləqdir."
        if not phone:
            errors["phone"] = "Telefon mütləqdir."
        if not birth_str:
            errors["birth_date"] = "Doğum tarixi mütləqdir."
        if not password:
            errors["password"] = "Parol mütləqdir."
        if User.objects.filter(email=email).exists():
            errors["email"] = "Bu e-mail artıq istifadə olunub."

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            if "-" in birth_str:
                birth_date = datetime.strptime(birth_str, "%Y-%m-%d").date()
            else:
                birth_date = datetime.strptime(birth_str, "%d.%m.%Y").date()
        except ValueError:
            raise ValidationError({
                "birth_date": "Format: YYYY-MM-DD və ya DD.MM.YYYY olmalıdır."
            })

        RegistrationOTP.objects.filter(email=email).delete()
        code = f"{random.randint(0, 9999):04d}"
        RegistrationOTP.objects.create(
            email=email,
            full_name=full_name,
            phone=phone,
            birth_date=birth_date,
            password=password,
            code=code
        )

        send_mail_async(
            subject="MContact – Qeydiyyat OTP kodu",
            message=f"Sizin Qeydiyyat OTP kodunuz: {code}",
            recipient_list=[email],
            fail_silently=False
        )

        return Response(
            {"detail": "OTP kod email-ə göndərildi."},
            status=status.HTTP_200_OK
        )


class RegisterOTPAPIView(APIView):
    serializer_class = VerifyOtpSerializer

    @swagger_auto_schema(
        operation_summary="OTP kodunu yoxla və istifadəçini yarat",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'otp_code'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="E‑poçt ünvanı"
                ),
                'otp_code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="4 rəqəmli OTP kodu"
                ),
                'fcm_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Mobil FCM registration tokeni"
                ),
                'platform': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['android', 'ios'],
                    description="Cihaz platforması"
                ),
            }
        ),
        responses={
            201: openapi.Response(
                description="User yaradıldı",
                schema=UserSerializer()
            ),
            400: openapi.Response(description="Yanlış OTP və ya validation xətası")
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower()
        otp_input = serializer.validated_data['otp_code']

        try:
            reg = RegistrationOTP.objects.get(email=email)
        except RegistrationOTP.DoesNotExist:
            return Response({'detail': 'Bu email üçün OTP göndərilməyib.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if reg.is_expired():
            reg.delete()
            return Response({'detail': 'OTP kodunun vaxtı bitib.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if otp_input != reg.code:
            return Response({'otp_code': 'Yanlış OTP kodu.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create(
            full_name=reg.full_name,
            email=reg.email,
            phone=reg.phone,
            birth_date=reg.birth_date,
            password=reg.password
        )
        reg.delete()

        fcm_token = request.data.get('fcm_token')
        platform = request.data.get('platform')
        if fcm_token:
            UserDeviceToken.objects.update_or_create(
                token=fcm_token,
                defaults={'user': user, 'platform': platform or 'android'}
            )

        return Response(
            UserSerializer(user, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class UserLoginAPIView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer

    @swagger_auto_schema(
        operation_summary="Login və FCM token qeydiyyatı",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="E‑poçt ünvanı"
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='password',
                    description="Parol"
                ),
                'fcm_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Mobil FCM registration tokeni"
                ),
                'platform': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['android', 'ios'],
                    description="Cihaz platforması"
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Login uğurlu oldu",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: openapi.Response(description="Yanlış email/parol və ya validation xətası")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Yanlış email və ya parol.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if user.password != password:
            return Response({'detail': 'Yanlış email və ya parol.'},
                            status=status.HTTP_400_BAD_REQUEST)

        fcm_token = serializer.validated_data.get('fcm_token')
        platform = serializer.validated_data.get('platform')
        if fcm_token:
            UserDeviceToken.objects.update_or_create(
                token=fcm_token,
                defaults={'user': user, 'platform': platform or 'android'}
            )

        return Response({
            'detail': 'Login uğurlu oldu.',
            'user': UserSerializer(user, context={'request': request}).data
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
    variant_id = data.get("variant_id")

    product = get_object_or_404(Product, pk=product_id)
    variant = None
    if variant_id:
        variant = get_object_or_404(
            ProductVariant, pk=variant_id, product=product, is_active=True)

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
        dt_naive = datetime.strptime(
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
            unit_price=item.unit_price,
        )
    cart.items.all().delete()

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
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='(Optional) İstifadəçi ID'),
                'session_key': openapi.Schema(type=openapi.TYPE_STRING, description='(Optional) Session açarı'),
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Məhsulun ID-si'),
                'variant_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='(Optional) Variant ID'),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Əlavə ediləcək miqdar', default=1),
            },
            required=['product_id'],
        ),
        responses={
            200: openapi.Response(description="Uğurlu cavab", schema=MobileCartSerializer()),
            400: "product_id tələb olunur və ya səhv format"
        },
    )
    def post(self, request):
        data = request.data
        user_id = data.get("user_id")
        session_key = data.get("session_key")
        product_id = data.get("product_id")
        variant_id = data.get("variant_id")
        qty = int(data.get("quantity", 1))

        if not product_id:
            return Response({"detail": "product_id tələb olunur."}, status=400)

        product = get_object_or_404(Product, pk=product_id)
        variant = None
        if variant_id is not None:
            variant = get_object_or_404(
                ProductVariant, pk=variant_id, product=product, is_active=True)

        cart, session_key = self._get_or_create_cart(
            user_id=user_id, session_key=session_key)

        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, variant=variant, defaults={
                "quantity": qty}
        )
        if not created:
            item.quantity += qty
            item.save()

        ser = MobileCartSerializer(cart, context={"request": request})
        return Response({"session_key": session_key, "cart": ser.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Səbəti əldə et",
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY,
                              type=openapi.TYPE_INTEGER, description='(Optional) İstifadəçi ID'),
            openapi.Parameter('session_key', openapi.IN_QUERY,
                              type=openapi.TYPE_STRING, description='(Optional) Session açarı'),
        ],
        responses={200: openapi.Response(
            description="Səbət məlumatı", schema=MobileCartSerializer())}
    )
    def get(self, request):
        user_id = request.query_params.get("user_id")
        session_key = request.query_params.get("session_key")

        cart, session_key = self._get_or_create_cart(
            user_id=user_id, session_key=session_key)
        ser = MobileCartSerializer(cart, context={"request": request})
        return Response({"session_key": session_key, "cart": ser.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Səbətdən məhsul sil",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='(Optional) İstifadəçi ID'),
                'session_key': openapi.Schema(type=openapi.TYPE_STRING, description='(Optional) Session açarı'),
                'item_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Silinəcək CartItem ID'),
            },
            required=['item_id'],
        ),
        responses={
            200: openapi.Response(description="Uğurlu cavab", schema=MobileCartSerializer()),
            400: "item_id tələb olunur və ya səhv format",
            404: "CartItem tapılmadı"
        },
    )
    def delete(self, request):
        data = request.data
        user_id = data.get("user_id")
        session_key = data.get("session_key")
        item_id = data.get("item_id")

        if item_id is None:
            return Response({"detail": "item_id tələb olunur."}, status=400)

        cart, session_key = self._get_or_create_cart(
            user_id=user_id, session_key=session_key)

        try:
            CartItem.objects.get(cart=cart, id=item_id).delete()
        except CartItem.DoesNotExist:
            return Response({"detail": "CartItem tapılmadı."}, status=404)

        ser = MobileCartSerializer(cart, context={"request": request})
        return Response({"session_key": session_key, "cart": ser.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Məhsul miqdarını yenilə",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['item_id', 'quantity'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='(Optional) İstifadəçi ID'),
                'session_key': openapi.Schema(type=openapi.TYPE_STRING, description='(Optional) Session açarı'),
                'item_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Yenilənəcək CartItem ID'),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Yeni miqdar', example=3),
            },
        ),
        responses={
            200: openapi.Response(description="Cart yeniləndi", schema=MobileCartSerializer()),
            400: "Validation Error",
            404: "CartItem tapılmadı"
        },
    )
    def patch(self, request):
        data = request.data
        user_id = data.get("user_id")
        session_key = data.get("session_key")
        item_id = data.get("item_id")
        qty = data.get("quantity")

        if item_id is None:
            return Response({"detail": "item_id tələb olunur."}, status=400)
        if qty is None:
            return Response({"detail": "quantity tələb olunur."}, status=400)

        try:
            qty = int(qty)
            if qty < 1:
                raise ValueError
        except ValueError:
            return Response({"detail": "quantity müsbət tam ədəd olmalıdır."}, status=400)

        cart, session_key = self._get_or_create_cart(
            user_id=user_id, session_key=session_key)

        try:
            item = CartItem.objects.get(cart=cart, id=item_id)
        except CartItem.DoesNotExist:
            return Response({"detail": "CartItem tapılmadı."}, status=404)

        item.quantity = qty
        item.save()

        ser = MobileCartSerializer(cart, context={"request": request})
        return Response({"session_key": session_key, "cart": ser.data}, status=status.HTTP_200_OK)


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
                name='user_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description='(Required) İstifadəçi ID-si'
            )
        ],
        responses={
            200: openapi.Response(
                description="Wishlist məhsulları",
                schema=ProductListSerializer(many=True)
            ),
            400: "user_id göndərilməyibsə",
        }
    )
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {"detail": "user_id göndərilməlidir."},
                status=status.HTTP_400_BAD_REQUEST
            )
        get_object_or_404(User, pk=user_id)

        product_ids = Wish.objects.filter(user_id=user_id) \
                                  .values_list('product_id', flat=True)
        products = Product.objects.filter(id__in=product_ids)

        serializer = ProductListSerializer(
            products,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

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
                description="Wishlist yeniləndi",
                schema=ProductListSerializer(many=True)
            ),
            400: "user_id və product_id göndərilməyibsə",
            404: "User və ya Product tapılmadıqda"
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

        Wish.objects.get_or_create(user=user, product=product)

        product_ids = Wish.objects.filter(user=user) \
                                  .values_list('product_id', flat=True)
        products = Product.objects.filter(id__in=product_ids)
        serializer = ProductListSerializer(
            products,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
                description="Wishlist yeniləndi",
                schema=ProductListSerializer(many=True)
            ),
            400: "user_id və product_id göndərilməyibsə",
            404: "User və ya Product tapılmadıqda"
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

        product_ids = Wish.objects.filter(user_id=user_id) \
                                  .values_list('product_id', flat=True)
        products = Product.objects.filter(id__in=product_ids)
        serializer = ProductListSerializer(
            products,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class MobileOrderView(APIView):
    parser_classes = [JSONParser]

    @swagger_auto_schema(
        operation_summary="Mobil sifariş yarat",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "full_name", "phone", "address",
                "delivery_date", "delivery_time",
                "discount_amount", "product_discount", "category_discount",
                "subtotal", "items"
            ],
            properties={
                "user_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="(Optional) İstifadəçi ID"),
                "full_name": openapi.Schema(type=openapi.TYPE_STRING, description="Tam ad", example="Test"),
                "phone": openapi.Schema(type=openapi.TYPE_STRING, description="Telefon", example="+994551234567"),
                "address": openapi.Schema(type=openapi.TYPE_STRING, description="Ünvan", example="Bakı, Nərimanov"),
                "delivery_date": openapi.Schema(type=openapi.TYPE_STRING, description="Çatdırılma tarixi (DD.MM.YYYY)", example="24.07.2025"),
                "delivery_time": openapi.Schema(type=openapi.TYPE_STRING, description="Çatdırılma vaxtı (HH:MM)", example="18:23"),
                "discount_amount": openapi.Schema(type=openapi.TYPE_STRING, description="Endirim Məbləği", example="0.00"),
                "product_discount": openapi.Schema(type=openapi.TYPE_STRING, description="Məhsul Endirimi", example="0.00"),
                "category_discount": openapi.Schema(type=openapi.TYPE_STRING, description="Kateqoriya Endirimi", example="0.00"),
                "subtotal": openapi.Schema(type=openapi.TYPE_STRING, description="Ara Cəm", example="60.00"),
                "items": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="Sifariş Məhsulları",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=["product_id", "quantity", "unit_price"],
                        properties={
                            "product_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=42),
                            "variant_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="(Optional) Variant ID", example=7),
                            "quantity": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                            "unit_price": openapi.Schema(type=openapi.TYPE_STRING, example="30.00"),
                        },
                    ),
                ),
            },
        ),
        responses={
            201: openapi.Response(description="Sifariş uğurla yaradıldı", schema=OrderSerializer()),
            400: "Validation Error",
        },
    )
    def post(self, request, *args, **kwargs):
        data = request.data

        cart, session_key = self._get_or_create_cart(
            user_id=data.get("user_id"),
            session_key=data.get("session_key")
        )

        required = (
            "full_name", "phone", "address",
            "delivery_date", "delivery_time",
            "discount_amount", "product_discount", "category_discount",
            "subtotal", "items",
        )
        for field in required:
            if field not in data:
                raise ValidationError({field: "Bu sahə tələb olunur."})

        def to_decimal(key):
            try:
                return Decimal(str(data[key]))
            except Exception:
                raise ValidationError({key: "Düzgün ədəd formatı deyil."})

        discount_amount = to_decimal("discount_amount")
        product_discount = to_decimal("product_discount")
        category_discount = to_decimal("category_discount")

        date_str = data["delivery_date"]
        time_str = data["delivery_time"]
        try:
            delivery_date = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            raise ValidationError({
                "delivery_date": "Format: DD.MM.YYYY olmalıdır (məs: 24.07.2025)."
            })
        try:
            delivery_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            raise ValidationError({
                "delivery_time": "Format: HH:MM olmalıdır (məs: 18:23)."
            })

        parsed_items = []
        for idx, itm in enumerate(data["items"], start=1):
            if "product_id" not in itm or "quantity" not in itm or "unit_price" not in itm:
                raise ValidationError(
                    {f"items[{idx}]": "product_id, quantity və unit_price tələb olunur."}
                )

            product = get_object_or_404(Product, pk=itm["product_id"])
            variant = None
            if itm.get("variant_id") is not None:
                variant = get_object_or_404(
                    ProductVariant,
                    pk=itm["variant_id"],
                    product=product,
                    is_active=True
                )

            try:
                qty = int(itm["quantity"])
            except Exception:
                raise ValidationError(
                    {f"items[{idx}].quantity": "quantity formatı yanlışdır."}
                )

            if variant and variant.price_override is not None:
                unit_price = variant.price_override
            else:
                unit_price = product.price

            parsed_items.append({
                "product": product,
                "variant": variant,
                "quantity": qty,
                "unit_price": unit_price
            })

        subtotal = sum(
            itm["unit_price"] * itm["quantity"]
            for itm in parsed_items
        )

        shipping_fee = Decimal('0.00') if subtotal >= Decimal(
            '200.00') else Decimal('10.00')
        total = subtotal + shipping_fee

        order = Order.objects.create(
            user_id=data.get("user_id"),
            full_name=data["full_name"],
            phone=data["phone"],
            address=data["address"],
            delivery_date=delivery_date,
            delivery_time=delivery_time,
            discount_amount=discount_amount,
            product_discount=product_discount,
            category_discount=category_discount,
            subtotal=subtotal,
            total=total,
            created_at=timezone.now()
        )

        for itm in parsed_items:
            OrderItem.objects.create(
                order=order,
                product=itm["product"],
                variant=itm["variant"],
                quantity=itm["quantity"],
                unit_price=itm["unit_price"]
            )

        cart.items.all().delete()

        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data, status=201)


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


class MobileProductFilterAPIView(APIView):
    pagination_class = CustomPageNumberPagination

    @swagger_auto_schema(
        operation_summary="Mobile product filter",
        manual_parameters=[
            openapi.Parameter(
                name="page",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Səhifə nömrəsi",
                default=1
            ),
            openapi.Parameter(
                name="perpage",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Səhifədəki element sayı",
                default=10
            ),
            openapi.Parameter(
                name="ordering",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Sıralama: price_asc və ya price_desc"
            ),
            openapi.Parameter(
                name="code",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Məhsul kodu (dəqiq uyğunluq)"
            ),
            openapi.Parameter(
                name="name",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Məhsul adı üzərində axtarış"
            ),
            openapi.Parameter(
                name="1",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                description="Brand filter — həm “&1=10&1=11” həm də “?1=10,11” formatlarını dəstəkləyir",
                items=openapi.Items(type=openapi.TYPE_INTEGER)
            ),
        ],
        responses={200: ProductFilterResponseSerializer()},
    )
    def get(self, request, *args, **kwargs):
        params = request.query_params
        page_num = int(params.get("page", 1))
        perpage = int(params.get("perpage", self.pagination_class.page_size))
        ordering = params.get("ordering")
        code_q = params.get("code", "").strip()
        name_q = params.get("name", "").strip()

        qs = Product.objects.all()

        user_id = request.session.get("user_id")
        if user_id:
            wqs = Wish.objects.filter(
                user_id=user_id, product_id=OuterRef("pk"))
            qs = qs.annotate(in_wishlist=Exists(wqs))
        else:
            qs = qs.annotate(in_wishlist=Value(
                False, output_field=BooleanField()))

        if name_q:
            qs = qs.filter(title__icontains=name_q)
        if code_q:
            qs = qs.filter(code__iexact=code_q)

        raw_brand_vals = params.getlist("1")
        brand_ids = []
        for rv in raw_brand_vals:
            for part in rv.split(","):
                part = part.strip()
                if part.isdigit():
                    brand_ids.append(int(part))
        if brand_ids:
            qs = qs.filter(brand_id__in=brand_ids)

        raw_sub_vals = params.getlist("2")
        sub_ids = []
        for rv in raw_sub_vals:
            for part in rv.split(","):
                part = part.strip()
                if part.isdigit():
                    sub_ids.append(int(part))
        if sub_ids:
            qs = qs.filter(subcategories__id__in=sub_ids).distinct()

        for key in params.keys():
            if key.isdigit() and key not in ("1", "2", "page", "perpage"):
                raw_vals = params.getlist(key)
                vals = []
                for rv in raw_vals:
                    for part in rv.split(","):
                        part = part.strip()
                        if part.isdigit():
                            vals.append(int(part))
                if vals:
                    qs = qs.filter(variants__attribute_values__id__in=vals)

        qs = qs.annotate(
            _prio=Case(
                When(priority__isnull=False, then="priority"),
                default=Value(999999),
                output_field=IntegerField()
            )
        )
        if ordering == "price_asc":
            qs = qs.order_by("price")
        elif ordering == "price_desc":
            qs = qs.order_by("-price")
        else:
            qs = qs.order_by("_prio", "-created_at")

        paginator = self.pagination_class()
        paginator.page_size = perpage
        if hasattr(request.query_params, "_mutable"):
            request.query_params._mutable = True
        request.query_params["page"] = page_num
        page = paginator.paginate_queryset(qs, request, view=self)

        serializer = ProductListSerializer(
            page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class AttributeListAPIView(generics.ListAPIView):

    queryset = ProductAttribute.objects.prefetch_related(
        'values').order_by('id')
    serializer_class = ProductAttributeSerializer
    pagination_class = CustomPageNumberPagination


class AttributeNameListAPIView(generics.ListAPIView):
    queryset = ProductAttribute.objects.all().order_by('name')
    serializer_class = AttributeNameSerializer


class AttributeValueByAttributeAPIView(generics.ListAPIView):
    serializer_class = AttributeValueSerializer

    def get_queryset(self):
        attribute_id = self.kwargs.get('attribute_id')
        return ProductAttributeValue.objects.filter(
            attribute_id=attribute_id
        ).order_by('value')


class FilterOptionsListAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="Filter başlıqları: Brendlər, Kateqoriyalar və Attribute adları",
        responses={
            200: openapi.Response(
                description="ID və name siyahısı",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Sıradakı nömrə'),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Başlıq')
                        }
                    )
                )
            )
        }
    )
    def get(self, request):
        data = [
            {'id': 1, 'name': 'Brendlər'},
            {'id': 2, 'name': 'Kateqoriyalar'},
        ]
        attrs = ProductAttribute.objects.order_by('name') \
            .values_list('name', flat=True)
        for idx, name in enumerate(attrs, start=3):
            data.append({'id': idx, 'name': name})
        return Response(data)


class FilterOptionValuesAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="Seçilmiş FilterOption-a aid dəyərləri qaytarır",
        manual_parameters=[
            openapi.Parameter(
                name='option_id',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                description='FilterOptionsListAPIView-dən gələn id (1,2,3,...)'
            )
        ],
        responses={
            200: openapi.Response(
                description="Seçilmiş option-un dəyərləri",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            ),
            400: openapi.Response(description="Yanlış option_id"),
            404: openapi.Response(description="Mənbə tapılmadı")
        }
    )
    def get(self, request, option_id):
        if option_id == 1:
            qs = Brand.objects.all().order_by('name')
            data = [{'id': b.id, 'name': b.name} for b in qs]
            return Response(data)

        if option_id == 2:
            cats = Category.objects.prefetch_related('subcategories') \
                                   .all().order_by('name')
            data = []
            for c in cats:
                subcats = [
                    {'id': sc.id, 'name': sc.name}
                    for sc in c.subcategories.all().order_by('name')
                ]
                data.append({
                    'id': c.id,
                    'name': c.name,
                    'subcategories': subcats
                })
            return Response(data)

        attr_names = list(
            ProductAttribute.objects
            .order_by('name')
            .values_list('name', flat=True)
        )
        idx = option_id - 3
        if idx < 0 or idx >= len(attr_names):
            return Response({"detail": "Yanlış option_id."},
                            status=status.HTTP_400_BAD_REQUEST)

        attribute = get_object_or_404(ProductAttribute, name=attr_names[idx])
        values = attribute.values.order_by('value')
        data = [{'id': v.id, 'name': v.value} for v in values]
        return Response(data)


class BroadcastNotificationView(APIView):
    @swagger_auto_schema(
        operation_summary="Seçilmiş istifadəçilərə bildiriş göndər",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["user_ids", "title", "message"],
            properties={
                "user_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="Bildiriş göndəriləcək istifadəçilərin ID-ləri",
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    example=[1, 2, 5]
                ),
                "title": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Bildirişin başlığı",
                    example="Kampaniya başladı!"
                ),
                "message": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Bildirişin mətni",
                    example="Bütün məhsullara 20% endirim!"
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Göndərilən token sayı",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "sent": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Göndərilən cihaz tokenlərinin sayı",
                            example=3
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Yoxlanış xətası",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="user_ids, title, message tələb olunur."
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="Heç bir istifadəçi tapılmadı",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="İstifadəçi tapılmadı."
                        )
                    }
                )
            ),
        }
    )
    def post(self, request):
        ids = request.data.get("user_ids", [])
        title = request.data.get("title", "").strip()
        message = request.data.get("message", "").strip()
        if not ids or not title or not message:
            return Response(
                {"detail": "user_ids, title və message mütləqdir."},
                status=status.HTTP_400_BAD_REQUEST
            )

        users = User.objects.filter(id__in=ids)
        if not users.exists():
            return Response({"detail": "İstifadəçi tapılmadı."}, status=status.HTTP_404_NOT_FOUND)

        note = PushNotification.objects.create(title=title, message=message)
        note.recipients.set(users)
        sent_count = note.send()

        return Response({"sent": sent_count}, status=status.HTTP_200_OK)
