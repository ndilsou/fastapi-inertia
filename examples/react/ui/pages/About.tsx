import { Link } from "@inertiajs/react";
import { useState } from "react";

export default function AboutPage() {
  const [count, setCount] = useState(0)
  return (
    <div>
      <h1>About Page</h1>
      <p>This is the about page.</p>
      <div className="card">
        <div className="card-body">
        <button className="btn btn-primary" onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        </div>
      </div>
    <Link href="/" className="link">Home</Link>
    </div>
  );
}
