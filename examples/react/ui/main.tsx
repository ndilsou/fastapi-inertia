import { createRoot } from "react-dom/client";
import { createInertiaApp } from "@inertiajs/react";
import "./global.css";
import { resolvePageComponent } from "./utils";



createInertiaApp({
  resolve: (name) => {
    return resolvePageComponent(
      `./pages/${name}.tsx`,
      import.meta.glob("./pages/**/*.tsx")
    );
  },
  setup({ el, App, props }) {
    createRoot(el).render(<App {...props} />);
  },
});
