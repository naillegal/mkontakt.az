from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .utils import get_or_create_cart
import json
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import (
    PartnerSlider, AdvertisementSlide,
    Brand, Category, Product, ProductType, CustomerReview, Blog, ContactMessage, ContactInfo, User, Wish,
    CartItem, DiscountCode, DiscountCodeUse, Order, OrderItem
)
from .serializers import (
    PartnerSliderSerializer, AdvertisementSlideSerializer,
    BrandSerializer, CategorySerializer, ProductTypeSerializer, ProductSerializer,
    CustomerReviewSerializer, BlogSerializer, UserSerializer, UserRegisterSerializer, UserLoginSerializer, UserUpdateSerializer, ChangePasswordSerializer
)
from django.contrib import messages


def about_us(request):
    return render(request, 'about-us.html')


def rules(request):
    return render(request, 'rules.html')


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


class ProductTypeListCreateAPIView(generics.ListCreateAPIView):
    queryset = ProductType.objects.all().order_by('id')
    serializer_class = ProductTypeSerializer


class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer


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


class PartnerSliderListAPIView(generics.ListAPIView):
    queryset = PartnerSlider.objects.all().order_by('created_at')
    serializer_class = PartnerSliderSerializer


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
        messages.success(request, "Qeydiyyat uğurla tamamlandı!")
        return redirect('MContact:index')
    return render(request, 'register.html')


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
    cart = get_or_create_cart(request)
    code_txt = request.POST.get("code", "").strip().upper()
    try:
        code = DiscountCode.objects.get(code=code_txt, active=True)
        if code.expires_at and code.expires_at < timezone.now():
            raise ValidationError
    except (DiscountCode.DoesNotExist, ValidationError):
        return JsonResponse({"error": "Kod tapılmadı və ya deaktivdir"}, status=400)
    DiscountCodeUse.objects.update_or_create(
        cart=cart, defaults={"code": code})
    return JsonResponse({"ok": True, "percent": code.percent, "amount": cart.get_discount_code_amount()})


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
