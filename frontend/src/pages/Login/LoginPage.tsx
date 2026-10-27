import { useEffect, useState } from "react";
import axios from "axios";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";

import {
  getPublicConfig,
  login,
  register,
  startDemo,
} from "../../services/auth.service";

import { OPEN_CONVERSATION_KEY } from "../../utils/storageKeys";

function authErrorMessage(
  error: unknown,
  isSignupMode: boolean,
  fallback?: string
) {
  const status = axios.isAxiosError(error) ? error.response?.status : undefined;

  if (status === 409) return "An account with this email already exists";
  if (status === 401) return "Invalid email or password";
  if (status === 422) return "Check your details — password needs 8+ characters";
  if (status === 429) return "Too many attempts — try again in a minute";

  return fallback ?? (isSignupMode ? "Signup failed" : "Login failed");
}

export function LoginPage() {
  const navigate = useNavigate();

  const [isSignupMode, setIsSignupMode] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [demoEnabled, setDemoEnabled] = useState(false);

  useEffect(() => {
    getPublicConfig()
      .then((config) => setDemoEnabled(config.demo_enabled))
      .catch(() => setDemoEnabled(false));
  }, []);

  async function handleDemo() {
    try {
      setLoading(true);

      const session = await startDemo();

      localStorage.setItem("access_token", session.access_token);
      sessionStorage.setItem(
        OPEN_CONVERSATION_KEY,
        String(session.conversation_id)
      );

      navigate("/dashboard");
    } catch (error) {
      console.error(error);
      toast.error(authErrorMessage(error, false, "Could not start the demo"));
    } finally {
      setLoading(false);
    }
  }

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

        {demoEnabled && (
          <div className="mt-6">
            <button
              type="button"
              onClick={handleDemo}
              disabled={loading}
              className="w-full rounded-lg border-2 border-slate-900 px-4 py-3 font-semibold text-slate-900 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-70"
            >
              Try the demo — no signup
            </button>
            <p className="mt-2 text-center text-xs text-slate-500">
              Opens a chat with sample support documents already loaded.
            </p>
            <div className="mt-6 flex items-center gap-3 text-xs text-slate-400">
              <span className="h-px flex-1 bg-slate-200" />
              or use an account
              <span className="h-px flex-1 bg-slate-200" />
            </div>
          </div>
        )}

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