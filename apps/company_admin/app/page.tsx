import { Shell } from "@quickbuddy/web-design-system";
export default function Page() {
  return (
    <Shell
      title="Control center"
      eyebrow="Company administration"
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
