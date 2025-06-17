from modeltranslation.translator import register, TranslationOptions
from .models import (
    Brand, Category, ProductType, Product,
    PartnerSlider, AdvertisementSlide,
    CustomerReview, Blog, ContactInfo,
)


@register(Brand)
class BrandTranslationOptions(TranslationOptions):
    fields = (
        'name',
    )


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = (
        'name',
    )


@register(ProductType)
class ProductTypeTranslationOptions(TranslationOptions):
    fields = (
        'name',
    )


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'description',
    )


@register(PartnerSlider)
class PartnerSliderTranslationOptions(TranslationOptions):
    fields = (
        'title',
    )


@register(AdvertisementSlide)
class AdvertisementSlideTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'description',
    )


@register(CustomerReview)
class CustomerReviewTranslationOptions(TranslationOptions):
    fields = (
        'full_name',
        'review',
    )


@register(Blog)
class BlogTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'description',
    )


@register(ContactInfo)
class ContactInfoTranslationOptions(TranslationOptions):
    fields = (
        'technical_label',
        'technical_email_label',
        'technical_mobile_label',
        'support_label',
        'support_email_label',
        'support_mobile_label',
    )
