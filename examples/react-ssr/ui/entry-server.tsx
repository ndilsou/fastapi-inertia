import { createInertiaApp } from "@inertiajs/react";
import createServer from "@inertiajs/react/server";
import ReactDOMServer from "react-dom/server";
import "./global.css";
import { resolvePageComponent } from "./utils";

createServer((page) =>
  createInertiaApp({
    page,
    render: ReactDOMServer.renderToString,
    resolve: (name) => {
      return resolvePageComponent(
        `./pages/${name}.tsx`,
        import.meta.glob("./pages/**/*.tsx")
      );
    },
    setup({ el, App, props }) {
      return <App {...props} />;
    },
  })
);
