import { describe, expect, it } from "vitest";

import { protectedPaths } from "@/App";

describe("protection des pages privées", () => {
  it("inclut toutes les familles de pages privées existantes", () => {
    expect(protectedPaths).toEqual([
      "/tableau-de-bord",
      "/entreprises",
      "/formateurs",
      "/dossiers",
    ]);
  });
});
