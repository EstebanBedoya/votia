import { NextRequest, NextResponse } from "next/server";

export function middleware(req: NextRequest) {
  const gate = req.cookies.get("votia_gate");
  if (!gate) {
    const url = req.nextUrl.clone();
    url.pathname = "/gate";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Apply to all routes EXCEPT:
     *   - /gate and /api/gate  (the gate itself must be reachable without the cookie)
     *   - _next static files and images
     *   - favicon
     */
    "/((?!gate|api/gate|_next/static|_next/image|favicon.ico).*)",
  ],
};
