import { AuthGuard } from '@/components/shared/AuthGuard';

export default function PresentationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AuthGuard>{children}</AuthGuard>;
}
