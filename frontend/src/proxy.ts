import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export function proxy(request: NextRequest) {
  const accessToken = request.cookies.get("access_token");

  if (!accessToken) {
    return NextResponse.redirect(new URL("/connexion", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/tableau-de-bord/:path*",
    "/entreprises/:path*",
    "/dossiers/:path*",
    "/formateurs/:path*",
  ],
};
