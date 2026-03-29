# import logging
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from reviews.constants.fields import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_PROCESSING,
)
from reviews.forms import ReviewRequestForm
from reviews.models import ReviewRequest
from reviews.services import run_manual_review
from reviews.tasks import run_manual_review_task

# from reviews.constants.api import HTTP_METHODS
# logger = logging.getLogger(__name__)


# Create your views here.
def review_request_create(request):
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
            print(f"review_request: {review_request}")
            print(run_manual_review_task.app.conf.task_always_eager)
            transaction.on_commit(
                lambda: run_manual_review_task.delay(review_request.id)
            )

            # try:
            #     review_request.status = STATUS_PROCESSING
            #     run_manual_review(review_request)
            #     review_request.status = STATUS_COMPLETED
            # except Exception:
            #     review_request.status = STATUS_FAILED
            # finally:
            #     review_request.save(update_fields=["status"])

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
        "comments": review_request.comments.all(),
    }
    return HttpResponse(template.render(context, request))
