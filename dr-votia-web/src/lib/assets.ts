/**
 * Static art assets live in the public Supabase Storage bucket `art`, not in
 * /public, so they are served from the CDN and never gated by the access-code
 * middleware. The project URL is centralized here via NEXT_PUBLIC_SUPABASE_URL
 * so the project ref isn't hardcoded across components and CSS.
 */
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";

/** Public URL for a file in the `art` storage bucket (e.g. "guacamayo.png"). */
export function artUrl(file: string): string {
  return `${SUPABASE_URL}/storage/v1/object/public/art/${file}`;
}
