import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { spacesApi } from "@/api/spaces";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Plus, Loader2 } from "lucide-react";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";

export default function SpacesPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [spaceId, setSpaceId] = useState("");

  const { data: spaces, isLoading, error } = useQuery({
    queryKey: ["spaces"],
    queryFn: () => spacesApi.list(),
  });

  const createSpaceMutation = useMutation({
    mutationFn: (space_id: string) => spacesApi.create({ space_id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["spaces"] });
      setOpen(false);
      setSpaceId("");
    },
  });

  const handleCreate = () => {
    if (spaceId.trim()) {
      createSpaceMutation.mutate(spaceId.trim());
    }
  };

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
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Spaces</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              新規スペース作成
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>新規スペース作成</DialogTitle>
              <DialogDescription>
                新しいスペースを作成します。スペースIDは英数字、ハイフン、アンダースコアのみ使用できます。
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="space-id">スペースID</Label>
                <Input
                  id="space-id"
                  placeholder="例: my-project"
                  value={spaceId}
                  onChange={(e) => setSpaceId(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !createSpaceMutation.isPending) {
                      handleCreate();
                    }
                  }}
                />
              </div>
              {createSpaceMutation.isError && (
                <div className="text-sm text-red-600">
                  ❌ エラー: {(createSpaceMutation.error as Error)?.message || "スペースの作成に失敗しました"}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setOpen(false)}
                disabled={createSpaceMutation.isPending}
              >
                キャンセル
              </Button>
              <Button
                onClick={handleCreate}
                disabled={!spaceId.trim() || createSpaceMutation.isPending}
              >
                {createSpaceMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    作成中...
                  </>
                ) : (
                  "作成"
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
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

