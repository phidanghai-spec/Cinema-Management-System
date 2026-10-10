"""
Django Management Command: sync_movies

Usage:
    python manage.py sync_movies
    python manage.py sync_movies --limit 15 --source tmdb
    python manage.py sync_movies --source tvmaze
"""

from django.core.management.base import BaseCommand
from cinema.services import MovieSyncService


class Command(BaseCommand):
    help = "Synchronize now-playing movie catalog from external movie APIs (TMDB/TVMaze/Curated)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of movies to synchronize (default: 10)'
        )
        parser.add_argument(
            '--source',
            type=str,
            default='auto',
            choices=['auto', 'tmdb', 'tvmaze', 'curated'],
            help='Data source to sync from: auto (default), tmdb, tvmaze, curated'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        source = options['source']

        self.stdout.write(self.style.NOTICE(f"[START] Starting movie catalog synchronization (limit={limit}, source={source})..."))

        try:
            result = MovieSyncService.sync_now_playing_movies(limit=limit, source=source)
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(
                    f"[SUCCESS] Successfully synchronized {result['count']} movies using '{result['source']}'!"
                ))
                self.stdout.write(f"   Created: {result.get('created_count', 0)}")
                self.stdout.write(f"   Updated: {result.get('updated_count', 0)}")
                self.stdout.write("--- Synced Movies ---")
                for idx, title in enumerate(result.get('movies', []), start=1):
                    try:
                        self.stdout.write(f"   {idx}. {title}")
                    except UnicodeEncodeError:
                        safe_title = title.encode('ascii', errors='replace').decode('ascii')
                        self.stdout.write(f"   {idx}. {safe_title}")
            else:
                self.stdout.write(self.style.WARNING("[WARNING] Synchronization completed with warnings or zero movies."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[ERROR] Failed to sync movies: {e}"))
