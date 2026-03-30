import json
import subprocess

from reviews.constants.constants import NODE_ANALYZER_DIR, NODE_ANALYZER_SCRIPT
from reviews.constants.fields import SOURCE_PARSER
from reviews.models import ReviewComment


class NodeAnalyzerError(Exception):
    pass


def detect_parser_filename(review_request):
    filename = (review_request.filename or "").strip()

    return filename if filename else "input.jsx"


def run_node_analyzer(code, filename):
    if not NODE_ANALYZER_SCRIPT.exists():
        raise NodeAnalyzerError(
            f"node analyzer script not found: {NODE_ANALYZER_SCRIPT}"
        )

    try:
        completed = subprocess.run(
            ["node", str(NODE_ANALYZER_SCRIPT), filename],
            input=code,
            capture_output=True,
            text=True,
            cwd=str(NODE_ANALYZER_DIR),
            check=False,
            timeout=15,
        )
    except FileNotFoundError as exc:
        raise NodeAnalyzerError(
            "Node.js is not installed or not available on PATH"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise NodeAnalyzerError("Node analyzer timed out.") from exc

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()

    if completed.returncode != 0:
        raise NodeAnalyzerError(
            f"Node analyzer failed with exit code {completed.returncode}. "
            f"stdout={stdout!r} stderr={stderr!r}"
        )

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise NodeAnalyzerError(
            f"Node analyzer returned invalid JSON. stdout={stdout!r} stderr={stderr!r}"
        ) from exc

    if not isinstance(payload, dict):
        raise NodeAnalyzerError("node analyzer response must be JSON object")

    if not payload.get("ok"):
        raise NodeAnalyzerError(payload.get("error", "node analyzer returned ok=false"))

    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        raise NodeAnalyzerError("findings must be a list")

    return findings


def normalise_finding(finding, review_request, filename):
    return {
        "rule_id": str(finding.get("rule_id") or "unknown-rule"),
        "source": SOURCE_PARSER,
        "severity": str(finding.get("severity") or "low"),
        "file": str(finding.get("file") or filename),
        "line": finding.get("line"),
        "message": str(finding.get("message") or ""),
        "suggestion": str(finding.get("suggestion") or ""),
        "review_request": review_request,
    }


def save_parser_findings(review_request, findings, filename):
    comments = [
        ReviewComment(
            review_request=item["review_request"],
            source=SOURCE_PARSER,
            rule_id=item["rule_id"],
            severity=item["severity"],
            file=item["file"],
            line=item["line"],
            message=item["message"],
            suggestion=item["suggestion"],
        )
        for item in (
            normalise_finding(finding, review_request, filename) for finding in findings
        )
    ]

    if not comments:
        comments = [
            ReviewComment(
                review_request=review_request,
                rule_id="no-issues-detected-yet",
                source=SOURCE_PARSER,
                severity="low",
                file=filename,
                line=None,
                message="No parser-based issues detected in the current pass.",
                suggestion="Add more parser rules or proceed to LLM-based review.",
            )
        ]

    return ReviewComment.objects.bulk_create(comments)


def run_parser_review(review_request):
    filename = detect_parser_filename(review_request)
    code = review_request.code or ""

    review_request.comments.all().delete()

    parser_findings = run_node_analyzer(code=code, filename=filename)
    save_parser_findings(
        review_request=review_request, findings=parser_findings, filename=filename
    )
    return parser_findings


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
