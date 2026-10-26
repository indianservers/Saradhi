import { Shell } from "@quickbuddy/web-design-system";
export default function Page() {
  return (
    <Shell
      title="Every conversation matters"
      eyebrow="Support console"
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
