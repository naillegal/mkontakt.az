from django.urls import path
from . import views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

app_name = 'MContact'

schema_view = get_schema_view(
    openapi.Info(
        title="MContact API List",
        default_version='v1',
        description="MContact üçün API endpointləri",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('api/swagger/', schema_view.with_ui('swagger'), name='schema-swagger-ui'),
    path('', views.index, name='index'),
    path('about-us/', views.about_us, name='about_us'),
    path('rules/', views.rules, name='rules'),
    path('forget-password/', views.forget_password, name='forget-password'),
    path('otp/', views.otp, name='otp'),
    path('new-password/', views.new_password, name='new-password'),
    path('products/', views.products, name='products'),
    path('products/<slug:slug>/', views.product_detail, name='product-detail'),
    path('api/brands/', views.BrandListCreateAPIView.as_view(),
         name='brand-list-create'),
    path('api/categories/', views.CategoryListCreateAPIView.as_view(),
         name='category-list-create'),
    path('api/product-types/', views.ProductTypeListCreateAPIView.as_view(),
         name='producttype-list-create'),
    path('api/products/', views.ProductListCreateAPIView.as_view(),
         name='product-list-create'),
    path('api/partners/', views.PartnerSliderListAPIView.as_view(),
         name='partner-slider-list'),
    path('api/advertisements/', views.AdvertisementSlideListAPIView.as_view(),
         name='advertisement-slide-list'),
    path('api/customer-reviews/', views.CustomerReviewListCreateAPIView.as_view(),
         name='customer-review-list-create'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog-detail'),
    path('api/blogs/', views.BlogListCreateAPIView.as_view(),
         name='blog-list-create'),
    path('api/blogs/<slug:slug>/',
         views.BlogRetrieveUpdateDestroyAPIView.as_view(), name='blog-detail-api'),
    path('contact/', views.contact, name='contact'),
    path('contact/submit/', views.contact_submit, name='contact-submit'),
    path('api/register/', views.UserRegisterAPIView.as_view(), name='user-register'),
    path('api/login/', views.UserLoginAPIView.as_view(), name='user-login'),
    path('api/users/', views.UserListAPIView.as_view(), name='user-list'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('api/update-profile/', views.UserProfileUpdateAPIView.as_view(),
         name='user-profile-update'),
    path("change-password/", views.change_password, name="change_password"),
    path("api/change-password/", views.ChangePasswordAPIView.as_view(),
         name="change-password"),
    path("wishlist/", views.wishlist_view, name="wishlist_view"),
    path("wishlist/toggle/<int:product_id>/",
         views.toggle_wishlist, name="wishlist-toggle"),
    path("cart/", views.cart_view, name="cart_view"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart-add"),
    path("cart/update/", views.cart_update,
         name="cart-update"),
    path("cart/apply-discount/", views.apply_discount, name="cart-discount"),
    path('order/', views.order_view, name='order'),
    path("order/create/", views.order_create, name="order-create"),
    path('logout/', views.logout_view, name='logout'),
    path('api/logout/', views.LogoutAPIView.as_view(), name='api-logout'),
]
