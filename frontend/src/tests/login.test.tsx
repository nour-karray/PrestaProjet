import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import LoginPage from "@/app/connexion/page";
import { renderWithQueryClient } from "@/tests/test-utils";

const { replaceMock } = vi.hoisted(() => ({
  replaceMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: replaceMock,
  }),
}));

afterEach(() => {
  replaceMock.mockReset();
  vi.unstubAllGlobals();
});

describe("Page de connexion", () => {
  it("affiche les erreurs de validation en français", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<LoginPage />);

    await user.click(screen.getByRole("button", { name: "Se connecter" }));

    expect(
      await screen.findByText("Saisissez une adresse email valide."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Le mot de passe doit contenir au moins 8 caractères."),
    ).toBeInTheDocument();
  });

  it("redirige vers le tableau de bord après connexion", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            administrator: {
              id: "a13d9c48-52e5-4ec0-8720-413853635195",
              full_name: "Administrateur",
              email: "admin@formation.local",
              is_active: true,
              created_at: "2026-07-24T12:00:00Z",
              last_login_at: "2026-07-24T12:00:00Z",
            },
            message: "Connexion réussie.",
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      ),
    );
    renderWithQueryClient(<LoginPage />);

    await user.type(
      screen.getByLabelText("Adresse email"),
      "admin@formation.local",
    );
    await user.type(screen.getByLabelText("Mot de passe"), "Admin123!");
    await user.click(screen.getByRole("button", { name: "Se connecter" }));

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/tableau-de-bord");
    });
  });
});

