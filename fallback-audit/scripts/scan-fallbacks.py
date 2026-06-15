#!/usr/bin/env python3
"""Scan codebase for useless fallback patterns across multiple languages."""

import argparse
import fnmatch
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

EXTENSIONS = {
    "go": ["*.go"],
    "java": ["*.java"],
    "kotlin": ["*.kt", "*.kts"],
    "csharp": ["*.cs"],
    "typescript": ["*.ts", "*.tsx", "*.mts", "*.cts"],
    "python": ["*.py"],
    "rust": ["*.rs"],
}

PATTERNS: dict[str, list[dict]] = {
    "java": [
        {"code": "F001", "name": "bare-catch-all", "severity": "high", "regex": re.compile(
            r"""catch\s*\(\s*Exception\s+\w+\s*\)\s*\{[^}]*\breturn\s+(null|false|0\b|["']["']|Collections\.empty(List|Map|Set)\(\))"""
        )},
        {"code": "F002", "name": "silent-catch", "severity": "medium", "regex": re.compile(
            r"""catch\s*\(\s*(Exception|Throwable)\s+\w+\s*\)\s*\{\s*(\/\*.*?\*\/\s*)?\}"""
        )},
        {"code": "F003", "name": "optional-null-masking", "severity": "high", "regex": re.compile(
            r"""\.orElse\(\s*(null|["']\s*["']|false)\s*\)|\.orElse\(\s*0\s*\)"""
        )},
        {"code": "F005", "name": "empty-collection-catch", "severity": "high", "regex": re.compile(
            r"""catch\s*\([^)]*\)\s*\{[^}]*\breturn\s+new\s+(ArrayList|HashMap|HashSet|LinkedList|TreeMap|TreeSet)<>\(\)"""
        )},
        {"code": "F008", "name": "orelse-constant", "severity": "low", "regex": re.compile(
            r"""\.orElse\(\s*(?!(?:null|["']\s*["']|false|true|0)\s*\))[^)]+\)"""
        )},
    ],
    "kotlin": [
        {"code": "F003", "name": "null-masking", "severity": "high", "regex": re.compile(
            r"""\?\s*:\s*(null|false|emptyList\(\)|emptyMap\(\)|emptySet\(\)|["']["']|0[^.\w])"""
        )},
        {"code": "F001", "name": "bare-catch-all", "severity": "high", "regex": re.compile(
            r"""catch\s*\(\s*e?\s*:\s*Exception\s*\)\s*\{[^}]*\breturn\b"""
        )},
        {"code": "F002", "name": "silent-catch", "severity": "medium", "regex": re.compile(
            r"""catch\s*\(\s*\w+\s*:\s*(Exception|Throwable)\s*\)\s*\{\s*\}"""
        )},
        {"code": "F012", "name": "runCatching-getOrDefault", "severity": "medium", "regex": re.compile(
            r"""\.getOrDefault\([^)]*\)"""
        )},
    ],
    "csharp": [
        {"code": "F001", "name": "bare-catch-all", "severity": "high", "regex": re.compile(
            r"""catch\s*\(\s*(Exception|System\.Exception)\s*\w*\s*\)\s*\{[^}]*\breturn\b"""
        )},
        {"code": "F002", "name": "silent-catch", "severity": "medium", "regex": re.compile(
            r"""catch\s*\(\s*(Exception|System\.Exception)\s*\w*\s*\)\s*\{\s*\}"""
        )},
        {"code": "F005", "name": "empty-collection-fallback", "severity": "high", "regex": re.compile(
            r"""return\s+Enumerable\.Empty<|return\s+Array\.Empty<|return\s+new\s+List[^)]*\)\s*\(\s*\)|return\s+new\s+\[\]"""
        )},
        {"code": "F004", "name": "null-coalesce-chain", "severity": "medium", "regex": re.compile(
            r"""\?\s*\?\s+\w+(\.\w+)*\s*(\?\s*\?\s+\w+(\.\w+)*)+"""
        )},
    ],
    "typescript": [
        {"code": "F003", "name": "null-masking", "severity": "high", "regex": re.compile(
            r"""\?\?\s*["'][^"']*["']|\?\?\s*0\b|\?\?\s*\{\}|\?\?\s*\[\]"""
        )},
        {"code": "F004", "name": "fallback-chain", "severity": "medium", "regex": re.compile(
            r"""\?\?\s+\w+(\?\.\w+)*\s*\?\?"""
        )},
        {"code": "F001", "name": "catch-return-default", "severity": "high", "regex": re.compile(
            r"""catch\s*\(\s*\w+\s*\)\s*\{[^}]*\breturn\s+(null|undefined|\{.*?\}|\[\s*\]|["']["']|-1\b|false)"""
        )},
        {"code": "F002", "name": "silent-catch", "severity": "medium", "regex": re.compile(
            r"""catch\s*\(\s*\w+\s*\)\s*\{\s*\}"""
        )},
    ],
    "python": [
        {"code": "F010", "name": "except-pass", "severity": "high", "regex": re.compile(
            r"""except\s*(Exception)?\s*:\s*\n\s*pass\b"""
        )},
        {"code": "F001", "name": "bare-except-return-none", "severity": "high", "regex": re.compile(
            r"""except\s*(Exception)?\s*:\s*[^#\n]*\breturn\s+None"""
        )},
        {"code": "F002", "name": "silent-except", "severity": "high", "regex": re.compile(
            r"""except\s*(Exception)?\s*:\s*\n\s*#"""
        )},
        {"code": "F004", "name": "or-chain", "severity": "medium", "regex": re.compile(
            r"""\w+[\w.()\[\]"' ]*\s+or\s+\w+[\w.()\[\]"' ]*\s+or\s+\w+"""
        )},
        {"code": "F005", "name": "except-empty-list", "severity": "medium", "regex": re.compile(
            r"""except\s*(Exception)?\s*:\s*[^#\n]*\breturn\s+\[\]|\breturn\s+\{\}"""
        )},
        {"code": "F007", "name": "catch-log-continue", "severity": "medium", "regex": re.compile(
            r"""except\s+(Exception\s+as\s+\w+|:)\s*\n\s+\w+\s*=\s*.*\n\s+logger\.[a-z]+\(|except\s+.*:\s*\n\s+logger\.[a-z]+\([^)]*\)\s*\n(?!\s+raise)"""
        )},
        {"code": "F003", "name": "dict-get-default", "severity": "low", "regex": re.compile(
            r"""\.get\(\s*["'][^"']*["']\s*,\s*["'][^"']*["']\s*\)"""
        )},
    ],
    "rust": [
        {"code": "F009", "name": "unwrap-or-default", "severity": "high", "regex": re.compile(
            r"""\.unwrap_or\([^)]*\)"""
        )},
        {"code": "F009", "name": "unwrap-or-else-default", "severity": "high", "regex": re.compile(
            r"""\.unwrap_or_default\(\)"""
        )},
        {"code": "F012", "name": "catch-all-fallback", "severity": "medium", "regex": re.compile(
            r"""catch_all"""
        )},
        {"code": "F003", "name": "unwrap-or-constant", "severity": "medium", "regex": re.compile(
            r"""\.unwrap_or\(\s*(true|false|0\b|1\b|String::from\(["'])"""
        )},
    ],
    "go": [
        {"code": "F002", "name": "ignore-error", "severity": "high", "regex": re.compile(
            r"""\b_\s*=\s*\w+\("""
        )},
        {"code": "F005", "name": "return-nil-nil", "severity": "high", "regex": re.compile(
            r"""return\s+nil,\s*nil"""
        )},
        {"code": "F005", "name": "return-nil-error", "severity": "high", "regex": re.compile(
            r"""if\s+\w+\s*!=\s*nil\s*\{[^}]*\breturn\s+nil,\s*nil"""
        )},
        {"code": "F012", "name": "silent-recover", "severity": "medium", "regex": re.compile(
            r"""recover\(\)\s*\n"""
        )},
    ],
}


