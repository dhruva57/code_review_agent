const fs = require("fs");
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;

function parseCode(code, filename = "input.jsx") {
  const isTypeScript = filename.endsWith(".ts") || filename.endsWith(".tsx");
  const plugins = [
    "jsx",
    ...(isTypeScript ? ["typescript"] : []),
  ];

  return parser.parse(code, {
    sourceType: "module",
    plugins,
    errorRecovery: true,
  });
}

function analyzeAst(ast, filename = "input.jsx") {
  const findings = [];

  traverse(ast, {
    JSXAttribute(path) {
      const attrName = path.node.name && path.node.name.name;

      if (!attrName) return;

      // Rule 1: inline style={{ ... }}
      if (
        attrName === "style" &&
        path.node.value &&
        path.node.value.type === "JSXExpressionContainer" &&
        path.node.value.expression &&
        path.node.value.expression.type === "ObjectExpression"
      ) {
        findings.push({
          rule_id: "non-tailwind-styling",
          severity: "medium",
          confidence: "high",
          file: filename,
          line: path.node.loc?.start?.line || null,
          message: "Inline style object found. Project policy prefers Tailwind utilities.",
          suggestion: "Replace inline style objects with Tailwind utility classes where possible.",
        });
      }

      // Rule 2: inline callback in JSX prop
      if (
        path.node.value &&
        path.node.value.type === "JSXExpressionContainer" &&
        path.node.value.expression &&
        (
          path.node.value.expression.type === "ArrowFunctionExpression" ||
          path.node.value.expression.type === "FunctionExpression"
        )
      ) {
        findings.push({
          rule_id: "react-rerender-risk",
          severity: "medium",
          confidence: "high",
          file: filename,
          line: path.node.loc?.start?.line || null,
          message: `Inline function passed to JSX prop '${attrName}'. This may contribute to avoidable rerenders.`,
          suggestion: "Extract the handler or memoize it where rerender stability matters.",
        });
      }
    },

    ImportDeclaration(path) {
      const importSource = path.node.source && path.node.source.value;

      if (
        typeof importSource === "string" &&
        (importSource.endsWith(".css") || importSource.endsWith(".scss"))
      ) {
        findings.push({
          rule_id: "custom-styles-import",
          severity: "medium",
          confidence: "high",
          file: filename,
          line: path.node.loc?.start?.line || null,
          message: "CSS/SCSS import detected. Project policy prefers Tailwind-first styling.",
          suggestion: "Use Tailwind utility classes unless there is a strong reason for custom stylesheet imports.",
        });
      }
    },
  });

  return findings;
}

function main() {
  const filename = process.argv[2] || "input.jsx";
  const code = fs.readFileSync(0, "utf8");

  try {
    const ast = parseCode(code, filename);
    const findings = analyzeAst(ast, filename);
    process.stdout.write(JSON.stringify({ ok: true, findings }, null, 2));
  } catch (error) {
    process.stdout.write(
      JSON.stringify(
        {
          ok: false,
          error: error.message,
        },
        null,
        2
      )
    );
    process.exit(1);
  }
}

main();