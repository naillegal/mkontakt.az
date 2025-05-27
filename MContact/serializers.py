from rest_framework import serializers
from .models import (PartnerSlider, AdvertisementSlide, Brand, Category, Product,
                     ProductType, ProductImage, CustomerReview, Blog, User, CartItem, Cart, DiscountCode, Wish, Order, OrderItem)
import html
from django.utils.html import strip_tags


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ('id', 'name', 'created_at')


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True, required=False)

    class Meta:
        model = Category
        fields = ('id', 'name', 'image', 'created_at')
        read_only_fields = ('created_at',)


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ('id', 'name')


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'created_at')


class ProductSerializer(serializers.ModelSerializer):
    category_names = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    images = serializers.SerializerMethodField()
    formatted_description = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'brand',
            'brand_name',
            'categories',
            'category_names',
            'product_types',
            'title',
            'slug',
            'formatted_description',
            'price',
            'discount',
            'images',
            'created_at',
        )
        read_only_fields = ('slug', 'created_at')

    def get_category_names(self, obj):
        return list(obj.categories.values_list("name", flat=True))

    def get_images(self, obj):
        qs = obj.images.all()
        main = qs.filter(is_main=True).order_by('-created_at').first()
        if main:
            others = qs.exclude(pk=main.pk).order_by('-created_at')
            ordered = [main] + list(others)
        else:
            ordered = qs.order_by('-created_at')

        request = self.context.get('request')
        return [
            (request.build_absolute_uri(img.image.url) if request else img.image.url)
            for img in ordered
        ]

    def get_formatted_description(self, obj):
        return [
            line.strip()
            for line in obj.description.splitlines()
            if line.strip()
        ]


class PartnerSliderSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = PartnerSlider
        fields = ('id', 'title', 'image')


class AdvertisementSlideSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = AdvertisementSlide
        fields = ('id', 'title', 'description', 'image', 'link')


class CustomerReviewSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True, required=False)

    class Meta:
        model = CustomerReview
        fields = ('id', 'full_name', 'image', 'review', 'created_at')
        read_only_fields = ('created_at',)


class BlogSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True, required=False)

    class Meta:
        model = Blog
        fields = ('id', 'title', 'slug', 'description', 'image', 'created_at')

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['description'] = html.unescape(strip_tags(instance.description))
        return rep


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone',
                  'birth_date', 'password', 'image']
        extra_kwargs = {
            'password': {'write_only': True},
            'image': {'required': False}
        }

    def create(self, validated_data):
        return User.objects.create(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone',
                  'birth_date', 'image', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "birth_date",
            "image",
        ]
        read_only_fields = []
        extra_kwargs = {
            "full_name":  {"required": False},
            "email":      {"required": False},
            "phone":      {"required": False},
            "birth_date": {"required": False},
            "image":      {"required": False},
        }


class ChangePasswordSerializer(serializers.Serializer):
    id = serializers.IntegerField(write_only=True)
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=4)


class UpdatePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField()


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source="product.id")
    product_title = serializers.CharField(source="product.title")
    product_image = serializers.SerializerMethodField()
    unit_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="product.price"
    )
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = (
            "id", "product_id", "product_title",
            "product_image", "quantity",
            "unit_price", "line_total",
        )

    def get_product_image(self, obj):
        url = obj.product.get_main_image_url()
        req = self.context.get("request")
        return req.build_absolute_uri(url) if req else url

    def get_line_total(self, obj):
        return obj.product.price * obj.quantity


class MobileCartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    raw_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True)
    product_discount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.SerializerMethodField()
    grand_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = (
            "id", "user_id", "session_key",
            "items",
            "raw_total", "product_discount",
            "discount_amount", "grand_total",
        )

    def get_discount_amount(self, obj):
        return obj.get_discount_code_amount()


class DiscountCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCode
        fields = ('id', 'code', 'percent', 'active', 'expires_at')
        read_only_fields = ('id',)


class WishItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_title = serializers.CharField(
        source='product.title', read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = Wish
        fields = (
            'id',
            'product_id',
            'product_title',
            'product_image',
            'created_at',
        )

    def get_product_image(self, obj):
        url = obj.product.get_main_image_url()
        req = self.context.get('request')
        return req.build_absolute_uri(url) if req else url


class OrderItemMiniSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(
        source="product.title", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("product_id", "product_title", "quantity", "unit_price")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "user_id", "full_name", "phone", "address",
            "delivery_date", "delivery_time",
            "subtotal", "product_discount", "discount_amount", "total",
            "created_at", "items"
        )
        read_only_fields = ("id", "subtotal", "product_discount",
                            "discount_amount", "total", "created_at", "items")
