from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.http import JsonResponse

def index(request):
    template_name = 'index.html'
    return render(request, template_name)


