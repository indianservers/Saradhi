import { AdminControlTower } from "@quickbuddy/web-design-system";
import { redirect } from "next/navigation";

export default function Page() {
  if (process.env.NODE_ENV === "production") redirect("/workspace");
  return <AdminControlTower />;
}
