"""
Security middleware for DefinitieAgent request validation pipeline.
Provides comprehensive request validation, threat detection, and security monitoring.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import json
from pathlib import Path
import hashlib
import re
from urllib.parse import urlparse

from validation.input_validator import get_validator, ValidationSeverity
from validation.sanitizer import get_sanitizer, SanitizationLevel, ContentType

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security validation levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of security threats."""
    XSS = "xss"
    SQL_INJECTION = "sql_injection"
    CSRF = "csrf"
    MALICIOUS_FILE = "malicious_file"
    BRUTE_FORCE = "brute_force"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfiltration"


@dataclass
class SecurityEvent:
    """Security event record."""
    timestamp: datetime
    event_type: ThreatType
    severity: SecurityLevel
    source_ip: str
    user_agent: str
    endpoint: str
    threat_data: Dict[str, Any]
    blocked: bool
    description: str


@dataclass
class ValidationRequest:
    """Request data for security validation."""
    endpoint: str
    method: str
    data: Dict[str, Any]
    headers: Dict[str, str]
    source_ip: str
    user_agent: str
    timestamp: datetime
    session_id: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class ValidationResponse:
    """Response from security validation."""
    allowed: bool
    sanitized_data: Dict[str, Any]
    threats_detected: List[ThreatType]
    security_events: List[SecurityEvent]
    sanitization_changes: List[str]
    validation_errors: List[str]
    response_headers: Dict[str, str]


