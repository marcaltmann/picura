// Keyboard navigation for the photo detail page.
// Left/right arrow keys move to the previous/next photo, whose URLs are
// declared as <link rel="prev"> / <link rel="next"> in the document head.
export default () => ({
  go(rel, event) {
    if (event.metaKey || event.ctrlKey || event.altKey) return;

    const active = document.activeElement;
    if (active && active.matches("input, textarea, select, [contenteditable]")) {
      return;
    }

    const link = document.querySelector(`link[rel="${rel}"]`);
    if (link) window.location.assign(link.href);
  },
});
