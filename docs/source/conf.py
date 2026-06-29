# Configuration file for the Sphinx documentation builder.

project = "Nicolae Dicu"
author = "Nicolae Dicu"

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "shibuya"
html_title = "Nicolae Dicu"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_extra_path = ["_extra"]

html_theme_options = {
  "github_url": "https://github.com/nicu1989/nicolaedicu.ro",
  "page_layout": "compact",
  "nav_links": [
        {
            "title": "Open Source Contributions",
            "children": [
                {
                    "title": "SCORE",
                    "url": "projects/eclipse-score",
                },
                {
                    "title": "Nordic & Zephyr",
                    "url": "projects/nrfconnect",
                },
                {
                    "title": "Other Organizations",
                    "url": "projects/other-open-source",
                }
            ]
        },
        {
            "title": "Hobby Projects",
            "url": "writing",
            "children": [
                {
                    "title": "Fitcamx repair",
                    "url": "fitcamx_dummy",
                }
            ]
        },
  ]
}
