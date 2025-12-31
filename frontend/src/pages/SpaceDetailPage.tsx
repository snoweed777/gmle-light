import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { spacesApi } from "@/api/spaces";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";
import { CheckCircle2, XCircle, Loader2, AlertCircle } from "lucide-react";

export default function SpaceDetailPage() {
  const { spaceId } = useParams<{ spaceId: string }>();
  const queryClient = useQueryClient();

  const { data: space, isLoading, error } = useQuery({
    queryKey: ["spaces", spaceId],
    queryFn: () => spacesApi.get(spaceId!),
    enabled: !!spaceId,
  });

  const { data: ankiStatus, isLoading: ankiStatusLoading } = useQuery({
    queryKey: ["spaces", spaceId, "anki-status"],
    queryFn: () => spacesApi.getAnkiStatus(spaceId!),
    enabled: !!spaceId,
    refetchInterval: 10000, // 10秒ごとに更新
  });

  const initializeMutation = useMutation({
    mutationFn: () => spacesApi.initializeSpace(spaceId!),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["spaces", spaceId, "anki-status"],
      });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !space) {
    return (
      <div>
        <ErrorAlert
          title="Failed to load space"
          message={error instanceof Error ? error.message : "Space not found"}
        />
        <div className="mt-4">
          <Link to="/">
            <Button variant="outline">Back to Spaces</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">{space.space_id}</h1>
        <Link to="/">
          <Button variant="outline">Back to Spaces</Button>
        </Link>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Space Information</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Deck Bank
                </dt>
                <dd className="text-sm">{space.deck_bank}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Data Root
                </dt>
                <dd className="text-sm">{space.data_root}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Sources Root
                </dt>
                <dd className="text-sm">{space.sources_root}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Anki Resources</CardTitle>
            <CardDescription>
              Note Type と Deck の存在状態を確認します
            </CardDescription>
          </CardHeader>
          <CardContent>
            {ankiStatusLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            ) : ankiStatus ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Note Type</span>
                    {ankiStatus.note_type_exists ? (
                      <Badge variant="default" className="bg-green-600">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        存在
                      </Badge>
                    ) : (
                      <Badge variant="destructive">
                        <XCircle className="h-3 w-3 mr-1" />
                        未作成
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground font-mono">
                    {ankiStatus.note_type_name}
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Deck</span>
                    {ankiStatus.deck_exists ? (
                      <Badge variant="default" className="bg-green-600">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        存在
                      </Badge>
                    ) : (
                      <Badge variant="destructive">
                        <XCircle className="h-3 w-3 mr-1" />
                        未作成
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground font-mono">
                    {ankiStatus.deck_name}
                  </p>
                </div>

                {ankiStatus.note_type_exists && ankiStatus.deck_exists ? (
                  <div className="pt-2 p-3 bg-green-50 border border-green-200 rounded-md">
                    <p className="text-sm text-green-800 font-medium">
                      ✓ すべてのリソースが準備完了しています
                    </p>
                  </div>
                ) : (
                  <div className="pt-2 space-y-2">
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                      <p className="text-sm text-yellow-800 font-medium mb-1">
                        <AlertCircle className="h-4 w-4 inline mr-1" />
                        初期化が必要です
                      </p>
                      <p className="text-xs text-yellow-700">
                        未作成のリソースを自動的に作成します
                      </p>
                    </div>
                    <Button
                      onClick={() => initializeMutation.mutate()}
                      disabled={initializeMutation.isPending}
                      className="w-full"
                    >
                      {initializeMutation.isPending ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Initializing...
                        </>
                      ) : (
                        "Initialize Space"
                      )}
                    </Button>
                  </div>
                )}

                {initializeMutation.isSuccess && (
                  <div className="pt-2 p-3 bg-green-50 border border-green-200 rounded-md">
                    <p className="text-sm text-green-800 font-medium">
                      ✓ {initializeMutation.data.message}
                    </p>
                  </div>
                )}

                {initializeMutation.isError && (
                  <div className="pt-2">
                    <ErrorAlert
                      title="初期化に失敗しました"
                      message={
                        initializeMutation.error instanceof Error
                          ? initializeMutation.error.message
                          : "Unknown error"
                      }
                    />
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                状態を取得できませんでした
              </p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Link to={`/spaces/${spaceId}/ingest`}>
              <Button className="w-full">Upload & Ingest</Button>
            </Link>
            <Link to={`/spaces/${spaceId}/runs`}>
              <Button className="w-full" variant="outline">
                View Runs
              </Button>
            </Link>
            <Link to={`/spaces/${spaceId}/items`}>
              <Button className="w-full" variant="outline">
                View Items
              </Button>
            </Link>
            <Link to={`/spaces/${spaceId}/config`}>
              <Button className="w-full" variant="outline">
                View Config
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

