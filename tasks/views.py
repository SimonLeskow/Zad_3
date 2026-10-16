import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .models import Task


def task_to_dict(task):
    return {
        "id": task.id,
        "title": task.title,
        "completed": task.completed,
        "created_at": task.created_at.isoformat(),
    }


def parse_json(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


@ensure_csrf_cookie          # ustawia cookie csrftoken, które odczyta JS
def index(request):
    return render(request, "tasks/index.html")


@require_http_methods(["GET", "POST"])
def task_list(request):
    if request.method == "GET":
        tasks = Task.objects.all()
        return JsonResponse([task_to_dict(t) for t in tasks], safe=False)

    # POST
    data = parse_json(request)
    if data is None:
        return JsonResponse({"error": "Niepoprawny JSON."}, status=400)

    title = data.get('title')
    if not isinstance(title, str) or not title.strip():
        return JsonResponse({"error": "Treść zadania nie może być pusta."}, status=400)
    if len(title.strip()) > 200:
        return JsonResponse({"error": "Zadanie może mieć maksymalnie 200 znaków."}, status=400)

    task = Task.objects.create(title=title.strip())
    return JsonResponse(task_to_dict(task), status=201)


@require_http_methods(["PATCH", "DELETE"])
def task_detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return JsonResponse({"error": "Zadanie o podanym ID nie istnieje."}, status=404)

    if request.method == "DELETE":
        task.delete()
        return HttpResponse(status=204)

    # PATCH
    data = parse_json(request)
    if data is None or not isinstance(data.get("completed"), bool):
        return JsonResponse(
            {"error": "Pole 'completed' musi być wartością true lub false."}, status=400
        )
    task.completed = data["completed"]
    task.save()
    return JsonResponse(task_to_dict(task))
