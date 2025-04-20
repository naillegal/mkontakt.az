from rest_framework import serializers
from .models import (PartnerSlider, AdvertisementSlide, Brand, Category, Product,
                     ProductType, ProductImage, CustomerReview, Blog, User)
import html
from django.utils.html import strip_tags


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ('id', 'name', 'created_at')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'created_at')


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
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(), required=False, allow_null=True
    )
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), many=True, required=False
    )
    product_types = serializers.PrimaryKeyRelatedField(
        queryset=ProductType.objects.all(), many=True, required=False
    )

    class Meta:
        model = Product
        fields = (
            'id', 'brand', 'categories', 'product_types',
            'title', 'slug', 'description', 'price', 'discount',
            'images',
            'created_at',
        )
        read_only_fields = ('slug', 'created_at')


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
