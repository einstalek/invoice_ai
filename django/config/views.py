from django.shortcuts import render

from config.header import build_index_context


def landing(request):
    return render(request, "landing.html")


def index(request):
    return render(request, "index.html", build_index_context(request))
