"""PII stripping module for detecting and redacting sensitive information.

Provides regex-based detection with optional Presidio NLP enhancement
for better entity recognition.  Zero-dependency operation by default.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SSN_PATTERN = re.compile(r"\b(?!000|666|9\d{2})\d{3}[- ]?\d{2}[- ]?\d{4}\b")
PHONE_PATTERN = re.compile(r"(?:\(\d{3}\)\s*|\d{3}[-.]?)\d{3}[-.]?\d{4}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

_PII_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("ssn", SSN_PATTERN, "[REDACTED]"),
    ("email", EMAIL_PATTERN, "[REDACTED]"),
    ("phone", PHONE_PATTERN, "[REDACTED]"),
    ("credit_card", CREDIT_CARD_PATTERN, "[REDACTED]"),
    ("name", re.compile(r"\b(?:[A-Z][a-z]+\s+(?:[A-Z][a-z]+\s*)?[A-Z][a-z]+)\b"), "[REDACTED]"),
    ("dob", re.compile(r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b"), "[REDACTED]"),
    ("ip_address", IP_PATTERN, "[REDACTED]"),
]


@dataclass
class PIIEntity:
    entity_type: str
    start: int
    end: int
    original_text: str
    replacement: str = "[REDACTED]"


@dataclass
class PIIPattern:
    name: str
    pattern: re.Pattern[str]
    enabled: bool = True
    replacement: str = "[REDACTED]"


class PIIStripper:
    """Detects and redacts PII from text using configurable regex patterns.

    Optionally uses Microsoft Presidio for NLP-based entity detection when
    the presidio_analyzer and presidio_anonymizer packages are installed.
    """

    def __init__(
        self,
        *,
        enable_ssn: bool = True,
        enable_email: bool = True,
        enable_phone: bool = True,
        enable_credit_card: bool = True,
        enable_name: bool = True,
        enable_dob: bool = True,
        enable_ip: bool = True,
        replacement: str = "[REDACTED]",
        use_presidio: bool = False,
    ):
        self.patterns: list[PIIPattern] = [
            PIIPattern(
                name="ssn",
                pattern=SSN_PATTERN,
                enabled=enable_ssn,
                replacement=replacement,
            ),
            PIIPattern(
                name="email",
                pattern=EMAIL_PATTERN,
                enabled=enable_email,
                replacement=replacement,
            ),
            PIIPattern(
                name="phone",
                pattern=PHONE_PATTERN,
                enabled=enable_phone,
                replacement=replacement,
            ),
            PIIPattern(
                name="credit_card",
                pattern=CREDIT_CARD_PATTERN,
                enabled=enable_credit_card,
                replacement=replacement,
            ),
            PIIPattern(
                name="name",
                pattern=re.compile(
                    r"\b(?:[A-Z][a-z]+\s+(?:[A-Z][a-z]+\s*)?[A-Z][a-z]+)\b"
                ),
                enabled=enable_name,
                replacement=replacement,
            ),
            PIIPattern(
                name="dob",
                pattern=re.compile(
                    r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b"
                ),
                enabled=enable_dob,
                replacement=replacement,
            ),
            PIIPattern(
                name="ip_address",
                pattern=IP_PATTERN,
                enabled=enable_ip,
                replacement=replacement,
            ),
        ]
        self._use_presidio = use_presidio
        self._replacement = replacement

    def strip(self, text: str) -> str:
        """Replace all enabled PII patterns in text with their replacement strings."""
        for p in self.patterns:
            if p.enabled:
                text = p.pattern.sub(p.replacement, text)
        return text

    def strip_with_report(self, text: str) -> tuple[str, list[str]]:
        """Strip PII and return (redacted_text, list_of_redacted_types).

        The list contains the PII type names that were actually redacted,
        not the original values.
        """
        redacted_types: list[str] = []
        for p in self.patterns:
            if p.enabled and p.pattern.search(text):
                redacted_types.append(p.name)
                text = p.pattern.sub(p.replacement, text)
        return text, redacted_types

    def strip_with_entities(self, text: str) -> tuple[str, list[PIIEntity]]:
        """Strip PII and return (redacted_text, list_of_PIIEntity).

        Each PIIEntity includes the entity_type, character offsets (start/end),
        the original text that was matched, and the replacement applied.
        """
        entities: list[PIIEntity] = []

        for p in self.patterns:
            if not p.enabled:
                continue
            for match in p.pattern.finditer(text):
                original = match.group()
                entities.append(PIIEntity(
                    entity_type=p.name,
                    start=match.start(),
                    end=match.end(),
                    original_text=original,
                    replacement=p.replacement,
                ))

        redacted = text
        for p in self.patterns:
            if p.enabled:
                redacted = p.pattern.sub(p.replacement, redacted)

        if self._use_presidio:
            presidio_entities = self._presidio_detect(text)
            entities.extend(presidio_entities)

        return redacted, entities

    def _presidio_detect(self, text: str) -> list[PIIEntity]:
        """Optionally detect PII using Presidio NLP for better entity recognition.

        Requires presidio_analyzer and presidio_anonymizer packages.
        Returns empty list if packages are not installed.
        """
        try:
            from presidio_analyzer import AnalyzerEngine

            analyzer = AnalyzerEngine()
            results = analyzer.analyze(text=text, language="en")

            entities: list[PIIEntity] = []
            for result in results:
                entities.append(PIIEntity(
                    entity_type=result.entity_type,
                    start=result.start,
                    end=result.end,
                    original_text=text[result.start:result.end],
                    replacement=self._replacement,
                ))
            return entities
        except ImportError:
            logger.debug("Presidio not installed — skipping NLP-based PII detection")
            return []

    def strip_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively strip PII from all string values in a dict."""
        return self._strip_value(data)

    def _strip_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.strip(value)
        if isinstance(value, dict):
            return {k: self._strip_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._strip_value(item) for item in value]
        return value


def strip_pii_from_prompt(prompt: str) -> tuple[str, list[str]]:
    """Standalone function to strip PII from an LLM prompt.

    Returns:
        (stripped_text, list_of_redacted_types) — types are strings like
        "ssn", "email", etc., never the original PII values.
    """
    stripper = PIIStripper()
    return stripper.strip_with_report(prompt)
