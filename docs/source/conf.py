import sys
import os

sys.path.append(os.path.abspath('../..'))


extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'nature'
html_static_path = ['_static']

project = 'Stas'
copyright = '2023, Stas'
author = 'Stas'

