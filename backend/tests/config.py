"""Shared configuration and utilities for tests."""
from dataclasses import dataclass
from typing import Optional
import random


@dataclass
class RequestConfig:
    """Configuration for a single HTTP request to be made during a test."""
    url: str
    method: str = "POST"  # GET, POST, PUT, DELETE, etc.
    json_body: Optional[dict] = None
    headers: Optional[dict] = None
    timeout: float = 10.0


def generate_random_ip() -> str:
    """Generate a random IP address for testing."""
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"