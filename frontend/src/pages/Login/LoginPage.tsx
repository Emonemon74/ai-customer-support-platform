import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { authenticate } from "../../services/auth.service";

export function LoginPage() {
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    try {
      setLoading(true);

      const response = await authenticate({
        full_name: fullName || undefined,
        email,
        password,
      });

      localStorage.setItem("access_token", response.access_token);

      navigate("/dashboard");
    } catch (error) {
      console.error(error);
      alert("Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <h1 className="text-3xl font-bold text-slate-900">
          AI Customer Support
        </h1>

        <p className="mt-2 text-slate-600">
          Login or create your account
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Full Name
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="Only required for signup"
              className="mt-1 w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-slate-900"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="emon@example.com"
              className="mt-1 w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-slate-900"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="password123"
              className="mt-1 w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-slate-900"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-slate-900 px-4 py-3 font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? "Please wait..." : "Continue"}
          </button>
        </form>
      </div>
    </div>
  );
}