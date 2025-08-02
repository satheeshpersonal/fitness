# utils/response.py

def success_response(data={}, message="success", code="success", extra_data={}):
    return {
        "status": "success",
        "data": data,
        "extra_data": extra_data,
        "error": {
            "code": code,
            "message": message
        }
    }

def error_response(message="Something went wrong", code="error", data={}):
    return {
        "status": "failure",
        "data": data,
        "error": {
            "code": code,
            "message": message
        }
    }
