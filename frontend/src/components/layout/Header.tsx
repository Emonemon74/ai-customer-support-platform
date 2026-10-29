import { useEffect, useState } from "react";

import { getCurrentUser, getPublicConfig } from "../../services/auth.service";

export function Header() {
  const [demo, setDemo] = useState<{ ttlHours: number; maxMessages: number } | null>(
    null
  );

  useEffect(() => {
    let cancelled = false;

    async function loadDemoState() {
      try {
        const user = await getCurrentUser();
        if (!user.is_demo) return;

        const config = await getPublicConfig();
        if (!cancelled) {
          setDemo({
            ttlHours: config.demo_ttl_hours,
            maxMessages: config.demo_max_messages,
          });
        }
      } catch {
        // The banner is informational; never block the page on it.
      }
    }

    loadDemoState();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    window.location.href = "/";
  };

  return (
    <header className="border-b border-slate-200 bg-white">
      {demo && (
        <p className="bg-amber-50 px-4 py-2 text-center text-xs text-amber-900 sm:px-6">
          <span className="font-semibold">Demo mode</span> · sample documents are
          loaded · {demo.maxMessages} questions per session · everything is deleted
          after {demo.ttlHours}h
        </p>
      )}

      <div className="flex h-16 items-center justify-between px-4 sm:px-6">
        <h1 className="text-lg font-bold text-slate-900">AI Customer Support</h1>

        <button
          onClick={handleLogout}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
        >
          {demo ? "Exit demo" : "Logout"}
        </button>
      </div>
    </header>
  );
}
