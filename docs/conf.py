# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = 'OWLAPY'
author = 'Ontolearn Team'
release = '1.3.2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["autoapi.extension",
              "sphinx.ext.githubpages",
              "sphinx.ext.todo",
              "sphinx.ext.napoleon",
              "sphinx.ext.viewcode",
              "sphinx.ext.autodoc",
              "sphinxcontrib.plantuml",
              "myst_parser",
              "sphinx_rtd_theme",
              ]


autoapi_dirs = ['../owlapy']

# by default all are included but had to reinitialize this to remove private members from showing
autoapi_options = ['members', 'undoc-members', 'show-inheritance', 'show-module-summary', 'special-members',
                   'imported-members']

# this is set to false, so we can add it manually in index.rst together with the other .md files of the documentation.
autoapi_add_toctree_entry = False

inheritance_graph_attrs = dict(rankdir="TB")

myst_enable_extensions = [
    'colon_fence',
    'deflist',
]

myst_heading_anchors = 3

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

pygments_style = 'rainbow_dash'

plantuml_output_format = 'svg_img'
plantuml_latex_output_format = 'pdf'

stanford_theme_mod = True
html_theme_options = {
    'navigation_depth': 6,
}

html_static_path = ['_static']

html_logo = '_static/images/owlapy_logo.png'

html_favicon = '_static/images/favicon.ico'

html_extra_path = ["googlec4c425077889c69c.html"]

if stanford_theme_mod:
    html_theme = 'sphinx_rtd_theme'

    def _import_theme():
        import os
        import shutil
        import sphinx_theme
        html_theme = 'stanford_theme'
        for _type in ['fonts']:
            shutil.copytree(
                os.path.join(sphinx_theme.get_html_theme_path(html_theme),
                             html_theme, 'static', _type),
                os.path.join('_static_gen', _type),
                dirs_exist_ok=True)
        shutil.copy2(
            os.path.join(sphinx_theme.get_html_theme_path(html_theme),
                         html_theme, 'static', 'css', 'theme.css'),
            os.path.join('_static_gen', 'theme.css'),
        )

    _import_theme()
    html_static_path = ['_static_gen'] + html_static_path

# -- Options for LaTeX output ------------------------------------------------

latex_engine = 'xelatex'
latex_show_urls = 'footnote'
latex_theme = 'howto'

latex_elements = {
    'preamble': r'''
\renewcommand{\pysiglinewithargsret}[3]{%
  \item[{%
      \parbox[t]{\linewidth}{\setlength{\hangindent}{12ex}%
        \raggedright#1\sphinxcode{(}\linebreak[0]{\renewcommand{\emph}[1]{\mbox{\textit{##1}}}#2}\sphinxcode{)}\linebreak[0]\mbox{#3}}}]}
''',
    'printindex': '\\def\\twocolumn[#1]{#1}\\footnotesize\\raggedright\\printindex',
}


def setup(app):
    # -- Options for HTML output ---------------------------------------------
    if stanford_theme_mod:
        app.add_css_file('theme.css')
    app.add_css_file('theme_tweak.css')
    app.add_css_file('pygments.css')