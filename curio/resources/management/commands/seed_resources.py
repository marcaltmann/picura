from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from curio.resources.models import Resource

SAMPLES = [
    {
        'title': 'Morning Meditation',
        'duration': timedelta(minutes=10, seconds=32),
    },
    {
        'title': 'Focus Music',
        'duration': timedelta(minutes=45, seconds=0),
    },
    {
        'title': 'Evening Wind Down',
        'duration': timedelta(minutes=20, seconds=15),
    },
]


class Command(BaseCommand):
    help = 'Seed sample audio Resource data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing audio Resource records before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count, _ = Resource.objects.filter(
                resource_type=Resource.Type.AUDIO
            ).delete()
            self.stdout.write(f'Deleted {count} existing record(s).')

        for sample in SAMPLES:
            filename = sample['title'].lower().replace(' ', '_') + '.mp3'
            resource = Resource(
                resource_type=Resource.Type.AUDIO,
                title=sample['title'],
                duration=sample['duration'],
            )
            resource.file.save(filename, ContentFile(b''), save=True)
            self.stdout.write(f'Created: {sample["title"]}')

        self.stdout.write(self.style.SUCCESS('Done.'))
