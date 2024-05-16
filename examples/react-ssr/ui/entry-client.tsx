import { createInertiaApp } from "@inertiajs/react";
import { hydrateRoot } from "react-dom/client";
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
    hydrateRoot(el, <App {...props} />);
  },
});
