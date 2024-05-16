# React SSR example

This example demonstrates how to use fastapi-inertia with a React Typescript frontend in SSR mode.

## How to run it:

Install the python and bun (or node) dependencies:

```bash
poetry install
bun install
```

Build the frontend:

```bash
bun run build
```

You can refer to Vite and Inertia documentation for more information on  the detail of the SSR build step.

Run the SSR server:

```bash
bun run dist/server/entry-server.js
```

Now run the Fastapi backend:

```bash
poetry run fastapi dev
```
