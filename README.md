# kroesslabs.de

Website of Kroess Labs: the studio homepage, a page per app (English and German),
the legal notice and the privacy policies. Served by GitHub Pages at
<https://kroesslabs.de/>.

## Editing

The HTML pages are generated. Edit the sources, then rebuild:

```sh
python3 tools/build.py
```

| What | Where |
| --- | --- |
| Page copy, apps, navigation | `tools/build.py` (`HOME`, `APPS`, `APP_PAGES`) |
| Legal texts | `src/legal/*.html` |
| Styles, script | `assets/css/site.css`, `assets/js/site.js` |
| Images, video, fonts | `assets/img/`, `assets/video/`, `assets/fonts/` |

After changing CSS or JS, raise `ASSET_VERSION` in `tools/build.py` so browsers
fetch the new files.

To add an app: add it to `APPS` and `APP_PAGES` and `URLS`, add its images to
`assets/img/` (`<key>.webp`, `<key>-800.webp`, an icon), and rebuild.

## Addresses that must not move

These URLs are compiled into Quevia and entered in Google Play and App Store
Connect. The old `prismadiamond.github.io` addresses redirect here via the
`PrismaDiamond/PrismaDiamond.github.io` repository.

| Page | URL |
| --- | --- |
| Impressum (de) | `/impressum/` |
| Legal notice (en) | `/legal-notice/` |
| Quevia – Datenschutzerklärung (de) | `/quevia/datenschutz/` |
| Quevia – Privacy policy (en) | `/quevia/privacy/` |

## Privacy

Nothing is loaded from third parties: fonts, images and video are served from
this domain, and there are no cookies, no analytics and no external scripts.
Keep it that way, the privacy policies say so.

`.nojekyll` stops GitHub Pages from running Jekyll.

## Spark Android preview

The APK supplied on 2026-11-14 is self-hosted at
`/downloads/spark/spark-0.1-debug.apk`. It is the original signed debug build
(`com.kroess.spark.debug`, version `0.1-debug`, Android 9+), available from the
homepage card and Spark page in both languages. It is not a Google Play release.

To publish another build, add it under a new filename in `downloads/spark/`,
update `SPARK_APK` and both `download_meta` strings in `tools/build.py`, and
verify its minimum Android version before updating the copy. The displayed
file size is read from the APK when generating the pages. Keep old download
URLs working. Rebuild and check the pages before publishing.
