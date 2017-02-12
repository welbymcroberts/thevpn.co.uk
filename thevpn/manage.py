#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "thevpn.settings")
    
    try:
        import django
    except ImportError:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        )

    django.setup()

    # Override default port for `runserver` command
    from django.core.management.commands.runserver import Command as runserver
    from django.conf import settings
    
    runserver.default_addr = settings.DEFAULT_ADDR
    runserver.default_port = settings.DEFAULT_PORT
    
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
