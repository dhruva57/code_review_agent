from celery import shared_task

from reviews.constants.fields import STATUS_COMPLETED, STATUS_FAILED, STATUS_PROCESSING
from reviews.models import ReviewRequest
from reviews.services import run_manual_review


@shared_task
def run_manual_review_task(review_request_id):
    review_request = ReviewRequest.objects.get(id=review_request_id)

    try:
        review_request.status = STATUS_PROCESSING
        review_request.save(update_fields=["status"])
        run_manual_review(review_request)
        review_request.status = STATUS_COMPLETED
    except Exception:
        review_request.status = STATUS_FAILED
    finally:
        review_request.save(update_fields=["status"])
