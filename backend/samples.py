import random
from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import JSONResponse

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class SearchRequest(BaseModel):
    yourUsername: str | None = None
    usernames: list[str]


@router.post("/login")
async def login(request: LoginRequest):
    """
    Login endpoint with hardcoded credentials.
    Only accepts username: "admin" and password: "password"
    """
    if request.username == "admin" and request.password == "password":
        return JSONResponse({
            "success": True,
            "message": "Login successful!",
            "username": request.username
        })
    else:
        return JSONResponse({
            "error": "Invalid username or password",
            "success": False
        }, status_code=401)


@router.post("/search")
async def search(request: SearchRequest):
    """
    Search endpoint that returns random generated data for the provided usernames.
    """
    if not request.usernames or len(request.usernames) == 0:
        return JSONResponse({
            "error": "No usernames provided"
        }, status_code=400)
    
    # Generate random data for each username
    results = []
    statuses = ["Active", "Inactive", "Pending", "Suspended"]
    details = [
        "Account verified",
        "Email not confirmed",
        "Premium member",
        "New user",
        "Requires verification",
        "Profile complete"
    ]
    
    for username in request.usernames:
        results.append({
            "username": username,
            "status": random.choice(statuses),
            "details": random.choice(details)
        })
    
    response = {
        "success": True,
        "count": len(results),
        "results": results
    }
    
    if request.yourUsername:
        response["yourUsername"] = request.yourUsername
    
    return JSONResponse(response)