from django.shortcuts import render, redirect
from django import forms
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.base import View

from django.conf import settings

from oauth2client.client import flow_from_clientsecrets, OAuth2WebServerFlow
from oauth2client.contrib import xsrfutil
from oauth2client.tools import argparser
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from .models import CredentialsModel

import tempfile
from django.http import HttpResponse,HttpResponseBadRequest
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
from embed_video.fields import EmbedVideoField
from apiclient.discovery import build
from apiclient.errors import HttpError
from django.views.decorators.csrf import requires_csrf_token

# Create your views here.
DEVELOPER_KEY="AIzaSyBC47N-lpeWWnXEG4yMHmpcVC6b3rQwXEY"
YOUTUBE_API_SERVICE_NAME="youtube"
YOUTUBE_API_VERSION="v3"


@requires_csrf_token
def youtube_search(request):
	q="My Python Youtube Video" 
	max_results=50
	order="relevance"
	token=None
	location=None
	location_radius=None
	print(q)
	youtube=googleapiclient.discovery.build(YOUTUBE_API_SERVICE_NAME,YOUTUBE_API_VERSION,developerKey=DEVELOPER_KEY)
	search_response=youtube.search().list(q=q,type="video",pageToken=token,order=order,part="snippet",maxResults=max_results,location=location,locationRadius=location_radius).execute()


	title=[]
	channelId=[]
	channelTitle=[]
	categoryId=[]
	videoId=[]
	viewCount=[]
	likeCount=[]
	dislikeCount=[]
	commentCount=[]
	favoriteCount=[]
	category=[]
	tags=[]
	videos=[]

	for search_result in search_response.get("items",[]):
		if search_result['id']['kind']=='youtube#video':
			title.append(search_result['snippet']['title'])
			videoId.append(search_result['id']['videoId'])

		response=youtube.videos().list(
			part='statistics,snippet',id=search_result['id']['videoId']).execute()

		channelId.append(response['items'][0]['snippet']['channelId'])
		channelTitle.append(response['items'][0]['snippet']['channelTitle'])
		categoryId.append(response['items'][0]['snippet']['categoryId'])
		favoriteCount.append(response['items'][0]['statistics']['favoriteCount'])
		viewCount.append(response['items'][0]['statistics']['viewCount'])
		likeCount.append(response['items'][0]['statistics']['likeCount'])
		dislikeCount.append(response['items'][0]['statistics']['dislikeCount'])

		if 'commentCount' in response['items'][0]['statistics'].keys():
			commentCount.append(response['items'][0]['statistics']['commentCount'])
		else:
			commentCount.append([])

		if 'tags' in response['items'][0]['snippet'].keys():
			tags.append(response['items'][0]['snippet']['tags'])
		# else:
		# 	tags.append()
		youtube_dict={
		'tags':tags,
		'channelId':"63lFwLa5B1Q",
		'channelTitle':channelTitle,
		'categoryId':categoryId,
		'title':title,
		'videoId':videoId,
		'viewCount':viewCount,
		'likeCount':likeCount,
		'dislikeCount':dislikeCount,
		'commentCount':commentCount,
		'favoriteCount':favoriteCount

		}
		print(youtube_dict)
	return HttpResponse("youtube_dict")
	#return render(request,'core/home.html')

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
				'title':'My Python Youtube Video',
				'description':'My Python Youtube Description',
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
				result=insert_request.execute()
				video_id=result['id']
				html='<html><body><iframe width="420" height="315" src="https://www.youtube.com/embed/{0}"></iframe></body></html>'.format(video_id)
				#print(api_key)
		
		#print(type(youtube))
	


		

		return HttpResponse(html)




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