@dataclass
class Finding:
    code: str
    name: str
    severity: str
    file: str
    line: int
    column: int
    snippet: str
    language: str


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    errors: list[str] = field(default_factory=list)


def scan_file(filepath: str, language: str, patterns: list[dict]) -> list[Finding]:
    findings = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return []

    for p in patterns:
        for match in p["regex"].finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            col = match.start() - content.rfind("\n", 0, match.start())
            snippet = content[max(0, match.start() - 40) : match.end() + 40]
            snippet = snippet.replace("\n", "\\n").strip()
            if len(snippet) > 120:
                snippet = snippet[:60] + "..." + snippet[-60:]
            findings.append(Finding(
                code=p["code"],
                name=p["name"],
                severity=p["severity"],
                file=filepath,
                line=line_num,
                column=col,
                snippet=snippet,
                language=language,
            ))
    return findings


def scan_directory(directory: str, language: Optional[str] = None, verbose: bool = False) -> ScanResult:
    result = ScanResult()
    langs_to_scan = [language] if language else list(EXTENSIONS.keys())

    for lang in langs_to_scan:
        if lang not in PATTERNS:
            if verbose:
                print(f"  [warn] No patterns defined for language: {lang}", file=sys.stderr)
            continue
        patterns = PATTERNS[lang]
        exts = EXTENSIONS[lang]
        for root, _dirs, files in os.walk(directory):
            if ".git" in root or "node_modules" in root or "target" in root or ".venv" in root or "vendor" in root:
                continue
            for f in files:
                if any(fnmatch.fnmatch(f, ext) for ext in exts):
                    fpath = os.path.join(root, f)
                    result.files_scanned += 1
                    if verbose:
                        print(f"  Scanning: {fpath}", file=sys.stderr)
                    result.findings.extend(scan_file(fpath, lang, patterns))

    return result


