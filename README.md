# nicolaedicu.ro

Personal website: nicolaedicu.ro

### BUILD: make -C docs html

## SMS Redirect privacy policy

The policy is served at https://nicolaedicu.ro/smsredirectpolicy/ from
`docs/source/_extra/smsredirectpolicy/index.html`. Sphinx's existing
`html_extra_path` setting copies this standalone page into the published site.
The existing deployment workflow publishes it when changes reach `main`.

To update it, copy the reviewed `docs/privacy/index.html` from
`nicu1989/android-smsredirect` into that path, build the site, and verify
`docs/build/html/smsredirectpolicy/index.html`. Keep the policy content in both
repositories synchronized. The standalone policy does not load the site's
analytics script or other external resources.
