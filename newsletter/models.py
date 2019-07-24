import logging
from datetime import datetime
import pytz

from django.db import models

import feedparser
import arrow


logger = logging.getLogger(__name__)


class Feed(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()
    last_update = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['name', 'url']]
        verbose_name_plural = 'feeds'

    def __str__(self):
        return f'{self.name}'

    @property
    def unsent_entries(self):
        return self.entries.filter(sent=False)

    def sync_feed(self):
        logger.info(f'Fetching entries for "{self.name}"')
        feed = feedparser.parse(self.url)
        try:
            last_published = arrow.get(feed.updated, 'ddd, DD MMM YYYY HH:mm:ss').datetime
        except (AttributeError, KeyError):
            logger.warning(f'There was an error trying to fetch some data for feed "{self.name}"')
            try:
                last_published = arrow.get(feed.feed.updated, 'ddd, DD MMM YYYY HH:mm:ss').datetime
            except AttributeError:
                last_published = arrow.get(feed.entries[0].published, 'ddd, DD MMM YYYY HH:mm:ss').datetime

        if last_published < self.last_update:
            logger.info(f'There are new entries for feed "{self.name}"')
            entries = list()
            for entry in feed.entries:
                if Entry.objects.filter(entry_id=entry.id).exists():
                    continue
                try:
                    tags = ', '.join(tag.term for tag in entry.tags)
                except AttributeError:
                    tags = ''

                entries.append(
                    Entry(entry_id=entry.id,
                          publication_date=arrow.get(entry.published, 'ddd, DD MMM YYYY HH:mm:ss').datetime,
                          title=entry.title,
                          tags=tags,
                          url=entry.link,
                          summary=entry.summary,
                          feed=self
                          )
                )
            Entry.objects.bulk_create(entries)
        else:
            logger.info(f'There are NO new entries for feed "{self.name}"')
        self.last_update = datetime.now(tz=pytz.timezone('Europe/Madrid'))
        self.save()


class Entry(models.Model):
    entry_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    summary = models.TextField()
    tags = models.CharField(max_length=255)
    url = models.URLField()
    publication_date = models.DateTimeField()
    sent = models.BooleanField(default=False)
    feed = models.ForeignKey(Feed, related_name='entries', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-publication_date']
        verbose_name_plural = 'entries'

    def __str__(self):
        return f'[{self.feed.name}] {self.title} ({self.publication_date.strftime("%d-%m-%Y")})'


class Subscriber(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()

    class Meta:
        unique_together = [['name', 'email']]

    def __str__(self):
        return f'{self.name} ({self.email})'
