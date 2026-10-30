`heic2any.min.js` is [heic2any](https://github.com/alexcorvi/heic2any) v0.0.4, MIT licensed.
Bundled locally (no CDN/runtime dependency) so HEIC->JPEG conversion works
offline and without a third-party script load on every page view -- it's
only injected into the page when the user actually picks a `.heic`/`.heif`
file on the upload page (see app/templates/upload.html).
