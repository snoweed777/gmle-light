import { useParams, Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { itemsApi } from "@/api/items";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";

export default function ItemDetailPage() {
  const { spaceId, itemId } = useParams<{ spaceId: string; itemId: string }>();
  const navigate = useNavigate();

  const { data: item, isLoading, error } = useQuery({
    queryKey: ["items", spaceId, itemId],
    queryFn: () => itemsApi.get(spaceId!, itemId!),
    enabled: !!spaceId && !!itemId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !item) {
    return (
      <div>
        <ErrorAlert
          title="Failed to load item"
          message={error instanceof Error ? error.message : "Item not found"}
        />
        <div className="mt-4">
          <Button onClick={() => navigate(`/spaces/${spaceId}/items`)}>
            Back to Items
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Item Details</h1>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => navigate(`/spaces/${spaceId}/items`)}
          >
            Back to Items
          </Button>
          <Link to={`/spaces/${spaceId}`}>
            <Button variant="outline">Space Home</Button>
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Question</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-medium">{item.question}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Metadata</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div>
              <span className="text-sm font-medium text-muted-foreground">ID:</span>
              <p className="text-sm font-mono">{item.id}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-muted-foreground">Domain:</span>
              <p className="text-sm">{item.domain_path}</p>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline">{item.format}</Badge>
              <Badge variant="secondary">Depth {item.depth}</Badge>
              {item.retired ? (
                <Badge variant="secondary">Retired</Badge>
              ) : (
                <Badge variant="default">Active</Badge>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Choices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {item.choices.map((choice, index) => (
                <div
                  key={index}
                  className={`p-2 rounded border ${
                    choice.startsWith(item.answer)
                      ? "bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800"
                      : "bg-muted"
                  }`}
                >
                  <span className="font-medium">{choice}</span>
                </div>
              ))}
            </div>
            <div className="mt-4">
              <p className="text-sm font-medium text-muted-foreground">Correct Answer:</p>
              <Badge variant="default" className="mt-1">
                {item.answer}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Rationale</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {item.rationale.quote && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">
                    Quote:
                  </p>
                  <p className="text-sm italic border-l-4 border-primary pl-4">
                    {item.rationale.quote}
                  </p>
                </div>
              )}
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-1">
                  Explanation:
                </p>
                <p className="text-sm">{item.rationale.explain}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Source</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div>
                <span className="text-sm font-medium text-muted-foreground">Title:</span>
                <p className="text-sm">{item.source.title}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-muted-foreground">Locator:</span>
                <p className="text-sm">{item.source.locator}</p>
              </div>
              {item.source.url && (
                <div>
                  <span className="text-sm font-medium text-muted-foreground">URL:</span>
                  <a
                    href={item.source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary hover:underline"
                  >
                    {item.source.url}
                  </a>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

