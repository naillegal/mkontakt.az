from django.contrib import admin
from django.utils.html import format_html
from .models import (
    PartnerSlider, AdvertisementSlide,
    Brand, Category, Product, ProductType, ProductImage, CustomerReview, Blog,
    ContactMessage, ContactInfo, User, Wish, Cart, CartItem, DiscountCode, Order,
    OrderItem, BlogImage, SiteConfiguration, HomePageBanner, ProductAttribute, ProductAttributeValue,
    ProductVariant, SubCategory, PushNotification
)
from django.http import HttpResponse
import openpyxl
from modeltranslation.admin import TranslationAdmin


class CustomTranslationAdmin(TranslationAdmin):
    group_fieldsets = True

    class Media:
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    inlines = [ProductAttributeValueInline]
    search_fields = ("name",)


class ProductVariantInline(admin.StackedInline):
    model = ProductVariant
    extra = 0
    filter_horizontal = ("attribute_values",)
    fields = ("code", "attribute_values", "price_override", "is_active")


@admin.register(Brand)
class BrandAdmin(CustomTranslationAdmin):
    list_display = ('name', 'name_en', 'name_ru', 'created_at')
    search_fields = ('name', 'name_en', 'name_ru')


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1
    fields = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(CustomTranslationAdmin):
    list_display = ('name', 'name_en', 'name_ru', 'discount', 'created_at')
    search_fields = ('name', 'name_en', 'name_ru')
    inlines = [SubCategoryInline]


# @admin.register(ProductType)
# class ProductTypeAdmin(CustomTranslationAdmin):
#     list_display = ('name', 'name_en', 'name_ru')
#     search_fields = ('name', 'name_en', 'name_ru')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)
    fields = ('image', 'is_main', 'image_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:100px; height:80px; object-fit:cover; '
                'border:1px solid #ddd; border-radius:4px; margin:5px 0;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Şəkil önizləmə"


@admin.register(Product)
class ProductAdmin(CustomTranslationAdmin):
    exclude = ('product_types',)
    list_display = (
        'main_image_preview',
        'title',
        'priority',
        'code',
        'brand',
        'get_subcategories',
        'price',
        'discount',
        'is_active',
        'created_at',
    )
    list_editable = ('priority',)
    search_fields = ('title', 'title_en', 'title_ru', 'brand__name')
    list_filter = ('brand', 'subcategories__category',
                   'subcategories', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('subcategories', 'attributes',)
    inlines = [ProductImageInline, ProductVariantInline]

    def get_subcategories(self, obj):
        return ", ".join(sc.name for sc in obj.subcategories.all())
    get_subcategories.short_description = "Alt Kateqoriyalar"

    def main_image_preview(self, obj):
        url = obj.get_main_image_url()
        if url:
            return format_html(
                '<img src="{}" style="max-height:60px; object-fit:contain; border:1px solid #ddd;"/>',
                url
            )
        return "-"
    main_image_preview.short_description = "Əsas Şəkil"
    main_image_preview.allow_tags = True


@admin.register(PartnerSlider)
class PartnerSliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_en', 'title_ru', 'created_at')
    search_fields = ('title', 'title_en', 'title_ru')


@admin.register(AdvertisementSlide)
class AdvertisementSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_en', 'title_ru', 'created_at')
    search_fields = ('title', 'title_en', 'title_ru',
                     'description', 'description_en', 'description_ru')


@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'full_name_en', 'full_name_ru', 'created_at')
    search_fields = ('full_name', 'full_name_en', 'full_name_ru',
                     'review', 'review_en', 'review_ru')


class BlogImageInline(admin.TabularInline):
    model = BlogImage
    extra = 1
    readonly_fields = ('image_preview',)
    fields = ('image', 'is_main', 'image_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:100px;height:80px;object-fit:cover;'
                'border:1px solid #ddd;border-radius:4px;margin:5px 0;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Şəkil önizləmə"


@admin.register(Blog)
class BlogAdmin(CustomTranslationAdmin):
    list_display = ('title', 'title_en', 'title_ru', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'title_en', 'title_ru',
                     'description', 'description_en', 'description_ru')
    inlines = [BlogImageInline]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'viewed', 'created_at')
    list_filter = ('viewed', 'created_at')
    search_fields = ('name', 'phone', 'email', 'message')


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = (
        'technical_label', 'technical_label_en', 'technical_label_ru',
        'technical_email_label', 'technical_email_label_en', 'technical_email_label_ru',
        'support_label', 'support_label_en', 'support_label_ru',
        'support_email_label', 'support_email_label_en', 'support_email_label_ru',
    )
    search_fields = (
        'technical_label', 'technical_label_en', 'technical_label_ru',
        'support_label', 'support_label_en', 'support_label_ru',
    )


class WishInline(admin.TabularInline):
    model = Wish
    extra = 0
    can_delete = False


class CartInline(admin.TabularInline):
    model = Cart
    extra = 0
    readonly_fields = ('session_key', 'created_at', 'updated_at')
    can_delete = False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'birth_date', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    inlines = [WishInline, CartInline]

    actions = ['export_users_to_excel']

    def export_users_to_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Users"

        headers = ['Ad Soyad', 'Email', 'Telefon', 'Doğum Tarixi']
        ws.append(headers)

        for user in queryset:
            ws.append([
                user.full_name,
                user.email,
                user.phone,
                user.birth_date.strftime('%Y-%m-%d'),
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=users.xlsx'

        wb.save(response)
        return response

    export_users_to_excel.short_description = "Seçilən istifadəçiləri Excel-ə export et"


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "percent", "active", "expires_at")
    list_filter = ("active",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone",
        "product_discount",
        "category_discount",
        "shipping_fee",
        "total",
        "created_at"
    )
    readonly_fields = (
        "discount_amount",
        "product_discount",
        "category_discount",
        "subtotal",
        "shipping_fee",
        "total",
        "created_at",
    )
    fieldsets = (
        (None, {
            "fields": (
                "user",
                "full_name", "phone", "address",
                "delivery_date", "delivery_time",
            )
        }),
        ("Endirimlər", {
            "fields": (
                "discount_amount",
                "product_discount",
                "category_discount",
            )
        }),
        ("Yekun Hesablamalar", {
            "fields": ("subtotal", "shipping_fee", "total")
        }),
        ("Vaxt Stempləri", {
            "fields": ("created_at",)
        }),
    )
    inlines = [OrderItemInline]


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ("__str__", "navbar_logo")


@admin.register(HomePageBanner)
class HomePageBannerAdmin(CustomTranslationAdmin):
    list_display = ('title', 'title_en', 'title_ru', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display   = ("title", "created_at")
    filter_horizontal = ("recipients",)   
    readonly_fields  = ("created_at",)