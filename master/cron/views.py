from django.shortcuts import render
from django.views.generic import ListView, View
from django.utils.decorators import method_decorator

# Create your views here.
class CronView(View):
    def get(self, request):
        
