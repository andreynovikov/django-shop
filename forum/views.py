from django.shortcuts import render, get_object_or_404

from .models import Thread, Opinion


def thread(request, id):
    thread = get_object_or_404(Thread, pk=id)
    context = {'thread': thread, 'opinions': Opinion.objects.filter(tid=thread.id).order_by('post')}
    return render(request, 'thread.html', context)
