from django.contrib import admin

import html2text

from .models import Feed, Entry, Subscriber


class EntryInline(admin.TabularInline):
    model = Entry

    def short_summary(self, obj):
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.single_line_break = True
        h.ignore_tables = True
        return h.handle(obj.summary[:500])

    fields = ('title', 'publication_date', 'short_summary', 'sent')
    readonly_fields = ['title', 'publication_date', 'short_summary']


class FeedAdmin(admin.ModelAdmin):
    inlines = [EntryInline, ]
    readonly_fields = ['last_update', ]


admin.site.register(Feed, FeedAdmin)
admin.site.register(Entry)
admin.site.register(Subscriber)
