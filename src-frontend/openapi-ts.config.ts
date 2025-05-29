import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "../api-spec.json",
  output: "./src/api/",
  plugins: ["@hey-api/client-axios"],
});