class SecurityMiddleware:
    """Main security middleware for request validation."""
    
    def __init__(self):
        self.validator = get_validator()
        self.sanitizer = get_sanitizer()
        self.security_events: List[SecurityEvent] = []
        self.request_tracking: Dict[str, List[datetime]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.rate_limits = self._load_rate_limits()
        
    def _load_suspicious_patterns(self) -> List[Dict[str, str]]:
        """Load suspicious patterns for threat detection."""
        return [
            {
                "pattern": r"<script[^>]*>.*?</script>",
                "threat_type": ThreatType.XSS.value,
                "description": "JavaScript injection attempt"
            },
            {
                "pattern": r"(union|select|insert|update|delete|drop)\s+",
                "threat_type": ThreatType.SQL_INJECTION.value,
                "description": "SQL injection attempt"
            },
            {
                "pattern": r"\.\.[\\/]",
                "threat_type": ThreatType.MALICIOUS_FILE.value,
                "description": "Path traversal attempt"
            },
            {
                "pattern": r"(eval|exec|system|cmd)\s*\(",
                "threat_type": ThreatType.SUSPICIOUS_PATTERN.value,
                "description": "Command execution attempt"
            },
            {
                "pattern": r"document\.cookie|window\.location",
                "threat_type": ThreatType.XSS.value,
                "description": "Browser object manipulation"
            },
            {
                "pattern": r"data:.*base64",
                "threat_type": ThreatType.DATA_EXFILTRATION.value,
                "description": "Base64 data URI detected"
            }
        ]
    
    def _load_rate_limits(self) -> Dict[str, Dict[str, int]]:
        """Load rate limit configurations."""
        return {
            "default": {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "burst_limit": 10
            },
            "definition_generation": {
                "requests_per_minute": 10,
                "requests_per_hour": 100,
                "burst_limit": 3
            },
            "admin": {
                "requests_per_minute": 100,
                "requests_per_hour": 5000,
                "burst_limit": 20
            }
        }
    
    async def validate_request(self, request: ValidationRequest) -> ValidationResponse:
        """Validate incoming request for security threats."""
        threats_detected = []
        security_events = []
        sanitized_data = request.data.copy()
        sanitization_changes = []
        validation_errors = []
        response_headers = {}
        
        try:
            # Step 1: Check if IP is blocked
            if self._is_ip_blocked(request.source_ip):
                event = SecurityEvent(
                    timestamp=datetime.now(),
                    event_type=ThreatType.UNAUTHORIZED_ACCESS,
                    severity=SecurityLevel.HIGH,
                    source_ip=request.source_ip,
                    user_agent=request.user_agent,
                    endpoint=request.endpoint,
                    threat_data={"reason": "IP blocked"},
                    blocked=True,
                    description="Request from blocked IP address"
                )
                security_events.append(event)
                threats_detected.append(ThreatType.UNAUTHORIZED_ACCESS)
                
                return ValidationResponse(
                    allowed=False,
                    sanitized_data={},
                    threats_detected=threats_detected,
                    security_events=security_events,
                    sanitization_changes=[],
                    validation_errors=["IP address is blocked"],
                    response_headers={"X-Security-Status": "blocked"}
                )
            
            # Step 2: Rate limiting check
            if not self._check_rate_limit(request):
                event = SecurityEvent(
                    timestamp=datetime.now(),
                    event_type=ThreatType.RATE_LIMIT_EXCEEDED,
                    severity=SecurityLevel.MEDIUM,
                    source_ip=request.source_ip,
                    user_agent=request.user_agent,
                    endpoint=request.endpoint,
                    threat_data={"rate_limit_type": "requests_per_minute"},
                    blocked=True,
                    description="Rate limit exceeded"
                )
                security_events.append(event)
                threats_detected.append(ThreatType.RATE_LIMIT_EXCEEDED)
                
                return ValidationResponse(
                    allowed=False,
                    sanitized_data={},
                    threats_detected=threats_detected,
                    security_events=security_events,
                    sanitization_changes=[],
                    validation_errors=["Rate limit exceeded"],
                    response_headers={"X-RateLimit-Remaining": "0"}
                )
            
            # Step 3: Threat detection
            detected_threats = self._detect_threats(request)
            for threat in detected_threats:
                threats_detected.append(threat['type'])
                
                event = SecurityEvent(
                    timestamp=datetime.now(),
                    event_type=threat['type'],
                    severity=threat['severity'],
                    source_ip=request.source_ip,
                    user_agent=request.user_agent,
                    endpoint=request.endpoint,
                    threat_data=threat['data'],
                    blocked=threat['severity'] in [SecurityLevel.HIGH, SecurityLevel.CRITICAL],
                    description=threat['description']
                )
                security_events.append(event)
                
                # Block high severity threats
                if threat['severity'] in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                    self._block_ip_temporarily(request.source_ip)
                    
                    return ValidationResponse(
                        allowed=False,
                        sanitized_data={},
                        threats_detected=threats_detected,
                        security_events=security_events,
                        sanitization_changes=[],
                        validation_errors=[f"Security threat detected: {threat['description']}"],
                        response_headers={"X-Security-Status": "threat_detected"}
                    )
            
            # Step 4: Input validation
            schema_name = self._get_validation_schema(request.endpoint)
            if schema_name:
                validation_results = self.validator.validate(request.data, schema_name)
                
                for result in validation_results:
                    if not result.passed and result.severity == ValidationSeverity.ERROR:
                        validation_errors.append(f"{result.field_name}: {result.message}")
                
                # If validation errors are critical, block request
                if validation_errors and len(validation_errors) > 5:
                    event = SecurityEvent(
                        timestamp=datetime.now(),
                        event_type=ThreatType.SUSPICIOUS_PATTERN,
                        severity=SecurityLevel.MEDIUM,
                        source_ip=request.source_ip,
                        user_agent=request.user_agent,
                        endpoint=request.endpoint,
                        threat_data={"validation_errors": validation_errors},
                        blocked=True,
                        description="Multiple validation errors detected"
                    )
                    security_events.append(event)
                    threats_detected.append(ThreatType.SUSPICIOUS_PATTERN)
                    
                    return ValidationResponse(
                        allowed=False,
                        sanitized_data={},
                        threats_detected=threats_detected,
                        security_events=security_events,
                        sanitization_changes=[],
                        validation_errors=validation_errors,
                        response_headers={"X-Validation-Status": "failed"}
                    )
            
            # Step 5: Data sanitization
            sanitized_data = self.sanitizer.sanitize_user_input(request.data)
            
            # Track sanitization changes
            for key, original_value in request.data.items():
                if key in sanitized_data and sanitized_data[key] != original_value:
                    sanitization_changes.append(f"Sanitized field: {key}")
            
            # Step 6: Set security headers
            response_headers.update({
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'",
                "X-Security-Status": "validated"
            })
            
            # Record successful validation
            self._record_request(request.source_ip)
            
            return ValidationResponse(
                allowed=True,
                sanitized_data=sanitized_data,
                threats_detected=threats_detected,
                security_events=security_events,
                sanitization_changes=sanitization_changes,
                validation_errors=validation_errors,
                response_headers=response_headers
            )
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            
            # Log security validation failure
            event = SecurityEvent(
                timestamp=datetime.now(),
                event_type=ThreatType.SUSPICIOUS_PATTERN,
                severity=SecurityLevel.CRITICAL,
                source_ip=request.source_ip,
                user_agent=request.user_agent,
                endpoint=request.endpoint,
                threat_data={"error": str(e)},
                blocked=True,
                description=f"Security validation failed: {str(e)}"
            )
            security_events.append(event)
            
            return ValidationResponse(
                allowed=False,
                sanitized_data={},
                threats_detected=[ThreatType.SUSPICIOUS_PATTERN],
                security_events=security_events,
                sanitization_changes=[],
                validation_errors=[f"Security validation failed: {str(e)}"],
                response_headers={"X-Security-Status": "error"}
            )
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP address is blocked."""
        if ip in self.blocked_ips:
            block_time = self.blocked_ips[ip]
            if datetime.now() - block_time < timedelta(hours=1):  # 1 hour block
                return True
            else:
                # Remove expired block
                del self.blocked_ips[ip]
        return False
    
    def _block_ip_temporarily(self, ip: str):
        """Block IP address temporarily."""
        self.blocked_ips[ip] = datetime.now()
        logger.warning(f"IP {ip} temporarily blocked due to security threat")
    
    def _check_rate_limit(self, request: ValidationRequest) -> bool:
        """Check if request is within rate limits."""
        ip = request.source_ip
        current_time = datetime.now()
        
        # Get rate limit config for endpoint
        endpoint_config = self.rate_limits.get(request.endpoint, self.rate_limits["default"])
        
        # Initialize tracking for IP if not exists
        if ip not in self.request_tracking:
            self.request_tracking[ip] = []
        
        # Clean old requests (older than 1 hour)
        cutoff_time = current_time - timedelta(hours=1)
        self.request_tracking[ip] = [
            req_time for req_time in self.request_tracking[ip]
            if req_time > cutoff_time
        ]
        
        # Check hourly limit
        hourly_requests = len(self.request_tracking[ip])
        if hourly_requests >= endpoint_config["requests_per_hour"]:
            return False
        
        # Check minute limit
        minute_cutoff = current_time - timedelta(minutes=1)
        minute_requests = len([
            req_time for req_time in self.request_tracking[ip]
            if req_time > minute_cutoff
        ])
        if minute_requests >= endpoint_config["requests_per_minute"]:
            return False
        
        # Check burst limit (last 10 seconds)
        burst_cutoff = current_time - timedelta(seconds=10)
        burst_requests = len([
            req_time for req_time in self.request_tracking[ip]
            if req_time > burst_cutoff
        ])
        if burst_requests >= endpoint_config["burst_limit"]:
            return False
        
        return True
    
    def _record_request(self, ip: str):
        """Record a successful request."""
        if ip not in self.request_tracking:
            self.request_tracking[ip] = []
        self.request_tracking[ip].append(datetime.now())
    
    def _detect_threats(self, request: ValidationRequest) -> List[Dict[str, Any]]:
        """Detect security threats in request."""
        threats = []
        
        # Check all data fields for suspicious patterns
        for field_name, field_value in request.data.items():
            if isinstance(field_value, str):
                for pattern_config in self.suspicious_patterns:
                    if re.search(pattern_config["pattern"], field_value, re.IGNORECASE):
                        threats.append({
                            "type": ThreatType(pattern_config["threat_type"]),
                            "severity": SecurityLevel.HIGH,
                            "description": pattern_config["description"],
                            "data": {
                                "field": field_name,
                                "pattern": pattern_config["pattern"],
                                "matched_value": field_value[:100]  # Limit logged data
                            }
                        })
        
        # Check headers for suspicious patterns
        for header_name, header_value in request.headers.items():
            if isinstance(header_value, str):
                for pattern_config in self.suspicious_patterns:
                    if re.search(pattern_config["pattern"], header_value, re.IGNORECASE):
                        threats.append({
                            "type": ThreatType(pattern_config["threat_type"]),
                            "severity": SecurityLevel.MEDIUM,
                            "description": f"Suspicious header: {pattern_config['description']}",
                            "data": {
                                "header": header_name,
                                "pattern": pattern_config["pattern"],
                                "matched_value": header_value[:100]
                            }
                        })
        
        # Check for brute force patterns
        if self._is_brute_force_attempt(request):
            threats.append({
                "type": ThreatType.BRUTE_FORCE,
                "severity": SecurityLevel.HIGH,
                "description": "Potential brute force attack detected",
                "data": {
                    "source_ip": request.source_ip,
                    "endpoint": request.endpoint,
                    "user_agent": request.user_agent
                }
            })
        
        return threats
    
    def _is_brute_force_attempt(self, request: ValidationRequest) -> bool:
        """Detect potential brute force attempts."""
        ip = request.source_ip
        
        if ip not in self.request_tracking:
            return False
        
        # Check for rapid successive requests
        current_time = datetime.now()
        recent_requests = [
            req_time for req_time in self.request_tracking[ip]
            if current_time - req_time < timedelta(minutes=1)
        ]
        
        # If more than 30 requests in 1 minute, consider it brute force
        return len(recent_requests) > 30
    
    def _get_validation_schema(self, endpoint: str) -> Optional[str]:
        """Get validation schema name for endpoint."""
        schema_mapping = {
            "definition_generation": "definition_generation",
            "user_input": "user_input",
            "context_validation": "context_validation"
        }
        return schema_mapping.get(endpoint)
    
    def get_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        current_time = datetime.now()
        
        # Filter recent events (last 24 hours)
        recent_events = [
            event for event in self.security_events
            if current_time - event.timestamp < timedelta(hours=24)
        ]
        
        # Group events by type
        threat_counts = {}
        for event in recent_events:
            threat_type = event.event_type.value
            threat_counts[threat_type] = threat_counts.get(threat_type, 0) + 1
        
        # Calculate statistics
        total_events = len(recent_events)
        blocked_events = len([e for e in recent_events if e.blocked])
        
        # Top threat sources
        ip_counts = {}
        for event in recent_events:
            ip = event.source_ip
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
        
        top_threat_sources = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "generated_at": current_time.isoformat(),
            "period": "24 hours",
            "total_security_events": total_events,
            "blocked_requests": blocked_events,
            "block_rate": blocked_events / total_events if total_events > 0 else 0,
            "threat_types": threat_counts,
            "top_threat_sources": top_threat_sources,
            "currently_blocked_ips": len(self.blocked_ips),
            "most_common_threats": sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def export_security_log(self, filename: Optional[str] = None) -> str:
        """Export security log to file."""
        if filename is None:
            filename = f"security_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = Path("logs") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        # Serialize events
        events_data = []
        for event in self.security_events:
            events_data.append({
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "source_ip": event.source_ip,
                "user_agent": event.user_agent,
                "endpoint": event.endpoint,
                "threat_data": event.threat_data,
                "blocked": event.blocked,
                "description": event.description
            })
        
        log_data = {
            "generated_at": datetime.now().isoformat(),
            "total_events": len(events_data),
            "report": self.get_security_report(),
            "events": events_data
        }
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)


# Global security middleware instance
_security_middleware: Optional[SecurityMiddleware] = None


def get_security_middleware() -> SecurityMiddleware:
    """Get or create global security middleware instance."""
    global _security_middleware
    if _security_middleware is None:
        _security_middleware = SecurityMiddleware()
    return _security_middleware


def security_middleware_decorator(endpoint_name: str = ""):
    """Decorator to apply security middleware to functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            middleware = get_security_middleware()
            
            # Extract request data (assuming first argument is request data)
            request_data = args[0] if args and isinstance(args[0], dict) else {}
            
            # Create validation request
            validation_request = ValidationRequest(
                endpoint=endpoint_name or func.__name__,
                method="POST",
                data=request_data,
                headers={"User-Agent": "DefinitieAgent"},
                source_ip="127.0.0.1",  # Would be extracted from actual request
                user_agent="DefinitieAgent",
                timestamp=datetime.now()
            )
            
            # Validate request
            response = await middleware.validate_request(validation_request)
            
            if not response.allowed:
                raise ValueError(f"Security validation failed: {'; '.join(response.validation_errors)}")
            
            # Use sanitized data
            sanitized_args = list(args)
            if sanitized_args and isinstance(sanitized_args[0], dict):
                sanitized_args[0] = response.sanitized_data
            
            return await func(*sanitized_args, **kwargs)
        return wrapper
    return decorator


async def test_security_middleware():
    """Test the security middleware system."""
    print("🔒 Testing Security Middleware")
    print("=" * 30)
    
    middleware = get_security_middleware()
    
    # Test normal request
    normal_request = ValidationRequest(
        endpoint="definition_generation",
        method="POST",
        data={
            "begrip": "identiteitsbehandeling",
            "context_dict": {
                "organisatorisch": ["Strafrechtketen"],
                "juridisch": ["Strafrecht"],
                "wettelijk": ["Wetboek van Strafrecht"]
            }
        },
        headers={"User-Agent": "Mozilla/5.0"},
        source_ip="192.168.1.1",
        user_agent="Mozilla/5.0",
        timestamp=datetime.now()
    )
    
    response = await middleware.validate_request(normal_request)
    print(f"✅ Normal request: {'ALLOWED' if response.allowed else 'BLOCKED'}")
    
    # Test malicious request
    malicious_request = ValidationRequest(
        endpoint="definition_generation",
        method="POST",
        data={
            "begrip": "<script>alert('XSS')</script>",
            "context_dict": {
                "organisatorisch": ["'; DROP TABLE users; --"],
                "juridisch": ["Strafrecht"],
                "wettelijk": ["Wetboek van Strafrecht"]
            }
        },
        headers={"User-Agent": "Mozilla/5.0"},
        source_ip="192.168.1.2",
        user_agent="Mozilla/5.0",
        timestamp=datetime.now()
    )
    
    response = await middleware.validate_request(malicious_request)
    print(f"🚨 Malicious request: {'ALLOWED' if response.allowed else 'BLOCKED'}")
    print(f"🚨 Threats detected: {len(response.threats_detected)}")
    print(f"🚨 Security events: {len(response.security_events)}")
    
    # Test rate limiting
    print("\n🚥 Testing rate limiting...")
    for i in range(15):  # Exceed rate limit
        test_request = ValidationRequest(
            endpoint="definition_generation",
            method="POST",
            data={"begrip": f"test_{i}"},
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.1.3",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now()
        )
        
        response = await middleware.validate_request(test_request)
        if not response.allowed:
            print(f"🚥 Rate limit triggered at request {i+1}")
            break
    
    # Generate security report
    report = middleware.get_security_report()
    print(f"\n📊 Security Report:")
    print(f"  Total events: {report['total_security_events']}")
    print(f"  Blocked requests: {report['blocked_requests']}")
    print(f"  Block rate: {report['block_rate']:.1%}")
    print(f"  Threat types: {report['threat_types']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_security_middleware())
