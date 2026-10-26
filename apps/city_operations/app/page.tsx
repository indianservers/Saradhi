import { Shell } from "@quickbuddy/web-design-system";
export default function Page() {
  return (
    <Shell
      title="Keep the city moving"
      eyebrow="City operations"
      modules={[
        "Live dispatch",
        "Delivery queues",
        "Pilot allocation",
        "Zone performance",
        "Incidents",
      ]}
    />
  );
}
