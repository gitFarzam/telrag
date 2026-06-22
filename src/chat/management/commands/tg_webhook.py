from django.core.management.base import BaseCommand, CommandError
from chat.utils.telegram import set_telegram_webhook_secret,delete_telegram_webhook,info_telegram_webhook

class Command(BaseCommand):

    help = f"""
    Telegram Webhook Operation\n
    use --set flag to set telegram webhook\n
    use --info flag to get update from telegram webhook\n
    use --del flag to delete telegram webhook\n
    """

    def add_arguments(self, parser):
        """
        This method will add arguments to the command
        """
        parser.add_argument(
            "--set",
            action="store_true",
            help="Set New Webhook",
        )

        parser.add_argument(
            "--info",
            action="store_true",
            help="Info of Webhook",
        )

        parser.add_argument(
            "--del",
            action="store_true",
            help="Delete Current Webhook",
        )

    def handle(self,*args,**options):
        error_message = self.style.ERROR(f"Error!")
        success_message = self.style.SUCCESS(f"Done!!!")
        
        try:
            if options['set']:
                success = set_telegram_webhook_secret()

            elif options['info']:
                success = info_telegram_webhook()

            elif options['del']:
                success = delete_telegram_webhook()

            success = True

        except Exception as e:
            success = False
            raise CommandError(f"Error: {e}")

        if success:
            self.stdout.write(success_message)
        else:
            self.stdout.write(error_message)