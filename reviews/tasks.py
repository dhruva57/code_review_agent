from celery import shared_task

from reviews.constants.fields import STATUS_COMPLETED, STATUS_FAILED, STATUS_PROCESSING
from reviews.llm_services import run_llm_review
from reviews.models import ReviewRequest
from reviews.services import run_manual_review, run_parser_review


@shared_task
def run_manual_review_task(review_request_id):
    review_request = ReviewRequest.objects.get(id=review_request_id)

    try:
        review_request.status = STATUS_PROCESSING
        review_request.save(update_fields=["status"])
        parser_findings = run_parser_review(review_request)
        run_llm_review(review_request, parser_findings)
        review_request.status = STATUS_COMPLETED
        review_request.save(update_fields=["status"])
    except Exception:
        review_request.status = STATUS_FAILED
        review_request.save(update_fields=["status"])
        raise
