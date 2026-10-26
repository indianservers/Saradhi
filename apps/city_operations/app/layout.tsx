import "@quickbuddy/web-design-system/styles.css";
import type { ReactNode } from "react";
export const metadata = {
  title: "Quickbuddy · City operations",
  description: "Quickbuddy city operations workspace",
};
export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
