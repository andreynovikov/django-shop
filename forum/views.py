from django.shortcuts import render, get_object_or_404

from .models import Topic, Thread, Opinion


def index(request):
    context = {'topics': Topic.objects.filter(enabled=True).order_by('seq')}
    return render(request, 'forum/index.html', context)


def topic(request, id):
    topic = get_object_or_404(Topic, pk=id)
    context = {'topic': topic, 'threads': Thread.objects.filter(topic=topic.id, enabled=True).order_by('mtime')}
    return render(request, 'forum/topic.html', context)


def thread(request, id):
    thread = get_object_or_404(Thread, pk=id)
    context = {'thread': thread, 'opinions': Opinion.objects.filter(tid=thread.id).order_by('post')}
    return render(request, 'forum/thread.html', context)
