import type { UserProfileOutSchema } from "../api";

export function formatDate(
  profile: UserProfileOutSchema | null,
  dateString: string | null | undefined,
): string {
  if (!dateString) return "Not available";
  if (!profile) return dateString;
  try {
    const date = new Date(dateString);

    // Use the user's timezone if available
    if (profile.timezone_name) {
      return date.toLocaleString("en-US", {
        timeZone: profile.timezone_name,
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "numeric",
        minute: "numeric",
        hour12: true,
      });
    }

    // Fallback format if no timezone
    return date.toLocaleString();
  } catch (e) {
    return dateString;
  }
}
