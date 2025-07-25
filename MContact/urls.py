from django.urls import path
from . import views

app_name = 'MContact'

urlpatterns = [
    path('', views.index, name='index'),
    path('haqqımızda/', views.about_us, name='about_us'),
    path('qaydalar/', views.rules, name='rules'),
    path('şifrə-bərpası/', views.forget_password, name='forget-password'),
    path('otp/', views.otp, name='otp'),
    path('yeni-şifrə/', views.new_password, name='new-password'),
    path('məhsullar/', views.products, name='products'),
    path('məhsullar/<slug:slug>/', views.product_detail, name='product-detail'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog-detail'),
    path('əlaqə/', views.contact, name='contact'),
    path('contact/submit/', views.contact_submit, name='contact-submit'),
    path('qeydiyyat/', views.register, name='register'),
    path('qeydiyyat/otp/', views.register_otp, name='register-otp'),
    path('giriş/', views.login_view, name='login'),
    path('profil-düzəlişi/', views.edit_profile, name='edit_profile'),
    path('şifrəni-dəyiş/', views.change_password, name='change_password'),
    path('istək-siyahısı/', views.wishlist_view, name='wishlist_view'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='wishlist-toggle'),
    path('səbət/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart-add'),
    path('cart/update/', views.cart_update, name='cart-update'),
    path('cart/apply-discount/', views.apply_discount, name='cart-discount'),
    path('sifariş/', views.order_view, name='order'),
    path('order/create/', views.order_create, name='order-create'),
    path('çıxış/', views.logout_view, name='logout'),
]
