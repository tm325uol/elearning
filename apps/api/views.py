from django.shortcuts import render
from django.urls import reverse


def api_home(request):
    return render(
        request,
        "api/index.html",
        {
            "app_name": "CM3035 | E-Learning Final Project",
            "api_links": {
                "OpenAPI Schema (JSON)": reverse("api:schema"),
                "Swagger UI": reverse("api:swagger"),
                "ReDoc": reverse("api:redoc"),
            },
        },
    )