"""Gera uma chave de assinatura nova e só a imprime. Nada é gravado em arquivo."""

from django.core.management.base import BaseCommand

from apps.audit.signing import generate_key_text


class Command(BaseCommand):
    help = "Imprime uma chave privada Ed25519 nova, para colar em AUDIT_SIGNING_KEY no backend/.env."

    def handle(self, *args, **options):
        self.stdout.write("Cole a linha abaixo no arquivo backend/.env (e nunca no repositório):")
        self.stdout.write(f"AUDIT_SIGNING_KEY={generate_key_text()}")
