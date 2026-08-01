import { describe, expect, it } from "vitest";

import { config } from "@/proxy";

describe("protection des pages privées", () => {
  it("inclut toutes les familles de pages privées existantes", () => {
    expect(config.matcher).toEqual([
      "/tableau-de-bord/:path*",
      "/entreprises/:path*",
      "/dossiers/:path*",
      "/formateurs/:path*",
    ]);
  });
});
