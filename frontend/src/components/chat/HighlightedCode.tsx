import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash";
import css from "react-syntax-highlighter/dist/esm/languages/prism/css";
import java from "react-syntax-highlighter/dist/esm/languages/prism/java";
import javascript from "react-syntax-highlighter/dist/esm/languages/prism/javascript";
import json from "react-syntax-highlighter/dist/esm/languages/prism/json";
import jsx from "react-syntax-highlighter/dist/esm/languages/prism/jsx";
import markup from "react-syntax-highlighter/dist/esm/languages/prism/markup";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import sql from "react-syntax-highlighter/dist/esm/languages/prism/sql";
import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx";
import typescript from "react-syntax-highlighter/dist/esm/languages/prism/typescript";
import yaml from "react-syntax-highlighter/dist/esm/languages/prism/yaml";

const LANGUAGES = {
  bash,
  css,
  java,
  javascript,
  json,
  jsx,
  markup,
  python,
  sql,
  tsx,
  typescript,
  yaml,
};

for (const [name, grammar] of Object.entries(LANGUAGES)) {
  SyntaxHighlighter.registerLanguage(name, grammar);
}

const ALIASES: Record<string, string> = {
  sh: "bash",
  shell: "bash",
  zsh: "bash",
  js: "javascript",
  ts: "typescript",
  py: "python",
  yml: "yaml",
  html: "markup",
  xml: "markup",
};

type HighlightedCodeProps = {
  code: string;
  language: string;
};

export default function HighlightedCode({ code, language }: HighlightedCodeProps) {
  const lang = language.toLowerCase();

  return (
    <SyntaxHighlighter
      style={oneDark}
      language={ALIASES[lang] ?? lang}
      PreTag="div"
      customStyle={{
        margin: 0,
        borderRadius: 0,
        background: "transparent",
        padding: "16px",
      }}
    >
      {code}
    </SyntaxHighlighter>
  );
}
