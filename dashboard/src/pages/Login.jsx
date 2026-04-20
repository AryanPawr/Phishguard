import { useState } from "react";
import { login } from "../services/api.js";

export default function Login({ onLogin, shield }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(username, password);
      onLogin();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-neutral-100 text-ink">
      <section className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-5">
        <div className="mb-8 flex items-center gap-3">
          <img src={shield} alt="PhishGuard shield" className="h-14 w-14 rounded" />
          <div>
            <h1 className="text-2xl font-bold">PhishGuard</h1>
            <p className="text-sm text-neutral-600">Admin console</p>
          </div>
        </div>

        <form onSubmit={submit} className="rounded-lg border border-line bg-paper p-5">
          <label className="block text-sm font-medium" htmlFor="username">
            Username
          </label>
          <input
            id="username"
            className="mt-2 w-full rounded-md border border-line px-3 py-2 outline-none focus:border-cyanmark"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />

          <label className="mt-4 block text-sm font-medium" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            className="mt-2 w-full rounded-md border border-line px-3 py-2 outline-none focus:border-cyanmark"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          {error ? <p className="mt-4 text-sm text-alert">{error}</p> : null}

          <button
            className="mt-5 w-full rounded-md bg-ink px-4 py-2 font-semibold text-white disabled:opacity-60"
            disabled={loading}
          >
            {loading ? "Signing in" : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

