from django.urls import reverse
from django.contrib import admin

from shop.decorators import admin_changelist_link

from . import models


@admin.register(models.DjConfig)
class DjConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.SpiritCategory)
class SpiritCategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_closed', 'is_removed', 'is_private', 'is_global']


@admin.register(models.SpiritUserProfile)
class SpiritUserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'slug', 'last_seen', 'last_post_on', 'is_administrator', 'is_moderator']
    list_filter = ['is_administrator', 'is_moderator']
    readonly_fields = ['user', 'slug', 'topic_count', 'comment_count', 'last_seen', 'last_ip', 'last_post_on', 'last_post_hash']
    search_fields = ['user__phone', 'user__name', 'user__email']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.SpiritTopic)
class SpiritTopicAdmin(admin.ModelAdmin):
    def category_title(self, obj):
        return obj.category.title
    category_title.admin_order_field = 'category'
    category_title.short_description = 'категория'

    def view_link(self, obj):
        return '<a href={}><i class="icon-eye-open"></i></a>'.format(reverse('spirit:topic:detail', args=(obj.pk, obj.slug)))
    view_link.allow_tags=True
    view_link.short_description = 'просмотр'

    list_display = ['title', 'category_title', 'date', 'comment_count', 'is_pinned', 'is_globally_pinned', 'is_closed', 'is_removed', 'view_link']
    list_filter = ['is_pinned', 'is_globally_pinned', 'is_closed', 'is_removed']
    readonly_fields = ['user', 'date', 'last_active', 'view_count', 'comment_count']
    search_fields = ['title']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.SpiritCommentFlag)
class SpiritCommentFlagAdmin(admin.ModelAdmin):
    def view_link(self, obj):
        return "<a href={}>{}</a>".format(reverse('spirit:comment:find', args=(obj.pk,)), obj.comment.comment)
    view_link.allow_tags=True
    view_link.short_description = 'просмотр'

    def moderate_link(self, obj):
        return '<a href={}><i class="icon-lock"></i></a>'.format(reverse('spirit:admin:flag:detail', args=(obj.pk,)))
    moderate_link.allow_tags=True
    moderate_link.short_description = 'модерирование'

    list_display = ['view_link', 'date', 'is_closed', 'moderate_link']
    list_filter = ['is_closed']
    list_display_links = None

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Opinion)
class OpinionAdmin(admin.ModelAdmin):
    def author_link(self, obj):
        if obj.author.pk == '':
            return obj.author
        return "<a href={}>{}</a>".format(reverse('admin:{}_{}_change'.format(obj.author._meta.app_label, obj.author._meta.model_name), args=(obj.author.pk,)), obj.author)
    author_link.admin_order_field = 'author'
    author_link.allow_tags=True
    author_link.short_description = 'author'

    list_display = ['id', 'tid', 'post', 'text', 'author_link', 'ip']
    list_display_links = ['id', 'tid']
    readonly_fields = ['tid', 'post', 'author', 'ip']
    search_fields = ['text', 'author__id', 'author__login', 'ip']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Thread)
class ThreadAdmin(admin.ModelAdmin):
    def owner_link(self, obj):
        if obj.owner.pk == '':
            return obj.owner
        return "<a href={}>{}</a>".format(reverse('admin:{}_{}_change'.format(obj.owner._meta.app_label, obj.owner._meta.model_name), args=(obj.owner.pk,)), obj.owner)
    owner_link.admin_order_field = 'owner'
    owner_link.allow_tags=True
    owner_link.short_description = 'owner'

    def discuss_count(self, obj):
        return models.Opinion.objects.filter(tid=obj.pk).count()
    discuss_count.short_description = 'len'

    @admin_changelist_link(None, 'ops', model=models.Opinion, query_string=lambda t: 'tid={}'.format(t.pk))
    def discuss_link(self, opinions):
        return '<i class="icon-list"></i>'

    list_display = ['id', 'topic', 'title', 'mtime', 'owner_link', 'ip', 'discuss_link', 'discuss_count']
    list_display_links = ['title']
    list_filter = ['topic', 'isopen', 'archived']
    readonly_fields = ['mtime', 'owner', 'ip']
    search_fields = ['title', 'owner__id', 'owner__login', 'ip']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title']
    list_display_links = ['title']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.BassetUser)
class BassetUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'login', 'fio', 'email', 'phone']
    list_display_links = ['id']
    search_fields = ['id', 'login', 'fio', 'email', 'phone']
    list_per_page = 100

    def has_add_permission(self, request, obj=None):
        return False
