"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { ArrowUpRight, ShieldCheck } from "lucide-react";

export function Login({ name }: { name: string }) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch("/api/session", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          email: form.get("email"),
          password: form.get("password"),
        }),
      });
      if (!response.ok) {
        const result = await response.json().catch(() => ({}));
        setError(
          typeof result.error?.message === "string"
            ? result.error.message
            : typeof result.detail === "string"
              ? result.detail
              : "Sign-in failed.",
        );
        return;
      }
      router.replace("/workspace");
      router.refresh();
    } catch {
      setError("The sign-in service is unavailable.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login">
      <form className="login-panel" onSubmit={submit}>
        <span className="brandmark">
          <ShieldCheck />
        </span>
        <p className="eyebrow">QUICKBUDDY / {name}</p>
        <h1>Secure workspace access</h1>
        <p>
          Sign in with your Quickbuddy account. Access is checked against your
          current backend role and scope.
        </p>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="username"
          required
          maxLength={254}
        />
        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          maxLength={128}
        />
        {error && (
          <p role="alert" className="login-error">
            {error}
          </p>
        )}
        <button className="qb-primary" type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <a className="backlink" href="/">
          Quickbuddy workspace <ArrowUpRight size={16} />
        </a>
      </form>
    </main>
  );
}
