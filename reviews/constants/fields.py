# Status Choices
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

STATUS_CHOICES = [
    (STATUS_PENDING, "Pending"),
    (STATUS_PROCESSING, "Processing"),
    (STATUS_COMPLETED, "Completed"),
    (STATUS_FAILED, "Failed"),
]

SEVERITY_LOW = "low"
SEVERITY_HIGH = "high"

SEVERITY_CHOICES = [
        (SEVERITY_LOW, "Low"),
        (SEVERITY_HIGH, "High"),
    ]