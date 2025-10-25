import httpx
import os


# reCAPTCHA configuration
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


async def verify_recaptcha(token: str) -> bool:
    """
    Verify reCAPTCHA token with Google's API.
    Returns True if verification succeeds, False otherwise.
    """
    if not token or not RECAPTCHA_SECRET_KEY:
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RECAPTCHA_VERIFY_URL,
                data={
                    "secret": RECAPTCHA_SECRET_KEY,
                    "response": token
                },
                timeout=5.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("success", False)
            
            return False
    except Exception as e:
        print(f"Error verifying reCAPTCHA: {e}")
        return False
