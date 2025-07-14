from rest_framework import serializers
from .models import (
    PartnerSlider, AdvertisementSlide, Brand, Category, Product,
    ProductType, ProductImage, CustomerReview,
    Blog, User, CartItem, Cart, DiscountCode, Wish, Order, OrderItem, UserDeviceToken,
    ProductAttribute, ProductVariant, ProductAttributeValue, SubCategory
)
import html
from django.utils.html import strip_tags
from decimal import Decimal, ROUND_HALF_UP


class AttributeValueMiniSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(
        source="attribute.name", read_only=True
    )

    class Meta:
        model = ProductAttributeValue
        fields = ("id", "attribute_name", "value")


class ProductAttributeSerializer(serializers.ModelSerializer):
    values = AttributeValueMiniSerializer(many=True, read_only=True)

    class Meta:
        model = ProductAttribute
        fields = ("id", "name", "values")


class ProductVariantSerializer(serializers.ModelSerializer):
    attribute_values = AttributeValueMiniSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ("id", "code", "price_override",
                  "is_active", "attribute_values")


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ('id', 'name', 'created_at')


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ("id", "name", "slug")


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True, required=False)
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'image', 'subcategories', 'created_at')
        read_only_fields = ('created_at',)


# class ProductTypeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProductType
#         fields = ('id', 'name')


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'created_at')


class ProductListSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    subcategory_names = serializers.SerializerMethodField()
    category_ids = serializers.SerializerMethodField()
    category_names = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    has_variants = serializers.BooleanField(
        source="variants.exists", read_only=True)
    variants = serializers.SerializerMethodField()
    in_wishlist = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "brand",
            "brand_name",
            "category_ids",
            "category_names",
            "subcategories",
            "subcategory_names",
            "title",
            "price",
            "image",
            "code",
            "has_variants",
            "variants",
            "in_wishlist",
        )

    def get_price(self, obj):
        return "{:.2f}".format(
            obj.price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

    def get_image(self, obj):
        qs = obj.images.all()
        main = qs.filter(is_main=True).order_by("-created_at").first()
        img = main or qs.order_by("-created_at").first()
        if not img:
            return None
        req = self.context.get("request")
        return req.build_absolute_uri(img.image.url) if req else img.image.url

    def get_subcategory_names(self, obj):
        return list(obj.subcategories.values_list("name", flat=True))

    def get_category_ids(self, obj):
        return list(
            obj.subcategories.values_list("category_id", flat=True).distinct()
        )

    def get_category_names(self, obj):
        return list(
            obj.subcategories
               .select_related("category")
               .values_list("category__name", flat=True)
               .distinct()
        )

    def get_variants(self, obj):
        variants = getattr(obj, "filtered_variants", obj.variants.all())
        return ProductVariantSerializer(variants, many=True, context=self.context).data


class ProductDetailSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    subcategory_names = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source="brand.name", read_only=True)

    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "title", "code", "description",
            "images", "price",
            "brand", "brand_name",
            "subcategories", "subcategory_names",
            "variants",
        )

    def get_price(self, obj):
        dec = Decimal(obj.price).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
        return "{:.2f}".format(dec)

    def get_subcategory_names(self, obj):
        return list(obj.subcategories.values_list("name", flat=True))

    def get_images(self, obj):
        qs = obj.images.all()
        main = qs.filter(is_main=True).order_by("-created_at").first()
        if main:
            ordered = [main] + \
                list(qs.exclude(pk=main.pk).order_by("-created_at"))
        else:
            ordered = list(qs.order_by("-created_at"))

        req = self.context.get("request")
        def make(i): return req.build_absolute_uri(
            i.image.url) if req else i.image.url
        return [make(i) for i in ordered]

    def get_attributes(self, obj):
        qs = (ProductAttribute.objects
              .filter(values__product_variants__product=obj)
              .distinct()
              .prefetch_related("values"))
        return ProductAttributeSerializer(qs, many=True).data


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

    variant_id = serializers.IntegerField(source="variant.id", read_only=True)
    selected_attrs = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = (
            "id", "product_id", "product_title",
            "product_image", "quantity", "unit_price",
            "line_total", "variant_id", "selected_attrs",
        )

    def get_product_image(self, obj):
        url = obj.product.get_main_image_url()
        req = self.context.get("request")
        return req.build_absolute_uri(url) if req else url

    def get_line_total(self, obj):
        return obj.product.price * obj.quantity

    def get_selected_attrs(self, obj):
        return obj.selected_attrs

    def get_unit_price(self, obj):
        if obj.variant and obj.variant.price_override is not None:
            return obj.variant.price_override
        return obj.product.price


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
    variant_id = serializers.IntegerField(source="variant.id", read_only=True)
    selected_attrs = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = (
            "product_id", "product_title",
            "quantity", "unit_price",
            "variant_id", "selected_attrs",
        )

    def get_selected_attrs(self, obj):
        return obj.variant and [
            {"name": v.attribute.name, "value": v.value}
            for v in obj.variant.attribute_values.all()
        ] or []


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
        read_only_fields = (
            "id", "subtotal", "product_discount",
            "discount_amount", "total", "created_at", "items"
        )


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDeviceToken
        fields = ("token", "platform")


class AttributeValueFilterSerializer(serializers.Serializer):
    attribute_id = serializers.IntegerField(required=False)
    value_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )


class ProductFilterRequestSerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    perpage = serializers.IntegerField(required=False, min_value=1,
                                       max_value=100, default=10)
    ordering = serializers.ChoiceField(
        choices=["price_asc", "price_desc"], required=False
    )
    brand_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False)
    category_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False)
    subcategory_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False)
    attributes = AttributeValueFilterSerializer(many=True, required=False)
    code = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)


class ProductFilterResponseSerializer(serializers.Serializer):
    page = serializers.IntegerField()
    perpage = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    total_items = serializers.IntegerField()
    results = serializers.ListField(
        child=serializers.DictField()
    )


class AttributeNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ('id', 'name')


class AttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttributeValue
        fields = ('id', 'value')
