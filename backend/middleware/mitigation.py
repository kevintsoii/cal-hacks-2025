import asyncio
from starlette.responses import JSONResponse

from .recaptcha import verify_recaptcha
from db.redis import redis_client


# Mitigation levels (higher = more severe)
MITIGATION_LEVELS = {
    "none": 0,
    "delay": 1,
    "captcha": 2,
    "temp_block": 3,
    "ban": 4
}


async def check_mitigations(ip: str, user: str = None) -> tuple[str, int]:
    """
    Check Redis for both IP and user mitigations and return the greatest.
    Returns tuple of (mitigation_type, severity_level).
    """
    ip_mitigation = None
    user_mitigation = None
    
    # Check IP mitigation
    if ip:
        ip_key = f"mitigation:ip:{ip}"
        ip_mitigation = await redis_client.get_value(ip_key)
    
    # Check user mitigation
    if user:
        user_key = f"mitigation:user:{user}"
        user_mitigation = await redis_client.get_value(user_key)
    
    # Determine the greatest mitigation
    ip_severity = MITIGATION_LEVELS.get(ip_mitigation, 0) if ip_mitigation else 0
    user_severity = MITIGATION_LEVELS.get(user_mitigation, 0) if user_mitigation else 0
    
    return max(user_severity, ip_severity)


async def apply_mitigation(severity: int, captcha_token: str = None) -> JSONResponse:
    """
    Apply the appropriate mitigation and return the response.
    Handles captcha verification for captcha-level mitigations.
    """
    if severity >= MITIGATION_LEVELS["ban"]:
        return JSONResponse(
            status_code=403,
            content={
                "error": "You have been permanently banned due to suspicious activity.",
                "message": "Your access has been permanently blocked due to suspicious activity."
            }
        )
    elif severity >= MITIGATION_LEVELS["temp_block"]:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Your account has been temporarily blocked due to suspicious activity.",
                "message": "Your access has been temporarily blocked. Please try again later."
            }
        )
    elif severity >= MITIGATION_LEVELS["captcha"]:
        # Check if captcha token was provided
        if not captcha_token:
            # No token provided, return captcha required
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Captcha required",
                    "message": "Please complete the captcha verification to continue.",
                    "requires_captcha": True
                }
            )
        
        # Verify the captcha token
        is_valid = await verify_recaptcha(captcha_token)
        if not is_valid:
            # Invalid captcha token
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Captcha verification failed",
                    "message": "The captcha verification failed. Please try again.",
                    "requires_captcha": True
                }
            )
        
        # Captcha verified successfully, return None to continue with the request
        return None
    elif severity >= MITIGATION_LEVELS["delay"]:
        # Apply delay (100-500ms)
        await asyncio.sleep(0.5)  # 300ms delay
    
    return None  # No mitigation, proceed normally
