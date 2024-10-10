from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# @login_required
def dashboard(request):
    form = OrdersForm
    return render(request, "dashboard/portfolio.html")
