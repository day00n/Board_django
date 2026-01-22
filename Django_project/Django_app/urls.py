from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
#    path('', views.issue_list, name='issue_list'),
    path('post', views.post, name='post'),
    path('detail/<int:post_id>/', views.detail, name='detail'),  
    path('sync', views.sync, name='sync'),
]
