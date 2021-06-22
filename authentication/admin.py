from django.contrib import admin
from .models import User, Author
from django.db.models import Count


class AuthorInline(admin.StackedInline):
    model = Author
    extra = 0


class UserAdmin(admin.ModelAdmin):
    model = User
    search_fields = ['first_name', 'last_name', 'pk', 'email', 'author__nickname']
    list_display = ['pk', 'get_full_name', 'get_author_nickname', 'get_followers_count']
    inlines = [AuthorInline]

    def get_queryset(self, request):
        qs = super(UserAdmin, self).get_queryset(request)
        qs = qs.annotate(top=Count('author__followers')).order_by('-top')
        return qs

    def get_full_name(self, instance):
        return f'{instance.first_name} {instance.last_name}'

    get_full_name.short_description = 'Full Name'

    def get_author_nickname(self, instance):
        return instance.author.nickname

    get_author_nickname.short_description = 'Author'

    def get_followers_count(self, instance):
        return instance.author.followers.count()

    get_followers_count.short_description = 'Followers'


admin.site.register(User, UserAdmin)
