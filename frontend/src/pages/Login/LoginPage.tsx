import { useState } from "react";
import axios from "axios";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";

import { login, register } from "../../services/auth.service";

function authErrorMessage(error: unknown, isSignupMode: boolean) {
  const status = axios.isAxiosError(error) ? error.response?.status : undefined;

  if (status === 409) return "An account with this email already exists";
  if (status === 401) return "Invalid email or password";
  if (status === 422) return "Check your details — password needs 8+ characters";
  if (status === 429) return "Too many attempts — try again in a minute";

  return isSignupMode ? "Signup failed" : "Login failed";
}

export function LoginPage() {
  const navigate = useNavigate();

  const [isSignupMode, setIsSignupMode] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    if (isSignupMode && !fullName.trim()) {
      toast.error("Full name is required for signup");
      return;
    }

    try {
      setLoading(true);

      const response = isSignupMode
        ? await register({ full_name: fullName.trim(), email, password })
        : await login({ email, password });

      localStorage.setItem("access_token", response.access_token);

      toast.success(
        isSignupMode ? "Account created successfully" : "Logged in successfully"
      );

      navigate("/dashboard");
    } catch (error) {
      console.error(error);
      toast.error(authErrorMessage(error, isSignupMode));
    } finally {
      setLoading(false);
    }
  };

  function toggleMode() {
    setIsSignupMode((current) => !current);
    setFullName("");
    setEmail("");
    setPassword("");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <h1 className="text-3xl font-bold text-slate-900">
          AI Customer Support
        </h1>

        <p className="mt-2 text-slate-600">
          {isSignupMode
            ? "Create your account to get started"
            : "Login to continue to your workspace"}
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          {isSignupMode && (
            <div>
              <label htmlFor="full-name" className="block text-sm font-medium text-slate-700">
                Full Name
              </label>
              <input
                type="text"
                id="full-name"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Emon Dewan"
                className="mt-1 w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-slate-900"
                required
              />
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-700">
              Email
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="emon@example.com"
              className="mt-1 w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-slate-900"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="password123"
              minLength={isSignupMode ? 8 : undefined}
              className="mt-1 w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-slate-900"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-slate-900 px-4 py-3 font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading
              ? "Please wait..."
              : isSignupMode
              ? "Create Account"
              : "Login"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-600">
          {isSignupMode ? (
            <>
              Already have an account?{" "}
              <button
                type="button"
                onClick={toggleMode}
                className="font-semibold text-slate-900 hover:underline"
              >
                Login
              </button>
            </>
          ) : (
            <>
              Don&apos;t have an account?{" "}
              <button
                type="button"
                onClick={toggleMode}
                className="font-semibold text-slate-900 hover:underline"
              >
                Create account
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}