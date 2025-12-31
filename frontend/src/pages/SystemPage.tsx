import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { systemApi, ServiceStatus } from "@/api/system";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";
import { Play, Square, RefreshCw, RotateCw, Server, AlertCircle, CheckCircle2, XCircle } from "lucide-react";
import { useEffect } from "react";

const SERVICE_NAMES = ["anki", "api", "gui"] as const;
const SERVICE_DISPLAY_NAMES: Record<string, string> = {
  anki: "AnkiConnect",
  api: "REST API",
  gui: "GUI Server",
};

const SERVICE_DESCRIPTIONS: Record<string, string> = {
  anki: "Ankiヘッドレスモード（AnkiConnect）",
  api: "REST APIサーバー（FastAPI/uvicorn）",
  gui: "GUI開発サーバー（Vite）",
};

function StatusBadge({ status }: { status: ServiceStatus["status"] }) {
  switch (status) {
    case "running":
      return (
        <Badge variant="default" className="bg-green-500">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          起動中
        </Badge>
      );
    case "stopped":
      return (
        <Badge variant="secondary">
          <XCircle className="h-3 w-3 mr-1" />
          停止中
        </Badge>
      );
    case "warning":
      return (
        <Badge variant="outline" className="border-yellow-500 text-yellow-700">
          <AlertCircle className="h-3 w-3 mr-1" />
          警告
        </Badge>
      );
    case "error":
      return (
        <Badge variant="destructive">
          <AlertCircle className="h-3 w-3 mr-1" />
          エラー
        </Badge>
      );
    default:
      return <Badge variant="secondary">不明</Badge>;
  }
}

export default function SystemPage() {
  const queryClient = useQueryClient();

  const { data: systemStatus, isLoading, error, refetch } = useQuery({
    queryKey: ["system", "status"],
    queryFn: () => systemApi.getStatus(),
    refetchInterval: 5000, // 5秒ごとに自動更新
  });

  const startMutation = useMutation({
    mutationFn: (serviceName: string) => systemApi.startService(serviceName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system", "status"] });
      // 起動には時間がかかるため、少し待ってから再取得
      setTimeout(() => {
        refetch();
      }, 2000);
    },
    onError: (error: any) => {
      // エラーをコンソールに出力（デバッグ用）
      console.error("Failed to start service:", error);
      // エラーメッセージをアラートで表示
      const errorMessage = error?.response?.data?.detail || error?.message || "Failed to start service";
      alert(`起動に失敗しました: ${errorMessage}`);
    },
  });

  const stopMutation = useMutation({
    mutationFn: (serviceName: string) => systemApi.stopService(serviceName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system", "status"] });
      setTimeout(() => {
        refetch();
      }, 1000);
    },
  });

  const restartMutation = useMutation({
    mutationFn: (serviceName: string) => systemApi.restartService(serviceName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system", "status"] });
      // 再起動には時間がかかるため、少し待ってから再取得
      setTimeout(() => {
        refetch();
      }, 3000);
    },
  });

  const handleStart = (serviceName: string) => {
    if (confirm(`${SERVICE_DISPLAY_NAMES[serviceName]}を起動しますか？`)) {
      startMutation.mutate(serviceName);
    }
  };

  const handleStop = (serviceName: string) => {
    if (confirm(`${SERVICE_DISPLAY_NAMES[serviceName]}を停止しますか？`)) {
      stopMutation.mutate(serviceName);
    }
  };

  const handleRestart = (serviceName: string) => {
    if (confirm(`${SERVICE_DISPLAY_NAMES[serviceName]}を再起動しますか？`)) {
      restartMutation.mutate(serviceName);
    }
  };

  if (isLoading && !systemStatus) {
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
          title="システム状態の取得に失敗しました"
          message={error instanceof Error ? error.message : "Unknown error"}
        />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">システム管理</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          更新
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {SERVICE_NAMES.map((serviceName) => {
          const service = systemStatus?.services[serviceName];
          if (!service) {
            return null;
          }

          const isRunning = service.status === "running";
          const isStopped = service.status === "stopped";
          const isLoading = startMutation.isPending || stopMutation.isPending || restartMutation.isPending;

          return (
            <Card key={serviceName} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Server className="h-5 w-5 text-muted-foreground" />
                    <CardTitle>{SERVICE_DISPLAY_NAMES[serviceName]}</CardTitle>
                  </div>
                  <StatusBadge status={service.status} />
                </div>
                <CardDescription>{SERVICE_DESCRIPTIONS[serviceName]}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {service.pid && (
                    <div className="text-sm text-muted-foreground">
                      <span className="font-medium">PID:</span> {service.pid}
                    </div>
                  )}
                  {service.port && (
                    <div className="text-sm text-muted-foreground">
                      <span className="font-medium">Port:</span> {service.port}
                    </div>
                  )}
                  {service.warning && (
                    <div className="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
                      ⚠️ {service.warning}
                    </div>
                  )}
                  {service.error && (
                    <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                      ❌ {service.error}
                    </div>
                  )}
                  {service.message && (
                    <div className="text-sm text-blue-600 bg-blue-50 p-2 rounded">
                      ℹ️ {service.message}
                    </div>
                  )}
                  <div className="flex gap-2 pt-2">
                    <Button
                      size="sm"
                      variant="default"
                      onClick={() => handleStart(serviceName)}
                      disabled={isRunning || isLoading}
                      className="flex-1"
                    >
                      <Play className="h-4 w-4 mr-1" />
                      起動
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleStop(serviceName)}
                      disabled={isStopped || isLoading}
                      className="flex-1"
                    >
                      <Square className="h-4 w-4 mr-1" />
                      停止
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRestart(serviceName)}
                      disabled={isStopped || isLoading}
                      className="flex-1"
                    >
                      <RotateCw className="h-4 w-4 mr-1" />
                      再起動
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="mt-6 p-4 bg-muted rounded-lg">
        <p className="text-sm text-muted-foreground">
          💡 システム状態は5秒ごとに自動更新されます。手動で更新する場合は「更新」ボタンをクリックしてください。
        </p>
      </div>
    </div>
  );
}

