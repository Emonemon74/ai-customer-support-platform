import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const previewAllowedHosts = env.VITE_PREVIEW_ALLOWED_HOSTS
    ?.split(",")
    .map((host) => host.trim())
    .filter(Boolean);

  return {
    plugins: [
      react(),
      tailwindcss(),
    ],
    preview: {
      allowedHosts: previewAllowedHosts,
    },
  };
});
