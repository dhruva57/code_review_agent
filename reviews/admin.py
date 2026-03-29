from django.contrib import admin

from reviews.models import ReviewComment, ReviewRequest

admin.site.register(ReviewRequest)
admin.site.register(ReviewComment)

# Register your models here.
