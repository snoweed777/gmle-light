import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  let d: Date;
  if (typeof date === "string") {
    // Ensure UTC interpretation if timezone info is missing
    const dateStr = date.endsWith("Z") || date.includes("+") || date.includes("-", 10)
      ? date
      : `${date}Z`; // Add Z to indicate UTC if no timezone info
    d = new Date(dateStr);
  } else {
    d = date;
  }
  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "Asia/Tokyo",
  }).format(d);
}

