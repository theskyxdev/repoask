import re
import uuid
from pathlib import Path
from typing import List, Dict, Any
from app.models.schemas import SecurityVulnerability, SecurityScanReport

SECRET_PATTERNS = [
    (r"(?i)(?:api_key|apikey|secret_key|secret|token|password|auth_token)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]", "Hardcoded Secret / Token", "HIGH", "Sensitive credentials detected in plaintext source code."),
    (r"(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}", "Hardcoded Bearer Token", "CRITICAL", "Hardcoded authorization bearer token found."),
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI API Key Leak", "CRITICAL", "Valid pattern for OpenAI API secret key."),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key Leak", "CRITICAL", "AWS Access Key ID discovered."),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token", "CRITICAL", "GitHub personal access token found."),
    (r"(?i)jwt_secret\s*=\s*['\"](?:secret|password|123456|test|admin)['\"]", "Weak JWT Secret", "CRITICAL", "Trivial or guessable JWT signing secret."),
]

CODE_INJECTION_PATTERNS = [
    (r"(?i)\beval\s*\(", "Unsafe eval() Execution", "HIGH", "Dynamic code evaluation via eval() allows arbitrary code execution."),
    (r"(?i)\bexec\s*\(", "Unsafe exec() Execution", "HIGH", "Dynamic Python execution via exec() can compromise host runtime."),
    (r"(?i)dangerouslySetInnerHTML\s*=", "Potential Cross-Site Scripting (XSS)", "HIGH", "Directly rendering unescaped HTML can lead to XSS vulnerabilities."),
    (r"(?i)subprocess\.(?:Popen|call|run)\(.*shell\s*=\s*True", "Shell Command Injection", "CRITICAL", "Running shell commands with shell=True is susceptible to command injection."),
    (r"(?i)(?:execute|raw)\s*\(\s*f['\"].*?SELECT|INSERT|UPDATE|DELETE", "SQL Injection Vulnerability", "CRITICAL", "SQL query assembled via string interpolation rather than parameterized queries."),
    (r"(?i)(?:execute|raw)\s*\(\s*['\"].*?%s.*?['\"]\s*%", "Potential SQL Injection", "HIGH", "Old-style string formatting in SQL query execution."),
]

class SecurityScanner:
    @staticmethod
    def scan_repository(repo_id: str, repo_dir: Path, files: List[str]) -> SecurityScanReport:
        vulnerabilities: List[SecurityVulnerability] = []

        for rel_path in files:
            full_path = repo_dir / rel_path
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            lines = content.splitlines()

            # Scan Secrets
            for pattern, title, severity, desc in SECRET_PATTERNS:
                for line_idx, line in enumerate(lines, 1):
                    # Skip comment-only lines or test dummy files
                    stripped = line.strip()
                    if stripped.startswith(("#", "//", "/*", "*")) and "dummy" in stripped.lower():
                        continue
                    if re.search(pattern, line):
                        vulnerabilities.append(
                            SecurityVulnerability(
                                id=str(uuid.uuid4())[:8],
                                title=title,
                                severity=severity,
                                category="Hardcoded Secret",
                                file_path=rel_path,
                                line_number=line_idx,
                                snippet=stripped[:120],
                                description=desc,
                                remediation="Store sensitive credentials in environment variables or a secret vault (e.g. AWS Secrets Manager, Doppler) rather than source code."
                            )
                        )

            # Scan Code Injections
            for pattern, title, severity, desc in CODE_INJECTION_PATTERNS:
                for line_idx, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if re.search(pattern, line):
                        vulnerabilities.append(
                            SecurityVulnerability(
                                id=str(uuid.uuid4())[:8],
                                title=title,
                                severity=severity,
                                category="Insecure Coding Pattern",
                                file_path=rel_path,
                                line_number=line_idx,
                                snippet=stripped[:120],
                                description=desc,
                                remediation="Replace unsafe dynamic execution or raw string concatenation with parameterized interfaces and sanitization libraries."
                            )
                        )

        # Calculate security score (100 is best)
        crit_count = sum(1 for v in vulnerabilities if v.severity == "CRITICAL")
        high_count = sum(1 for v in vulnerabilities if v.severity == "HIGH")
        med_count = sum(1 for v in vulnerabilities if v.severity == "MEDIUM")
        low_count = sum(1 for v in vulnerabilities if v.severity == "LOW")

        deductions = (crit_count * 25) + (high_count * 15) + (med_count * 8) + (low_count * 3)
        score = max(0, min(100, 100 - deductions))

        summary = (
            f"Repository security scan completed with {len(vulnerabilities)} findings. "
            f"Detected {crit_count} Critical, {high_count} High, and {med_count} Medium issues."
            if vulnerabilities else "No high-severity vulnerabilities detected in indexed codebase. Security posture appears clean."
        )

        return SecurityScanReport(
            repo_id=repo_id,
            security_score=score,
            critical_count=crit_count,
            high_count=high_count,
            medium_count=med_count,
            low_count=low_count,
            vulnerabilities=vulnerabilities,
            summary=summary
        )

security_scanner = SecurityScanner()
