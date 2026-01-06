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
            "title": "CV",
            "url": "cv_dummy"
        },
        {
            "title": "Open Source Contributions",
            "children": [
                {
                    "title": "SCORE",
                    "url": "score_dummy",
                },
                {
                    "title": "Nordic & Zephyr",
                    "url": "nordic_dummy",
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