"""Batch MCQ generation CLI with rate limit management."""

from __future__ import annotations

import argparse
import sys
import threading
import time
import yaml
from datetime import datetime
from pathlib import Path

from gmle.app.config.paths import resolve_paths
from gmle.app.config.space_loader import load_space_yaml
from gmle.app.http.api_gate import get_unified_api_gate
from gmle.app.infra.logger import get_logger
from gmle.app.phase.runner import run as run_phases
from gmle.app.sot.items_io import read_items


def get_current_mcq_count(space_id: str) -> int:
    """Get current MCQ count from items.json.
    
    Args:
        space_id: Space ID
        
    Returns:
        Current MCQ count
    """
    try:
        root = Path.cwd()
        space_cfg = load_space_yaml(root, space_id)
        paths = resolve_paths(root, space_id, space_cfg)
        items_path = paths.get("items")
        if not items_path:
            return 0
        items = read_items(items_path)
        return len(items)
    except Exception:
        return 0


def batch_generate(
    space_id: str,
    target_total: int,
    batch_size: int = 1,
    max_per_hour: int = 30,
    max_per_day: int = 800,
    dry_run: bool = False,
) -> None:
    """Execute batch MCQ generation with rate limit management.
    
    Args:
        space_id: Space ID
        target_total: Target total MCQ count
        batch_size: MCQs to generate per batch (default: 1)
        max_per_hour: Max API calls per hour
        max_per_day: Max API calls per day
        dry_run: If True, only show plan without execution
    """
    logger = get_logger()
    
    # 現在のMCQ数を取得
    current_count = get_current_mcq_count(space_id)
    remaining = target_total - current_count
    
    if remaining <= 0:
        print(f"✅ Target of {target_total} MCQs already met or exceeded. Current: {current_count}")
        return
    
    total_batches = (remaining + batch_size - 1) // batch_size
    total_api_calls = remaining * 2  # Stage1 + Stage2
    
    print("🚀 Batch MCQ Generation")
    print("=" * 60)
    print(f"📊 Current MCQs:     {current_count}")
    print(f"📊 Target MCQs:      {target_total}")
    print(f"📊 Remaining:        {remaining}")
    print(f"📦 Batch size:       {batch_size} MCQ/batch")
    print(f"📦 Total batches:    {total_batches}")
    print(f"🔒 Rate limits:      {max_per_hour}/hour, {max_per_day}/day")
    print(f"📈 API calls:        {total_api_calls} calls ({total_api_calls * 2} tokens est.)")
    print("=" * 60)
    
    if dry_run:
        print("\n✅ Dry run completed. Use --execute to start actual generation.")
        return
    
    print("\n⚠️  Starting batch generation in 3 seconds...")
    print("   Press Ctrl+C to cancel.\n")
    time.sleep(3)
    
    generated_count = current_count
    batch_num = 0
    start_time = time.time()
    
    try:
        while generated_count < target_total:
            batch_num += 1
            remaining_now = target_total - generated_count
            current_batch_size = min(batch_size, remaining_now)
            
            # レートリミットチェック
            gate = get_unified_api_gate()
            usage = gate.usage_tracker.get_usage("groq")
            current_hour_usage = usage.get("hourly_usage", {})
            
            # 現在の時間のusageを取得
            from datetime import datetime as dt
            current_hour_key = dt.now().strftime("%Y-%m-%dT%H")
            hour_data = current_hour_usage.get(current_hour_key, {}).get("groq", {})
            total_hour = hour_data.get("total", 0)
            
            # レートリミットチェック（予想されるAPI呼び出し数を考慮）
            estimated_calls = current_batch_size * 2  # Stage1 + Stage2
            if total_hour + estimated_calls >= max_per_hour:
                # 次の時間まで待機
                current_time = dt.now()
                next_hour = current_time.replace(minute=0, second=0, microsecond=0)
                next_hour = next_hour.replace(hour=current_time.hour + 1)
                wait_seconds = int((next_hour - current_time).total_seconds()) + 60
                
                print(f"\n⏸️  Rate limit would be exceeded ({total_hour + estimated_calls}/{max_per_hour})")
                print("   Waiting until next hour...")
                
                # 毎秒カウントダウン表示
                for remaining_sec in range(wait_seconds, 0, -1):
                    mins, secs = divmod(remaining_sec, 60)
                    print(f"   ⏱️  残り {mins:02d}:{secs:02d} | MCQ: {generated_count}/{target_total}", end="\r")
                    time.sleep(1)
                print()  # 改行
            
            # Run実行（別スレッドで実行し、メインスレッドで監視）
            print(f"\n{'='*60}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            print(f"🔄 MCQ #{generated_count + 1}/{target_total} を生成中...")
            print(f"   Rate usage: {total_hour}/{max_per_hour} calls/hour")
            progress_bar = '█' * int((generated_count / target_total) * 30) + '░' * (30 - int((generated_count / target_total) * 30))
            print(f"   Progress: {progress_bar} {generated_count}/{target_total}")
            print(f"{'='*60}")
            
            # Run実行用の共有状態
            run_result = {"completed": False, "error": None, "new_count": generated_count}
            
            def run_task():
                """Run実行タスク"""
                try:
                    # Override new_total temporarily in space config
                    root = Path.cwd()
                    space_config_path = root / "config" / "spaces" / f"{space_id}.yaml"
                    
                    # Read current config
                    with open(space_config_path, "r") as f:
                        space_cfg = yaml.safe_load(f)
                    
                    original_new_total = space_cfg.get("params", {}).get("new_total")
                    
                    # Temporarily update new_total
                    if "params" not in space_cfg:
                        space_cfg["params"] = {}
                    space_cfg["params"]["new_total"] = current_batch_size
                    
                    # Write temporary config
                    with open(space_config_path, "w") as f:
                        yaml.dump(space_cfg, f, default_flow_style=False, allow_unicode=True)
                    
                    try:
                        run_phases(
                            space_id=space_id,
                            options={
                                "mode": "normal",
                                "space": space_id,
                            }
                        )
                    finally:
                        # Restore original new_total
                        space_cfg["params"]["new_total"] = original_new_total
                        with open(space_config_path, "w") as f:
                            yaml.dump(space_cfg, f, default_flow_style=False, allow_unicode=True)
                    
                    # 完了後のカウント確認
                    run_result["new_count"] = get_current_mcq_count(space_id)
                    run_result["completed"] = True
                    
                except Exception as e:
                    run_result["error"] = e
                    run_result["completed"] = True
            
            # Run実行を別スレッドで開始
            run_thread = threading.Thread(target=run_task, daemon=True)
            run_thread.start()
            
            # メインスレッドで1秒ごとに状況を監視
            elapsed = 0
            while not run_result["completed"]:
                time.sleep(1)
                elapsed += 1
                
                # 現在の状況を表示
                mins, secs = divmod(elapsed, 60)
                gate = get_unified_api_gate()
                usage = gate.usage_tracker.get_usage("groq")
                current_hour_usage = usage.get("hourly_usage", {})
                current_hour_key = dt.now().strftime("%Y-%m-%dT%H")
                hour_data = current_hour_usage.get(current_hour_key, {}).get("groq", {})
                current_rate = hour_data.get("total", 0)
                
                status = f"   ⏱️  経過: {mins:02d}:{secs:02d} | Rate: {current_rate}/{max_per_hour} | MCQ: {generated_count}/{target_total}"
                print(status, end="\r")
            
            print()  # 改行
            
            # Run実行結果を処理
            if run_result["error"]:
                error_msg = str(run_result["error"])
                
                # レートリミットエラーは予期されるものなので、優雅に処理
                if "Hourly limit reached" in error_msg or "Rate limit" in error_msg:
                    wait_seconds = 3600
                    print("\n⏸️  Rate limit reached, waiting 1 hour...")
                    logger.info(f"Batch {batch_num} paused due to rate limit, waiting 1 hour")
                    
                    # 毎秒カウントダウン表示
                    for remaining_sec in range(wait_seconds, 0, -1):
                        mins, secs = divmod(remaining_sec, 60)
                        print(f"   ⏱️  残り {mins:02d}:{secs:02d} | MCQ: {generated_count}/{target_total}", end="\r")
                        time.sleep(1)
                    print()  # 改行
                else:
                    # その他のエラーはログに記録して続行
                    logger.error(f"Batch {batch_num} failed: {error_msg}")
                    print(f"\n❌ Error: {error_msg}")
                    print("   Continuing to next MCQ...")
            else:
                # 成功した場合
                new_count: int = run_result.get("new_count") or generated_count
                actual_generated = new_count - generated_count
                generated_count = new_count
                
                progress = (generated_count / target_total) * 100
                elapsed_seconds = time.time() - start_time
                
                print(f"\n✅ MCQ #{generated_count} 完了！ (生成数: {actual_generated})")
                print(f"   Total: {generated_count}/{target_total} ({progress:.1f}%)")
                print(f"   Elapsed: {int(elapsed_seconds)}秒")
                
                if generated_count > 0:
                    avg_time = elapsed_seconds / generated_count
                    remaining_mcqs = target_total - generated_count
                    eta_seconds = avg_time * remaining_mcqs
                    eta_mins = int(eta_seconds / 60)
                    print(f"   ETA: 約{eta_mins}分 ({avg_time:.1f}秒/MCQ)")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Batch generation interrupted by user")
        print(f"✅ Generated so far: {generated_count - current_count} MCQs")
        print(f"📊 Current total: {generated_count}/{target_total} MCQs")
        sys.exit(0)
    
    # 完了
    total_time = (time.time() - start_time) / 3600
    total_generated = generated_count - current_count
    
    print("\n" + "=" * 60)
    print("🎉 Batch generation completed!")
    print(f"✅ Generated: {total_generated} MCQs")
    print(f"📊 Total: {generated_count}/{target_total} MCQs")
    print(f"⏱️  Total time: {total_time:.2f} hours")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Batch MCQ generation with rate limit management"
    )
    parser.add_argument("--space-id", required=True, help="Space ID")
    parser.add_argument("--target", type=int, required=True, help="Target MCQ count")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Batch size (MCQs per batch, default: 1)",
    )
    parser.add_argument(
        "--max-per-hour",
        type=int,
        default=40,
        help="Max API calls per hour (default: 40)",
    )
    parser.add_argument(
        "--max-per-day",
        type=int,
        default=800,
        help="Max API calls per day (default: 800)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show plan without execution")
    parser.add_argument("--execute", action="store_true", help="Execute batch generation")
    
    args = parser.parse_args()
    
    if not args.execute and not args.dry_run:
        parser.error("Use --execute to start or --dry-run to preview")
    
    batch_generate(
        space_id=args.space_id,
        target_total=args.target,
        batch_size=args.batch_size,
        max_per_hour=args.max_per_hour,
        max_per_day=args.max_per_day,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
