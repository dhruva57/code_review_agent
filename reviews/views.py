from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from reviews.constants.fields import STATUS_PENDING
from reviews.forms import ReviewRequestForm
from reviews.models import ReviewRequest

# from reviews.constants.api import HTTP_METHODS


# Create your views here.
def review_request_create(request):
    print(f"request:{request}")
    if request.method == "POST":
        form = ReviewRequestForm(request.POST)

        if form.is_valid():
            review_request = ReviewRequest(
                title=form.cleaned_data["title"],
                filename=form.cleaned_data["filename"],
                code=form.cleaned_data["code"],
                status=STATUS_PENDING,
            )
            review_request.save()

            return HttpResponseRedirect(f"/reviews/{review_request.id}/")

    else:
        form = ReviewRequestForm()

    template = loader.get_template("reviews/review_request_form.html")
    context = {
        "form": form,
    }

    return HttpResponse(template.render(context, request))


def review_request_detail(request, review_id):
    try:
        review_request = ReviewRequest.objects.get(id=review_id)
    except ReviewRequest.DoesNotExist:
        return HttpResponse("Review request not found", status=404)
    
    template = loader.get_template("reviews/review_request_detail.html")
    context = {
        "review_request": review_request,
        "comments": review_request.comments.all()
    }
    return HttpResponse(template.render(context, request))
