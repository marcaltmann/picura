import "vite/modulepreload-polyfill";

import Alpine from "alpinejs";

import "@/css/public.css";

// Initialize Alpine.js
window.Alpine = Alpine;
Alpine.start();
