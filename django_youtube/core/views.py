from django.shortcuts import render, redirect
from django import forms
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.base import View

from django.conf import settings

from oauth2client.client import flow_from_clientsecrets, OAuth2WebServerFlow
from oauth2client.contrib import xsrfutil
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from .models import CredentialsModel

import tempfile
from django.http import HttpResponse,HttpResponseBadRequest
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Create your views here.

class YouTubeForm(forms.Form):
	video = forms.FileField()

class HomePageView(FormView):
	template_name='core/home.html'
	form_class=YouTubeForm

	def form_valid(self,form):
		fname=form.cleaned_data['video'].temporary_file_path()
		storage=DjangoORMStorage(
			CredentialsModel,'id',self.request.user.id,'credential')
		credentials=storage.get()

		client=build('youtube','v3',credentials=credentials)

		body={
			'snippet':{
				'title':'My Django Youtube Video',
				'description':'My Django Youtube Description',
				'tags':'django,howto,video,api',
				'categoryId':'27',


			},
			'status':{
				'privacyStatus':'unlisted'
			}
		}

		with tempfile.NamedTemporaryFile('wb',suffix='yt-django') as tmpfile:
			with open(fname,'rb') as fileobj:
				tmpfile.write(fileobj.read())
				insert_request=client.videos().insert(
					part=','.join(body.keys()),
					body=body,
					media_body=MediaFileUpload(
                        tmpfile.name, chunksize=-1, resumable=True))
				insert_request.execute()
		return redirect()




class AuthorizeView(View):

	def get(self,request, *args, **kwargs):
		storage=DjangoORMStorage(
			CredentialsModel,'id',request.user.id,'credential')
		credential=storage.get()
		flow=OAuth2WebServerFlow(
			client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
			client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
			scope='https://www.googleapis.com/auth/youtube',
			redirect_uri='http://localhost:8000/oauth2callback/'
			)

		if credential is None or credential.invalid==True:
			flow.params['state']=xsrfutil.generate_token(settings.SECRET_KEY,request.user)
			authorize_url=flow.step1_get_authorize_url()
			return redirect(authorize_url)
		return redirect('/')


flow = OAuth2WebServerFlow(
	client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
	client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
	scope='https://www.googleapis.com/auth/youtube',
	redirect_uri='http://localhost:8000/oauth2callback/'
	)

class OAuth2CallbackView(View):
	def get(self,request,*args,**kwargs):
		if not xsrfutil.validate_token(settings.SECRET_KEY, request.GET.get('state').encode(),request.user):
			return HttpResponseBadRequest()
		credential=flow.step2_exchange(request.GET)
		storage=DjangoORMStorage(
			CredentialsModel,'id',request.user.id, 'credential')
		storage.put(credential)
		return redirect('/')






