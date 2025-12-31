import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { runsApi, RunResponse } from "@/api/runs";
import { systemApi, RateLimitStatus, ApiKeyStatus } from "@/api/system";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useRunPolling } from "@/hooks/useRunPolling";
import { formatDate } from "@/lib/utils";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";
import { AlertCircle, CheckCircle2, Loader2, XCircle } from "lucide-react";

export default function RunsPage() {
  const { spaceId } = useParams<{ spaceId: string }>();
  const queryClient = useQueryClient();
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);

  // システム状態を取得
  const { data: systemStatus } = useQuery({
    queryKey: ["system", "status"],
    queryFn: () => systemApi.getStatus(),
    refetchInterval: 5000, // 5秒ごとに更新
  });

  // 必要なサービスが起動しているかチェック
  const requiredServices = ["anki", "api"] as const;
  const stoppedServices = requiredServices.filter(
    (serviceName) => systemStatus?.services[serviceName]?.status !== "running"
  );
  const canCreateRun = stoppedServices.length === 0;

  const createRunMutation = useMutation({
    mutationFn: () => runsApi.create(spaceId!, { mode: "normal" }),
    onSuccess: (data) => {
      setCurrentRunId(data.run_id);
      queryClient.invalidateQueries({ queryKey: ["runs", spaceId] });
    },
  });

  const { data: currentRun, isLoading: isPolling } = useRunPolling({
    spaceId: spaceId!,
    runId: currentRunId,
    enabled: !!currentRunId,
  });

  // Run履歴を取得
  const { data: runHistory } = useQuery({
    queryKey: ["runs", spaceId],
    queryFn: () => runsApi.list(spaceId!),
    enabled: !!spaceId,
    refetchInterval: 10000, // 10秒ごとに更新
  });

  // レート制限状態を取得（Run実行中のみ）
  const { data: rateLimitStatus } = useQuery({
    queryKey: ["rate-limit-status"],
    queryFn: () => systemApi.getRateLimitStatus(),
    enabled: currentRun?.status === "running",
    refetchInterval: currentRun?.status === "running" ? 2000 : false, // 2秒ごとに更新
  });

  // APIキー状態を取得
  const { data: apiKeyStatus } = useQuery({
    queryKey: ["api-key-status"],
    queryFn: () => systemApi.getApiKeyStatus(),
    enabled: !!spaceId && !currentRunId,
    refetchInterval: 10000, // 10秒ごとに更新
  });

  // 前提条件チェック
  const { data: prerequisites } = useQuery({
    queryKey: ["prerequisites", spaceId],
    queryFn: () => runsApi.checkPrerequisites(spaceId!),
    enabled: !!spaceId && !currentRunId,
    refetchInterval: 10000, // 10秒ごとに更新
  });

  const handleCreateRun = () => {
    createRunMutation.mutate();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
        return (
          <Badge variant="default" className="flex items-center gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            Running
          </Badge>
        );
      case "completed":
        return (
          <Badge variant="default" className="flex items-center gap-1 bg-green-600">
            <CheckCircle2 className="h-3 w-3" />
            Completed
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive" className="flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
      default:
        return <Badge>{status}</Badge>;
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Runs</h1>
        <div className="flex gap-2">
          <Link to={`/spaces/${spaceId}`}>
            <Button variant="outline">Back</Button>
          </Link>
          <Button
            onClick={handleCreateRun}
            disabled={
              createRunMutation.isPending ||
              !!currentRunId ||
              !canCreateRun ||
              (prerequisites && !prerequisites.all_passed) ||
              (apiKeyStatus && (!apiKeyStatus.valid || !apiKeyStatus.has_quota))
            }
          >
            {createRunMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              "Create Run"
            )}
          </Button>
        </div>
      </div>

      {createRunMutation.isError && (
        <ErrorAlert
          title="Failed to create run"
          message={createRunMutation.error?.message || "Unknown error"}
        />
      )}

      {/* APIキー状態表示 */}
      {apiKeyStatus && (
        <Card className={`mb-6 ${
          !apiKeyStatus.valid || !apiKeyStatus.has_quota
            ? "border-red-200 bg-red-50"
            : apiKeyStatus.key_type === "trial"
            ? "border-yellow-200 bg-yellow-50"
            : "border-blue-200 bg-blue-50"
        }`}>
          <CardHeader>
            <CardTitle className={`flex items-center gap-2 ${
              !apiKeyStatus.valid || !apiKeyStatus.has_quota
                ? "text-red-800"
                : apiKeyStatus.key_type === "trial"
                ? "text-yellow-800"
                : "text-blue-800"
            }`}>
              {!apiKeyStatus.valid || !apiKeyStatus.has_quota ? (
                <XCircle className="h-5 w-5" />
              ) : (
                <AlertCircle className="h-5 w-5" />
              )}
              APIキー状態
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">状態</span>
                <Badge
                  variant={
                    !apiKeyStatus.valid || !apiKeyStatus.has_quota
                      ? "destructive"
                      : "default"
                  }
                >
                  {!apiKeyStatus.valid
                    ? "無効"
                    : !apiKeyStatus.has_quota
                    ? "クォータなし"
                    : apiKeyStatus.key_type === "trial"
                    ? "Trial (制限あり)"
                    : "利用可能"}
                </Badge>
              </div>
              {apiKeyStatus.key_type && (
                <div className="text-sm">
                  <span className="font-medium">タイプ:</span>{" "}
                  {apiKeyStatus.key_type === "trial" ? "Trial" : "Production"}
                </div>
              )}
              {apiKeyStatus.error && (
                <div className="text-sm text-red-700">
                  <span className="font-medium">エラー:</span> {apiKeyStatus.error}
                </div>
              )}
              {!apiKeyStatus.has_quota && 
               apiKeyStatus.error && 
               !apiKeyStatus.error.includes("not implemented") && (
                <div className="mt-2 p-2 bg-red-100 border border-red-200 rounded text-sm text-red-800">
                  <p className="font-medium mb-1">⚠️ 月次制限に到達しています</p>
                  <p>Production APIキーへのアップグレード、または制限リセット（月初）まで待機してください。</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 前提条件チェック結果表示 */}
      {prerequisites && !prerequisites.all_passed && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-800">
              <XCircle className="h-5 w-5" />
              前提条件チェック失敗
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {prerequisites.errors.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-red-800 mb-2">エラー:</p>
                  <ul className="list-disc list-inside space-y-1 text-sm text-red-700">
                    {prerequisites.errors.map((error, idx) => (
                      <li key={idx}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}
              {prerequisites.warnings.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-yellow-800 mb-2">警告:</p>
                  <ul className="list-disc list-inside space-y-1 text-sm text-yellow-700">
                    {prerequisites.warnings.map((warning, idx) => (
                      <li key={idx}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {!canCreateRun && (
        <Card className="mb-6 border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-800">
              <AlertCircle className="h-5 w-5" />
              必要なサービスが停止しています
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <p className="text-sm text-yellow-700">
                Run を実行するには、以下のサービスが起動している必要があります：
              </p>
              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-700">
                {stoppedServices.map((serviceName) => {
                  const service = systemStatus?.services[serviceName];
                  const displayName =
                    serviceName === "anki"
                      ? "AnkiConnect"
                      : serviceName === "api"
                      ? "REST API"
                      : serviceName;
                  return (
                    <li key={serviceName} className="flex items-center gap-2">
                      <XCircle className="h-4 w-4 text-red-500" />
                      <span className="font-medium">{displayName}</span>
                      {service?.status && (
                        <Badge variant="secondary" className="ml-2">
                          {service.status === "stopped" ? "停止中" : service.status}
                        </Badge>
                      )}
                    </li>
                  );
                })}
              </ul>
              <div className="pt-2">
                <Link to="/system">
                  <Button variant="outline" size="sm">
                    システム管理画面で起動する
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {!currentRun && !createRunMutation.isPending && canCreateRun && (
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <p className="text-lg font-medium text-muted-foreground mb-2">
                まだ Run が実行されていません
              </p>
              <p className="text-sm text-muted-foreground mb-4">
                「Create Run」ボタンをクリックして、MCQ 生成を開始してください。
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {currentRun && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Current Run</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Run ID</p>
                  <p className="text-sm text-muted-foreground font-mono">
                    {currentRun.run_id}
                  </p>
                </div>
                {getStatusBadge(currentRun.status)}
              </div>

              <Table>
                <TableBody>
                  <TableRow>
                    <TableHead className="w-32">Mode</TableHead>
                    <TableCell>{currentRun.mode}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableHead>Started At</TableHead>
                    <TableCell>{formatDate(currentRun.started_at)}</TableCell>
                  </TableRow>
                  {currentRun.completed_at && (
                    <TableRow>
                      <TableHead>Completed At</TableHead>
                      <TableCell>{formatDate(currentRun.completed_at)}</TableCell>
                    </TableRow>
                  )}
                  {currentRun.today_count !== undefined && (
                    <TableRow>
                      <TableHead>Today Count</TableHead>
                      <TableCell>{currentRun.today_count}</TableCell>
                    </TableRow>
                  )}
                  {currentRun.new_accepted !== undefined && (
                    <TableRow>
                      <TableHead>New Accepted</TableHead>
                      <TableCell>{currentRun.new_accepted}</TableCell>
                    </TableRow>
                  )}
                  {currentRun.degraded && (
                    <TableRow>
                      <TableHead>Degraded</TableHead>
                      <TableCell>
                        <Badge variant="destructive">Yes</Badge>
                        {currentRun.degraded_reason && (
                          <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                            <p className="text-sm font-medium text-yellow-800">Degraded Reason:</p>
                            <p className="text-sm text-yellow-700 mt-1">
                              {currentRun.degraded_reason}
                            </p>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>

              {currentRun.status === "failed" && currentRun.error_message && (
                <Card className="mt-4 border-red-200 bg-red-50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-red-800">
                      <AlertCircle className="h-5 w-5" />
                      エラーが発生しました
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {currentRun.error_code && (
                        <div>
                          <span className="text-sm font-medium text-red-800">エラーコード:</span>
                          <Badge
                            variant={
                              currentRun.error_code === "RATE_LIMIT"
                                ? "outline"
                                : "destructive"
                            }
                            className={
                              currentRun.error_code === "RATE_LIMIT"
                                ? "ml-2 border-yellow-500 text-yellow-700"
                                : "ml-2"
                            }
                          >
                            {currentRun.error_code}
                          </Badge>
                        </div>
                      )}
                      {currentRun.error_phase !== undefined && (
                        <div>
                          <span className="text-sm font-medium text-red-800">発生Phase:</span>
                          <span className="text-sm text-red-700 ml-2">
                            Phase {currentRun.error_phase}
                          </span>
                        </div>
                      )}
                      <div>
                        <p className="text-sm font-medium text-red-800 mb-1">エラーメッセージ:</p>
                        <p className="text-sm text-red-700 bg-red-100 p-2 rounded border border-red-200">
                          {currentRun.error_message}
                        </p>
                      </div>
                      {currentRun.error_code === "RATE_LIMIT" && (
                        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                          <p className="text-sm font-medium text-yellow-800 mb-1">
                            💡 推奨アクション:
                          </p>
                          <p className="text-sm text-yellow-700">
                            APIのレート制限に達しました。5分ほど待ってから再実行してください。
                          </p>
                        </div>
                      )}
                      {currentRun.error_code === "ANKI_ERROR" && (
                        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                          <p className="text-sm font-medium text-yellow-800 mb-1">
                            💡 推奨アクション:
                          </p>
                          <p className="text-sm text-yellow-700">
                            AnkiConnectサービスが起動しているか確認してください。
                            <Link to="/system" className="text-primary hover:underline ml-1">
                              システム管理画面
                            </Link>
                            から確認できます。
                          </p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {currentRun.status === "running" && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Polling for updates...</span>
                  </div>
                  
                  {rateLimitStatus && (
                    <Card className="border-blue-200 bg-blue-50">
                      <CardContent className="pt-4">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="font-medium text-blue-800">レート制限状態</span>
                            <Badge
                              variant={
                                rateLimitStatus.minute_tokens > 0 &&
                                rateLimitStatus.hour_tokens > 0
                                  ? "default"
                                  : "destructive"
                              }
                            >
                              {rateLimitStatus.minute_tokens > 0 &&
                              rateLimitStatus.hour_tokens > 0
                                ? "利用可能"
                                : "制限中"}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs text-blue-700">
                            <div>
                              <span className="text-blue-600">分間:</span>{" "}
                              {Math.floor(rateLimitStatus.minute_tokens)} /{" "}
                              {rateLimitStatus.requests_per_minute}
                            </div>
                            <div>
                              <span className="text-blue-600">時間:</span>{" "}
                              {Math.floor(rateLimitStatus.hour_tokens)} /{" "}
                              {rateLimitStatus.requests_per_hour}
                            </div>
                          </div>
                          {rateLimitStatus.minute_tokens <= 1 &&
                            rateLimitStatus.next_minute_refill_seconds > 0 && (
                              <div className="text-xs text-yellow-700">
                                次の補充まで:{" "}
                                {Math.ceil(rateLimitStatus.next_minute_refill_seconds)}秒
                              </div>
                            )}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {runHistory && runHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Run History</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Started At</TableHead>
                  <TableHead>Today Count</TableHead>
                  <TableHead>New Accepted</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runHistory.map((run) => (
                  <TableRow key={run.run_id}>
                    <TableCell className="font-mono text-sm">{run.run_id}</TableCell>
                    <TableCell>{getStatusBadge(run.status)}</TableCell>
                    <TableCell>{run.mode}</TableCell>
                    <TableCell>{formatDate(run.started_at)}</TableCell>
                    <TableCell>{run.today_count ?? "-"}</TableCell>
                    <TableCell>{run.new_accepted ?? "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
