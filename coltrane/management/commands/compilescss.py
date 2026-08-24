"""
Project-local compilescss management command.

Compiles non-partial SCSS files found in each installed app's static
directories and writes the resulting CSS alongside the source.  This
replaces the django-sass-processor bundled command (which transitively
required django-compressor) with a minimal equivalent that only depends
on libsass, which is already a direct dependency of django-sass-processor.
"""

import os

import sass
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compile SCSS files found in app static directories into CSS."

    def handle(self, *args, **options) -> None:
        verbosity: int = int(options["verbosity"])
        output_style: str = getattr(settings, "SASS_OUTPUT_STYLE", "compressed" if not settings.DEBUG else "nested")
        include_paths: list[str] = [str(p) for p in getattr(settings, "SASS_PROCESSOR_INCLUDE_DIRS", [])]

        compiled = 0
        for app_config in apps.get_app_configs():
            static_dir = os.path.join(app_config.path, "static")
            if not os.path.isdir(static_dir):
                continue
            for root, _dirs, files in os.walk(static_dir):
                for filename in files:
                    if not filename.endswith(".scss") or filename.startswith("_"):
                        continue
                    scss_path = os.path.join(root, filename)
                    css_path = os.path.splitext(scss_path)[0] + ".css"
                    content = sass.compile(
                        filename=scss_path,
                        include_paths=[static_dir] + include_paths,
                        output_style=output_style,
                    )
                    with open(css_path, "w", encoding="utf-8") as fh:
                        fh.write(content)
                    compiled += 1
                    if verbosity >= 2:
                        self.stdout.write(f"Compiled: {scss_path}")

        if verbosity >= 1:
            self.stdout.write(f"Successfully compiled {compiled} SCSS file(s).")
