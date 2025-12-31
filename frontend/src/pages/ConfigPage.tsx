import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { configApi, ConfigUpdateRequest } from "@/api/config";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";
import { Save, Loader2 } from "lucide-react";

export default function ConfigPage() {
  const { spaceId } = useParams<{ spaceId: string }>();
  const queryClient = useQueryClient();
  const [params, setParams] = useState<Record<string, unknown>>({});

  const { data: config, isLoading, error } = useQuery({
    queryKey: ["config", spaceId],
    queryFn: () => configApi.get(spaceId!),
    enabled: !!spaceId,
  });

  useEffect(() => {
    if (config?.params) {
      setParams(config.params);
    }
  }, [config]);

  const updateMutation = useMutation({
    mutationFn: (request: ConfigUpdateRequest) =>
      configApi.update(spaceId!, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["config", spaceId] });
    },
  });

  const handleSave = () => {
    updateMutation.mutate({ params });
  };

  const handleParamChange = (key: string, value: string) => {
    setParams((prev) => ({
      ...prev,
      [key]: isNaN(Number(value)) ? value : Number(value),
    }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !config) {
    return (
      <div>
        <ErrorAlert
          title="Failed to load config"
          message={error instanceof Error ? error.message : "Unknown error"}
        />
        <div className="mt-4">
          <Link to={`/spaces/${spaceId}`}>
            <Button variant="outline">Back</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Config</h1>
        <div className="flex gap-2">
          <Link to={`/spaces/${spaceId}`}>
            <Button variant="outline">Back</Button>
          </Link>
          <Button
            onClick={handleSave}
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save
              </>
            )}
          </Button>
        </div>
      </div>

      {updateMutation.isError && (
        <ErrorAlert
          title="Failed to update config"
          message={updateMutation.error?.message || "Unknown error"}
        />
      )}

      {updateMutation.isSuccess && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md text-sm text-green-800 dark:bg-green-950 dark:border-green-800 dark:text-green-200">
          Config updated successfully
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(params).map(([key, value]) => (
              <div key={key}>
                <label className="text-sm font-medium mb-1 block">{key}</label>
                {typeof value === "number" ? (
                  <Input
                    type="number"
                    value={value}
                    onChange={(e) => handleParamChange(key, e.target.value)}
                  />
                ) : typeof value === "boolean" ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={(e) =>
                        setParams((prev) => ({ ...prev, [key]: e.target.checked }))
                      }
                    />
                    <span className="text-sm">{value ? "True" : "False"}</span>
                  </div>
                ) : (
                  <Input
                    value={String(value)}
                    onChange={(e) => handleParamChange(key, e.target.value)}
                  />
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Paths (Read-only)</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm bg-muted p-4 rounded-md overflow-auto">
              {JSON.stringify(config.paths, null, 2)}
            </pre>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
