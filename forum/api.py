from rest_framework import viewsets, serializers, status
from rest_framework.response import Response

from .models import Topic, Thread, Opinion


class OpinionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Opinion
        fields = ('id', 'post', 'text')


class ThreadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = ('id', 'mtime', 'title')


class ThreadSerializer(ThreadListSerializer):
    opinions = serializers.SerializerMethodField()

    class Meta(ThreadListSerializer.Meta):
        fields = ThreadListSerializer.Meta.fields + ('opinions',)

    def get_opinions(self, obj):
        opinions = Opinion.objects.filter(tid=obj.id).order_by('post')
        return OpinionSerializer(opinions, many=True).data


class TopicSerializer(serializers.ModelSerializer):
    threads = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ('id', 'title', 'threads')

    def get_threads(self, obj):
        threads = Thread.objects.filter(topic=obj.id, enabled=True).order_by('-mtime')
        return ThreadListSerializer(threads, many=True).data


class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    ordering = ('seq',)
    serializer_class = TopicSerializer

    def get_queryset(self):
        return Topic.objects.filter(enabled=True)


class ThreadViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ThreadSerializer

    def get_queryset(self):
        return Thread.objects.filter(enabled=True)

    def list(self, request):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
