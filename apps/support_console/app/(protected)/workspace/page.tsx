import { Shell } from "@quickbuddy/web-design-system";
export default function Page() {
  return (
    <Shell
      title="Every conversation matters"
      eyebrow="Authorized workspace"
      modules={[
        "Tickets",
        "Order assistance",
        "Refund approvals",
        "Complaints",
        "Escalations",
      ]}
    />
  );
}
