import logging
from itertools import chain

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

from newsletter.models import Entry, Feed, Subscriber


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync feeds and send new entries through email'

    def handle(self, *args, **options):
        self.sync_feeds()
        self.send_email()

    @staticmethod
    def sync_feeds():
        logger.info('Start sync_feed')
        for feed in Feed.objects.all():
            feed.sync_feed()
        logger.info('End sync_feed')

    def send_email(self):
        feed_entries = dict()
        all_entries = list()
        num_entries = 0
        # TODO: Put in function - process_feeds
        for feed in Feed.objects.all():
            entries = feed.unsent_entries
            num_entries += entries.count()
            if entries:
                all_entries.append(list(entries.values_list('id', flat=True)))
                entry_list = list(entries)
                feed_entries[feed.name] = entry_list
                entries.update(sent=True)
        if not feed_entries:
            logger.info('There are no entries')
            return

        context = {'feed_entries': feed_entries}
        email_template = render_to_string("email.html", context)

        recipient_list = list(Subscriber.objects.all().values_list('email', flat=True))

        try:
            send_mail(
                f'Álex Newsletter ({num_entries})',
                email_template,
                settings.EMAIL_HOST_USER,
                recipient_list,
                html_message=email_template,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f'There was a problem sending the email: {repr(e)}')
            all_entries_list = self._flat_list(all_entries)
            self._mark_entries_as_not_sent(all_entries_list)
        else:
            logger.info(f'Email sent with {num_entries} new entries')

    @staticmethod
    def _flat_list(entries_id_list):
        return list(chain.from_iterable(entries_id_list))

    @staticmethod
    def _mark_entries_as_not_sent(entries):
        Entry.objects.filter(id__in=entries).update(sent=False)
