from reviews.models import ReviewComment


def run_manual_review(review_request):
    code = review_request.code or ""
    filename = review_request.filename or ""

    findings = []

    if "style={{" in code:
        findings.append(
            {
                "rule_id": "non-tailwind-styling",
                "severity": "medium",
                "file": filename,
                "line": None,
                "message": "Inline style usage found. Project policy prefers Tailwind utilities over inline styles.",
                "suggestion": "Replace inline style objects with Tailwind utility classes where possible.",
            }
        )

    if ".css" in code or ".scss" in code:
        findings.append(
            {
                "rule_id": "custom-styles-import",
                "severity": "medium",
                "file": filename,
                "line": None,
                "message": "Custom stylesheet import detected. Project policy prefers Tailwind-first styling.",
                "suggestion": "Use Tailwind utility classes unless there is a strong reason not to.",
            }
        )

    if "useState(" in code and "props." in code:
        findings.append(
            {
                "rule_id": "possible-zustand-opportunity",
                "severity": "low",
                "file": filename,
                "line": None,
                "message": "Local state + prop usage may indicate prop drilling or duplicated state.",
                "suggestion": "Check whether this state is shared across components and should move to Zustand.",
            }
        )

    if "onClick={() =>" in code or "renderItem={({ item }) =>" in code:
        findings.append(
            {
                "rule_id": "react-rerender-risk",
                "severity": "medium",
                "file": filename,
                "line": None,
                "message": "Inline function detected inside JSX. This can contribute to avoidable rerenders.",
                "suggestion": "Consider extracting the handler or memoizing where it matters.",
            }
        )

    if "import " in code and " from " in code and "lazy(" not in code:
        findings.append(
            {
                "rule_id": "missing-lazy-load-check",
                "severity": "low",
                "file": filename,
                "line": None,
                "message": "Static imports found. Some components may be candidates for lazy loading.",
                "suggestion": "Review route-level or heavy conditional components for React.lazy usage.",
            }
        )

    if not findings:
        findings.append(
            {
                "rule_id": "no-issues-detected-yet",
                "severity": "low",
                "file": filename,
                "line": None,
                "message": "No basic heuristic issues detected in the current manual review pass.",
                "suggestion": "Next step is to replace these heuristics with AST-based checks.",
            }
        )

    comment_instances = []
    for finding in findings:
        comment_instances.append(
            ReviewComment(
                review_request=review_request,
                rule_id=finding["rule_id"],
                severity=finding["severity"],
                file=finding["file"],
                line=finding["line"],
                message=finding["message"],
                suggestion=finding["suggestion"],
            )
        )

    return ReviewComment.objects.bulk_create(comment_instances)
