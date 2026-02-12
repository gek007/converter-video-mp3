import os

import requests


def login(request):
    """Forward login request to auth service."""
    auth = request.authorization
    
    if not auth:
        return None, ("Missing credentials", 401)
    
    try:
        response = requests.post(
            f"http://{os.getenv('AUTH_SVC_ADDRESS')}/login",
            auth=(auth.username, auth.password)
        )
        
        if response.status_code == 200:
            return response.text, None
        else:
            return None, (response.text, response.status_code)
    except Exception as e:
        return None, (f"Auth service connection failed: {str(e)}", 503)
