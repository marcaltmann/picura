import "vite/modulepreload-polyfill";

import Alpine from "alpinejs";

import "@/css/public.css";
import { audioPlayer } from "./audio-player.js";

Alpine.data("audioPlayer", audioPlayer);

window.Alpine = Alpine;
Alpine.start();
