from django.conf.urls import url

from accounts.forms import UserLoginForm
from . import views
from django.contrib.auth.views import (
    LoginView, LogoutView as logout, PasswordResetView as password_reset,
    PasswordResetDoneView as password_reset_done, PasswordResetConfirmView as password_reset_confirm,
    PasswordResetCompleteView as password_reset_complete
)
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    url(r'^login/$', auth_views.LoginView.as_view(template_name='accounts/login.html', authentication_form=UserLoginForm), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(template_name='accounts/logout.html'), name='logout'),
    url(r'^register/$', views.register, name='register'),
    url(r'^profile/$', views.view_profile, name='view_profile'),
    url(r'^profile/(?P<pk>\d+)/$', views.view_profile, name='view_profile_with_pk'),
    url(r'^profile/edit/$', views.edit_profile, name='edit_profile'),
    url(r'^change-password/$', views.change_password, name='change_password'),
    url(r'^reset-password/$', auth_views.PasswordResetView.as_view(), {'template_name': 'accounts/reset_password.html', 'post_reset_redirect': 'accounts:password_reset_done', 'email_template_name': 'accounts/reset_password_email.html'}, name='reset_password'),
    url(r'^reset-password/done/$', password_reset_done, {'template_name': 'accounts/reset_password_done.html'}, name='password_reset_done'),
    url(r'^reset-password/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', password_reset_confirm, {'template_name': 'accounts/reset_password_confirm.html', 'post_reset_redirect': 'accounts:password_reset_complete'}, name='password_reset_confirm'),
    url(r'^reset-password/complete/$', password_reset_complete,{'template_name': 'accounts/reset_password_complete.html'}, name='password_reset_complete')

]
