# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys


project = 'global_exchange'
copyright = '2025, Maria Cielito Melgarejo Baez, Manuel Antonio Aguero Vera, Raquel Panambi Torres Otazu, Martin Leonardo Cano Gonzalez, Sofia Monserrat Sanabria Estigarribia'
author = 'Maria Cielito Melgarejo Baez, Manuel Antonio Aguero Vera, Raquel Panambi Torres Otazu, Martin Leonardo Cano Gonzalez, Sofia Monserrat Sanabria Estigarribia'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # Genera documentación desde docstrings
    'sphinx.ext.napoleon',     # Soporte docstrings tipo Google o NumPy
    'sphinx.ext.viewcode',  # Agrega enlaces al código fuente
]

templates_path = ['_templates']
exclude_patterns = []

language = 'es'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Tema HTML
html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

sys.path.insert(0, os.path.abspath('../..'))  # Para importar tu proyecto Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_project.settings")

import django
django.setup()

# Excluir migraciones y archivos innecesarios de la documentación
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**/migrations/*']

# Configuración de napoleon para soportar docstrings estilo Google
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_use_param = True
napoleon_use_rtype = True
