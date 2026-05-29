import "vite/modulepreload-polyfill";

import Alpine from "alpinejs";

import photoNav from "@/js/alpine/photo-nav.js";

import "@/css/public.css";

// Initialize Alpine.js
window.Alpine = Alpine;
Alpine.data("photoNav", photoNav);
Alpine.start();
