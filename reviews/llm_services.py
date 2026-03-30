import json
from openai import OpenAI
from config import settings
from reviews.constants.fields import SOURCE_LLM
from reviews.models import ReviewComment
import google.generativeai as genai


class LLMReviewError(Exception):
    pass


def build_llm_prompt(review_request, parser_findings):
    filename = (review_request.filename or "input.jsx").strip()
    code = review_request.code or ""

    payload = {
        "filename": filename,
        "review_policy": {
            "frontend_scope": "React / React Native",
            "prefer_tailwind": True,
            "check_rerenders": True,
            "suggest_zustand_only_when_justified": True,
            "suggest_lazy_loading_only_when_justified": True,
        },
        "existing_parser_findings": parser_findings,
        "code": code,
    }

    return f"""
    You are an expert frontend code reviewer for React and React Native.

    Your job:
    - Review the submitted code.
    - Use the parser findings as prior signals.
    - Add only useful findings.
    - Do not duplicate parser findings unless you add materially new reasoning.
    - Prefer Tailwind over inline styles and custom CSS where applicable.
    - Flag rerender risks when justified.
    - Suggest Zustand only for clearly shared/global state.
    - Suggest lazy loading only when clearly justified.

    Return ONLY valid JSON.
    Return a JSON array.
    Each item must have exactly these fields:
    - rule_id
    - severity ("low", "medium", "high")
    - file
    - line
    - message
    - suggestion

    If there are no additional findings, return [].

    Input:
    {json.dumps(payload, indent=2)}
    """.strip()


def call_llm_for_review(review_request, parser_findings):
    if not settings.OPENAI_API_KEY:
        raise LLMReviewError("OPENAI_API_KEY not configured")

    # client = OpenAI(api_key=settings.OPENAI_API_KEY)
    # prompt = build_llm_prompt(
    #     review_request=review_request, parser_findings=parser_findings
    # )

    # genai.configure(api_key=settings.GEMINI_API_KEY)
    # model = genai.GenerativeModel(settings.GEMINI_MODEL)

    # # response = client.responses.create(model=settings.OPENAI_MODEL, input=prompt)
    # response = model.generate_content(
    #     prompt, generation_config={"response_mime_type": "application/json"}
    # )
    # print(f"response:{response}")
    # text = response.text.strip()

    # try:
    #     findings = json.loads(text)
    # except json.JSONDecodeError as exc:
    #     raise LLMReviewError(f"LLM returned invalid JSON: {text!r}") from exc

    findings = [
        {
            "rule_id": "missing-prop-types",
            "severity": "medium",
            "file": "usercard.jsx",
            "line": 3,
            "message": "The component's props are not validated. The 'user' prop is used without ensuring its shape, which can lead to runtime errors like `Cannot read properties of undefined (reading 'name')`.",
            "suggestion": "Add prop validation to enforce the component's contract. If using PropTypes, add: `import PropTypes from 'prop-types'; UserCard.propTypes = { user: PropTypes.shape({ name: PropTypes.string.isRequired }).isRequired };`. If using TypeScript, define an interface for the props.",
        },
        {
            "rule_id": "a11y-vague-action",
            "severity": "low",
            "file": "usercard.jsx",
            "line": 6,
            "message": 'The button text "Open" is ambiguous and lacks context for users of assistive technologies. It is not clear what will be opened.',
            "suggestion": 'Provide a more descriptive label for the button. You can either change the visible text to something like "View Profile" or add a more descriptive `aria-label`, for example: `aria-label={\\`View profile for \\${user.name}\\`}`.',
        },
        {
            "rule_id": "extract-inline-handler",
            "severity": "low",
            "file": "usercard.jsx",
            "line": 6,
            "message": "The `onClick` handler is defined inline. While acceptable for trivial logic, extracting it improves code readability and separation of concerns, especially if the logic were to become more complex.",
            "suggestion": "Define the event handler as a constant inside the component body and reference it in the JSX. For example: `const handleOpen = () => console.log(user.name);` and then use `<button onClick={handleOpen}>`.",
        },
    ]
    if not isinstance(findings, list):
        raise LLMReviewError(f"LLM response must be a json")

    return findings


def normalize_llm_finding(finding, review_request):
    filename = (review_request.filename or "input.jsx").strip() or "input.jsx"

    severity = str(finding.get("severity") or "low")
    if severity not in {"low", "medium", "high"}:
        severity = "low"

    line = finding.get("line")
    if not isinstance(line, int):
        line = None

    return {
        "source": SOURCE_LLM,
        "rule_id": str(finding.get("rule_id") or "llm-review"),
        "severity": severity,
        "file": str(finding.get("file") or filename),
        "line": line,
        "message": str(finding.get("message") or ""),
        "suggestion": str(finding.get("suggestion") or ""),
        "review_request": review_request,
    }


def save_llm_findings(review_request, llm_findings):
    comments = []

    for finding in llm_findings:
        item = normalize_llm_finding(finding, review_request)

        if not item["message"]:
            continue

        comments.append(
            ReviewComment(
                review_request=item["review_request"],
                source=item["source"],
                rule_id=item["rule_id"],
                severity=item["severity"],
                file=item["file"],
                line=item["line"],
                message=item["message"],
                suggestion=item["suggestion"],
            )
        )

    if not comments:
        return []

    return ReviewComment.objects.bulk_create(comments)


def run_llm_review(review_request, parser_findings):
    llm_findings = call_llm_for_review(review_request, parser_findings)
    return save_llm_findings(review_request, llm_findings)
