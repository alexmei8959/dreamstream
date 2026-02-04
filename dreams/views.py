from django.template.response import TemplateResponse
from django.http.response import HttpResponse
from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger("django")

# Create your views here.
def dreamlist(request):
    # username = request.user.first_name
    html = TemplateResponse(request, "dreams/dreamlist.html")
    return HttpResponse(html.render())


def dream_reply(request):
    html = TemplateResponse(request, "dreams/dream_reply.html")
    return HttpResponse(html.render())
