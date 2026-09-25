"""
Grupo "editores" y su usuario - paso 9.

Crea un grupo con permiso para anadir y cambiar peliculas, pero NO para
eliminarlas, y un usuario dentro de ese grupo:

    py manage.py setup_editores

El paso 9 pide hacerlo desde el panel (Autenticacion y autorizacion > Grupos).
El comando hace exactamente lo mismo y sirve para repetir la entrega sin
tener que volver a hacer clic a clic.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

# Permisos que el enunciado concede al grupo "editores".
PERMISOS_CONCEDIDOS = ["view_movie", "add_movie", "change_movie"]

# Permiso que el enunciado excluye expresamente.
PERMISOS_EXCLUIDOS = ["delete_movie"]

NOMBRE_GRUPO = "editores"
USUARIO_EDITOR = "editor01"
EMAIL_EDITOR = "editor01@cinevault.local"
CLAVE_EDITOR = "Editor2026!"


class Command(BaseCommand):
    help = 'Crea el grupo "editores" (anadir y cambiar, nunca eliminar) y su usuario.'

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help=f"Vuelve a poner la clave {CLAVE_EDITOR} al usuario {USUARIO_EDITOR}.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        grupo, _ = Group.objects.get_or_create(name=NOMBRE_GRUPO)

        concedidos = list(
            Permission.objects.filter(
                content_type__app_label="movies",
                codename__in=PERMISOS_CONCEDIDOS,
            )
        )
        excluidos = Permission.objects.filter(
            content_type__app_label="movies", codename__in=PERMISOS_EXCLUIDOS
        )

        faltan = set(PERMISOS_CONCEDIDOS) - {p.codename for p in concedidos}
        if faltan:
            self.stderr.write(
                self.style.ERROR(
                    f"No se encontraron estos permisos en movies: {sorted(faltan)}"
                )
            )
            return

        grupo.permissions.set(concedidos)
        # El paso 9 es explicito: el grupo no debe poder eliminar peliculas.
        grupo.permissions.remove(*excluidos)

        editor, creado = User.objects.get_or_create(
            username=USUARIO_EDITOR,
            defaults={"email": EMAIL_EDITOR, "is_staff": True},
        )
        editor.email = EMAIL_EDITOR
        # El panel exige que el usuario tenga is_staff para poder entrar.
        editor.is_staff = True
        # Sin is_superuser y sin is_staff=False: es un usuario normal del panel.
        editor.is_superuser = False
        if creado or options["reset_password"]:
            editor.set_password(CLAVE_EDITOR)
        editor.save()
        editor.groups.set([grupo])

        self.stdout.write(self.style.SUCCESS(f'Grupo "{NOMBRE_GRUPO}" configurado:'))
        for permiso in grupo.permissions.all():
            self.stdout.write(
                f"  + {permiso.content_type.app_label}.{permiso.codename} ({permiso.name})"
            )
        for permiso in excluidos:
            if permiso in grupo.permissions.all():  # pragma: no cover - defensivo
                self.stdout.write(self.style.ERROR(f"  - {permiso.codename} NO deberia estar"))
            else:
                self.stdout.write(self.style.ERROR(
                    f"  - {permiso.content_type.app_label}.{permiso.codename} "
                    f"({permiso.name}) -> NO concedido, correcto"
                ))

        self.stdout.write("")
        self.stdout.write(
            f'Usuario "{USUARIO_EDITOR}" en el grupo "{NOMBRE_GRUPO}" '
            f"(is_staff={editor.is_staff}, is_superuser={editor.is_superuser})"
        )
        if not creado and not options["reset_password"]:
            self.stdout.write(
                "  Ya existia, su clave no se ha cambiado. "
                "Usa --reset-password para restablecerla."
            )
        else:
            self.stdout.write(f"  Clave: {CLAVE_EDITOR}")
        self.stdout.write("")
        self.stdout.write("Al entrar con esta cuenta desaparece del panel:")
        self.stdout.write("  - el boton 'Eliminar' de la ficha de la pelicula")
        self.stdout.write("  - la accion masiva 'Eliminar seleccionados' del listado")
