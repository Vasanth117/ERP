import { CampusDetailView } from "@/features/college-admin/components/institution/institution-views";

type Props = { params: Promise<{ campusId: string }> };

export default async function Page({ params }: Props) {
  const { campusId } = await params;
  return <CampusDetailView campusId={campusId} />;
}