from django.core.management.base import BaseCommand

from certificats_ssl.alerts import run_ssl_alert_checks


class Command(BaseCommand):
    help = (
        'Vérifie les certificats SSL et envoie des alertes aux admins '
        '(e-mail, SMS si configuré, notification in-app). '
        'À planifier quotidiennement via cron ou tâche planifiée.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule la vérification sans envoyer de notifications.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        stats, results = run_ssl_alert_checks(dry_run=dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING('Mode simulation — aucune alerte envoyée.'))

        self.stdout.write(
            f"Certificats vérifiés : {stats['checked']} | "
            f"En alerte : {stats['alerted']} | "
            f"E-mails : {stats['email']} | "
            f"SMS : {stats['sms']} | "
            f"Notifications app : {stats['app']}"
        )

        for result in results:
            if not result.get('niveau'):
                continue
            suffix = ' (simulation)' if result.get('dry_run') else ''
            self.stdout.write(
                f"  - {result['certificat']} [{result['niveau']}] "
                f"email={result['email']} sms={result['sms']} app={result['app']}{suffix}"
            )
