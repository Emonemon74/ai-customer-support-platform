import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as authService from "../../services/auth.service";
import { Header } from "./Header";

vi.mock("../../services/auth.service");

const user = (isDemo: boolean) => ({
  id: 1,
  full_name: "Test",
  email: "t@example.com",
  is_demo: isDemo,
});

beforeEach(() => {
  vi.mocked(authService.getPublicConfig).mockResolvedValue({
    demo_enabled: true,
    demo_max_messages: 30,
    demo_ttl_hours: 24,
  });
});

describe("Header", () => {
  it("tells guests they are in demo mode and how long data lives", async () => {
    vi.mocked(authService.getCurrentUser).mockResolvedValue(user(true));
    render(<Header />);

    expect(await screen.findByText(/demo mode/i)).toBeInTheDocument();
    expect(screen.getByText(/30 questions per session/)).toBeInTheDocument();
    expect(screen.getByText(/deleted/)).toHaveTextContent("24h");
    expect(screen.getByRole("button", { name: "Exit demo" })).toBeInTheDocument();
  });

  it("shows a normal header for a regular account", async () => {
    vi.mocked(authService.getCurrentUser).mockResolvedValue(user(false));
    render(<Header />);

    expect(await screen.findByRole("button", { name: "Logout" })).toBeInTheDocument();
    expect(screen.queryByText(/demo mode/i)).not.toBeInTheDocument();
  });
});
