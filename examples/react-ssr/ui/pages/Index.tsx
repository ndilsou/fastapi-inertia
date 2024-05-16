import { useState } from "react";
import { Link, Head } from "@inertiajs/react";

export default function IndexPage({ name = "World" }: { name: string }) {
  const [count, setCount] = useState(0);
  return (
    <>
      <Head title="Index Page" />
      <div className="flex flex-col items-center justify-start h-screen pt-10">
        <h1 className="text-4xl font-bold">Hello {name}</h1>
        <p>This is the index page.</p>
        <div className="card bg-base-300 mt-3">
          <div className="card-body">
            <button
              className="btn btn-primary"
              onClick={() => setCount((count) => count + 1)}
            >
              count is {count}
            </button>
          </div>
        </div>
        <Link href="/about" className="link">
          About
        </Link>
      </div>
    </>
  );
}
