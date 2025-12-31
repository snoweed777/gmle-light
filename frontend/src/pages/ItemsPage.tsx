import { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { itemsApi, ItemResponse } from "@/api/items";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";
import { Search } from "lucide-react";

export default function ItemsPage() {
  const { spaceId } = useParams<{ spaceId: string }>();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [retiredFilter, setRetiredFilter] = useState<boolean | undefined>(
    undefined
  );

  const { data: items, isLoading, error } = useQuery({
    queryKey: ["items", spaceId, retiredFilter],
    queryFn: () => itemsApi.list(spaceId!, retiredFilter),
    enabled: !!spaceId,
  });

  const filteredItems = items?.filter((item) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        item.question.toLowerCase().includes(query) ||
        item.domain_path.toLowerCase().includes(query) ||
        item.id.toLowerCase().includes(query)
      );
    }
    return true;
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
          title="Failed to load items"
          message={error instanceof Error ? error.message : "Unknown error"}
        />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Items</h1>
        <Link to={`/spaces/${spaceId}`}>
          <Button variant="outline">Back</Button>
        </Link>
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by question, domain, or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={retiredFilter === undefined ? "default" : "outline"}
                size="sm"
                onClick={() => setRetiredFilter(undefined)}
              >
                All
              </Button>
              <Button
                variant={retiredFilter === false ? "default" : "outline"}
                size="sm"
                onClick={() => setRetiredFilter(false)}
              >
                Active
              </Button>
              <Button
                variant={retiredFilter === true ? "default" : "outline"}
                size="sm"
                onClick={() => setRetiredFilter(true)}
              >
                Retired
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Items ({filteredItems?.length || 0} / {items?.length || 0})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredItems && filteredItems.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Question</TableHead>
                  <TableHead>Domain</TableHead>
                  <TableHead>Format</TableHead>
                  <TableHead>Depth</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map((item) => (
                  <TableRow
                    key={item.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/spaces/${spaceId}/items/${item.id}`)}
                  >
                    <TableCell className="max-w-md">
                      <p className="truncate font-medium">{item.question}</p>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {item.domain_path}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{item.format}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">Depth {item.depth}</Badge>
                    </TableCell>
                    <TableCell>
                      {item.retired ? (
                        <Badge variant="secondary">Retired</Badge>
                      ) : (
                        <Badge variant="default">Active</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/spaces/${spaceId}/items/${item.id}`);
                        }}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <div className="space-y-2">
                <p className="text-lg font-medium text-muted-foreground">
                  {searchQuery || retiredFilter !== undefined
                    ? "No items found matching your filters"
                    : "まだアイテムがありません"}
                </p>
                {!searchQuery && retiredFilter === undefined && (
                  <p className="text-sm text-muted-foreground">
                    Run を実行して MCQ を生成してください。
                    <br />
                    <Link
                      to={`/spaces/${spaceId}/runs`}
                      className="text-primary hover:underline"
                    >
                      Runs 画面
                    </Link>
                    から実行できます。
                  </p>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
