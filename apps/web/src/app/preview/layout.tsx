import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Live Preview | Code Weaver Pro",
  description: "Live preview with WebContainer - Edit code and see changes instantly",
};

export default function PreviewLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Preview page uses a full-screen layout without sidebar
  return <>{children}</>;
}
