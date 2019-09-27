from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import HomePageView,AuthorizeView,OAuth2CallbackView

urlpatterns=[
	path('',HomePageView.as_view(), name='home'),
	path('authorize/',AuthorizeView.as_view(), name='authorize'),
	path('oauth2callback/',OAuth2CallbackView.as_view(), name='oauth2callback'),
	path('show_video/',ShowView.as_view(),name='show_video'),
]

if settings.DEBUG:
	urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
