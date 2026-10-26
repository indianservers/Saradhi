import { Shell } from "@quickbuddy/web-design-system";
export default function Page() {
  return (
    <Shell
      title="Control center"
      eyebrow="Authorized workspace"
      modules={[
        "Merchants",
        "Customers & pilots",
        "Cities & categories",
        "Finance",
        "AI operations",
      ]}
    />
  );
}
