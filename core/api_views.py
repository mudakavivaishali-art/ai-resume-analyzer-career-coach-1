from django.http import JsonResponse

def api_home(request):
    return JsonResponse({
        "status": "success",
        "message": "API is working successfully!"
    })

def analyze_resume(request):
    return JsonResponse({
        "status": "success",
        "message": "Resume analysis endpoint is ready."
    })