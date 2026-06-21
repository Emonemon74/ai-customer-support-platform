import { useState } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";

import { authenticate } from "../../services/auth.service";

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

      const response = await authenticate({
        full_name: isSignupMode ? fullName : undefined,
        email,
        password,
      });

      localStorage.setItem("access_token", response.access_token);

      toast.success(
        isSignupMode ? "Account created successfully" : "Logged in successfully"
      );

      navigate("/dashboard");
    } catch (error) {
      console.error(error);
      toast.error(
        isSignupMode ? "Signup failed" : "Login failed"
      );
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
              <label className="block text-sm font-medium text-slate-700">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Emon Dewan"
                className="mt-1 w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-slate-900"
                required
              />
            </div>
          )}

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