import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError, type AxiosResponse } from "axios";
import toast from "react-hot-toast";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as authService from "../../services/auth.service";
import { OPEN_CONVERSATION_KEY } from "../../utils/storageKeys";
import { LoginPage } from "./LoginPage";

const navigate = vi.fn();

vi.mock("react-router-dom", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react-router-dom")>()),
  useNavigate: () => navigate,
}));

vi.mock("../../services/auth.service");

function renderPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>
  );
}

function httpError(status: number) {
  return new AxiosError("failed", "ERR_BAD_REQUEST", undefined, undefined, {
    status,
  } as AxiosResponse);
}

const config = (demoEnabled: boolean) => ({
  demo_enabled: demoEnabled,
  demo_max_messages: 30,
  demo_ttl_hours: 24,
});

beforeEach(() => {
  navigate.mockClear();
  sessionStorage.clear();
  vi.mocked(authService.getPublicConfig).mockResolvedValue(config(false));
  vi.spyOn(console, "error").mockImplementation(() => {});
  vi.spyOn(toast, "error").mockImplementation(() => "");
  vi.spyOn(toast, "success").mockImplementation(() => "");
});

describe("LoginPage", () => {
  it("logs in, stores the token and opens the dashboard", async () => {
    vi.mocked(authService.login).mockResolvedValue({
      access_token: "tok",
      token_type: "bearer",
    });
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Email"), "a@example.com");
    await user.type(screen.getByLabelText("Password"), "secret-pw");
    await user.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() => expect(navigate).toHaveBeenCalledWith("/dashboard"));
    expect(authService.login).toHaveBeenCalledWith({
      email: "a@example.com",
      password: "secret-pw",
    });
    expect(localStorage.getItem("access_token")).toBe("tok");
  });

  it("registers with a trimmed full name in signup mode", async () => {
    vi.mocked(authService.register).mockResolvedValue({
      access_token: "new-tok",
      token_type: "bearer",
    });
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Create account" }));
    await user.type(screen.getByLabelText("Full Name"), "  Ada Lovelace ");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Password"), "long-enough-pw");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() => expect(navigate).toHaveBeenCalledWith("/dashboard"));
    expect(authService.register).toHaveBeenCalledWith({
      full_name: "Ada Lovelace",
      email: "ada@example.com",
      password: "long-enough-pw",
    });
    expect(authService.login).not.toHaveBeenCalled();
    expect(localStorage.getItem("access_token")).toBe("new-tok");
  });

  it.each([
    [401, "Invalid email or password"],
    [429, "Too many attempts — try again in a minute"],
  ])("shows a specific message for a %i on login", async (status, message) => {
    vi.mocked(authService.login).mockRejectedValue(httpError(status));
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Email"), "a@example.com");
    await user.type(screen.getByLabelText("Password"), "secret-pw");
    await user.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith(message));
    expect(navigate).not.toHaveBeenCalled();
    expect(localStorage.getItem("access_token")).toBeNull();
  });

  it("tells the user when the email is already registered", async () => {
    vi.mocked(authService.register).mockRejectedValue(httpError(409));
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Create account" }));
    await user.type(screen.getByLabelText("Full Name"), "Ada");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Password"), "long-enough-pw");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith(
        "An account with this email already exists"
      )
    );
  });

  it("hides the demo button when the demo is disabled", async () => {
    renderPage();

    await screen.findByRole("button", { name: "Login" });
    expect(
      screen.queryByRole("button", { name: /try the demo/i })
    ).not.toBeInTheDocument();
  });

  it("starts a demo session and opens its sample conversation", async () => {
    vi.mocked(authService.getPublicConfig).mockResolvedValue(config(true));
    vi.mocked(authService.startDemo).mockResolvedValue({
      access_token: "guest-tok",
      token_type: "bearer",
      conversation_id: 42,
    });
    const user = userEvent.setup();
    renderPage();

    await user.click(
      await screen.findByRole("button", { name: /try the demo/i })
    );

    await waitFor(() => expect(navigate).toHaveBeenCalledWith("/dashboard"));
    expect(localStorage.getItem("access_token")).toBe("guest-tok");
    expect(sessionStorage.getItem(OPEN_CONVERSATION_KEY)).toBe("42");
    expect(authService.login).not.toHaveBeenCalled();
  });

  it("explains a rate-limited demo start", async () => {
    vi.mocked(authService.getPublicConfig).mockResolvedValue(config(true));
    vi.mocked(authService.startDemo).mockRejectedValue(httpError(429));
    const user = userEvent.setup();
    renderPage();

    await user.click(
      await screen.findByRole("button", { name: /try the demo/i })
    );

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith(
        "Too many attempts — try again in a minute"
      )
    );
    expect(navigate).not.toHaveBeenCalled();
  });
});
