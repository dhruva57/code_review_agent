from django.urls import path

from reviews import views


app_name = "reviews"

urlpatterns = [
    path("", views.review_request_create, name="create"),
    path("<int:review_id>/", views.review_request_detail, name="detail"),
]