def print_summary(result: ScanResult, verbose: bool = False):
    if not result.findings:
        print("No fallback patterns found.")
        return

    by_severity = {"high": [], "medium": [], "low": []}
    for f in result.findings:
        by_severity.setdefault(f.severity, []).append(f)

    print(f"Files scanned: {result.files_scanned}")
    print(f"Total findings: {len(result.findings)}")
    print()

    for severity in ["high", "medium", "low"]:
        items = by_severity.get(severity, [])
        if not items:
            continue
        print(f"=== {severity.upper()} ({len(items)} findings) ===")
        for f in items:
            print(f"  [{f.code}] {f.name} — {f.file}:{f.line}:{f.column}")
            print(f"         {f.snippet}")
        print()

    print(f"High: {len(by_severity.get('high', []))}  "
          f"Medium: {len(by_severity.get('medium', []))}  "
          f"Low: {len(by_severity.get('low', []))}")


def serialize_finding(f: Finding) -> dict:
    d = asdict(f)
    return d


def main():
    parser = argparse.ArgumentParser(description="Scan for useless fallback patterns")
    parser.add_argument("--dir", default=".", help="Directory to scan")
    parser.add_argument("--lang", choices=list(EXTENSIONS.keys()), help="Language to scan (default: all)")
    parser.add_argument("--json", help="Output JSON report to file")
    parser.add_argument("--verbose", action="store_true", help="Show per-file scan progress")
    args = parser.parse_args()

    result = scan_directory(args.dir, args.lang, args.verbose)

    if args.json:
        report = {
            "summary": {
                "files_scanned": result.files_scanned,
                "total_findings": len(result.findings),
                "by_severity": {
                    "high": sum(1 for f in result.findings if f.severity == "high"),
                    "medium": sum(1 for f in result.findings if f.severity == "medium"),
                    "low": sum(1 for f in result.findings if f.severity == "low"),
                },
                "patterns": args.lang or "all",
            },
            "findings": [serialize_finding(f) for f in result.findings],
        }
        with open(args.json, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {args.json}")
    else:
        print_summary(result, args.verbose)

    return 1 if result.findings else 0


if __name__ == "__main__":
    sys.exit(main())
