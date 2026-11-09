// Kroess Labs: small progressive enhancements. Everything works without it.
(function () {
  var doc = document.documentElement;
  doc.classList.add("js");

  // Header gets a solid background once the page scrolls.
  var header = document.querySelector(".site-header");
  function onScroll() {
    if (header) header.classList.toggle("solid", window.scrollY > 24);
  }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  // Fade sections in as they come into view.
  var items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("in"); });
  }

  // Hero video: only on larger screens, without reduced motion or data saver.
  // The poster image stays visible otherwise.
  var video = document.querySelector(".hero-media video");
  if (video) {
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var saver = navigator.connection && navigator.connection.saveData;
    var small = window.matchMedia("(max-width: 720px)").matches;
    if (reduce || saver || small) {
      video.remove();
    } else {
      video.querySelectorAll("source[data-src]").forEach(function (s) { s.src = s.getAttribute("data-src"); });
      video.load();
      video.addEventListener("playing", function () { video.classList.add("ready"); }, { once: true });
      var p = video.play();
      if (p && p.catch) p.catch(function () { video.remove(); });
    }
  }
})();
