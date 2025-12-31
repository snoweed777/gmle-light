import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { spacesApi } from "@/api/spaces";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";

export default function SpacesPage() {
  const { data: spaces, isLoading, error } = useQuery({
    queryKey: ["spaces"],
    queryFn: () => spacesApi.list(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <ErrorAlert
          title="Failed to load spaces"
          message={error instanceof Error ? error.message : "Unknown error"}
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Spaces</h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {spaces?.map((space) => (
          <Link key={space.space_id} to={`/spaces/${space.space_id}`}>
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle>{space.space_id}</CardTitle>
                <CardDescription>{space.deck_bank}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">
                  <p>Data: {space.data_root}</p>
                  <p>Sources: {space.sources_root}</p>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

