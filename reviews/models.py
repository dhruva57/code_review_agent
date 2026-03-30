from django.db import models
from .constants.fields import (
    SEVERITY_CHOICES,
    SOURCE_PARSER,
    SOURCES_CHOICES,
    STATUS_CHOICES,
    STATUS_PENDING,
)


# Create your models here.
class ReviewRequest(models.Model):

    title = models.CharField(max_length=255, blank=True)
    code = models.TextField()
    filename = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or self.filename or f"ReviewRequest {self.id}"


class ReviewComment(models.Model):

    review_request = models.ForeignKey(
        ReviewRequest, on_delete=models.CASCADE, related_name="comments"
    )
    source = models.CharField(
        max_length=20, choices=SOURCES_CHOICES, default=SOURCE_PARSER
    )
    rule_id = models.CharField(max_length=100)
    severity = models.CharField(choices=SEVERITY_CHOICES, max_length=20)
    file = models.CharField(blank=True, max_length=255)
    line = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField()
    suggestion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source}: {self.rule_id} ({self.severity})"
