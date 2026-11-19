import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function LoginFormSkeleton() {
  return (
    <Card className="w-full max-w-md border-border/80 shadow-sm">
      <CardHeader>
        <CardTitle className="text-xl">College ERP</CardTitle>
        <CardDescription>Loading sign-in…</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4" aria-hidden>
          <div className="h-16 animate-pulse rounded-lg bg-muted" />
          <div className="h-16 animate-pulse rounded-lg bg-muted" />
          <div className="h-16 animate-pulse rounded-lg bg-muted" />
          <div className="h-8 animate-pulse rounded-lg bg-muted" />
        </div>
      </CardContent>
    </Card>
  );
}