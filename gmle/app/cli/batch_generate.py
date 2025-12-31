"""Batch MCQ generation CLI with rate limit management."""

from __future__ import annotations

import argparse
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

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
    batch_interval_minutes: float = 0.083,  # 5 seconds = 0.083 minutes
    max_per_hour: int = 30,
    max_per_day: int = 800,
    dry_run: bool = False,
) -> None:
    """Execute batch MCQ generation with rate limit management.
    
    Args:
        space_id: Space ID
        target_total: Target total MCQ count
        batch_size: MCQs to generate per batch
        batch_interval_minutes: Minutes to wait between batches
        max_per_hour: Max API calls per hour
        max_per_day: Max API calls per day
        dry_run: If True, only show plan without execution
    """
    logger = get_logger(space_id=space_id)
    
    # 現在のMCQ数を取得
    current_count = get_current_mcq_count(space_id)
    remaining = target_total - current_count
    
    if remaining <= 0:
        print(f"✅ Target already reached: {current_count}/{target_total} MCQs")
        return
    
    total_batches = (remaining + batch_size - 1) // batch_size
    total_minutes = total_batches * batch_interval_minutes
    total_api_calls = remaining * 2  # Stage1 + Stage2
    
    print("🚀 Batch MCQ Generation")
    print("=" * 60)
    print(f"📊 Current MCQs:     {current_count}")
    print(f"📊 Target MCQs:      {target_total}")
    print(f"📊 Remaining:        {remaining}")
    print(f"📦 Batch size:       {batch_size} MCQ/batch")
    print(f"📦 Total batches:    {total_batches}")
    if batch_interval_minutes < 1:
        print(f"⏱️  Batch interval:   {int(batch_interval_minutes * 60)} seconds")
    else:
        print(f"⏱️  Batch interval:   {batch_interval_minutes} minutes")
    print(f"🔒 Rate limits:      {max_per_hour}/hour, {max_per_day}/day")
    print(f"📈 API calls:        {total_api_calls} calls ({total_api_calls * 2} tokens est.)")
    
    # 推定時間を適切な単位で表示
    if total_minutes < 1:
        print(f"⏰ Estimated time:   ~{int(total_minutes * 60)} seconds")
    elif total_minutes < 60:
        print(f"⏰ Estimated time:   ~{int(total_minutes)} minutes")
    else:
        print(f"⏰ Estimated time:   ~{total_minutes / 60:.1f} hours")
    print("=" * 60)
    
    if dry_run:
        print("\n✅ Dry run completed. Use --execute to start actual generation.")
        return
    
    print("\n⚠️  Starting batch generation in 5 seconds...")
    print("   Press Ctrl+C to cancel.\n")
    time.sleep(5)
    
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
            
            print(f"\n{'='*60}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            print(f"🔄 MCQ #{generated_count + 1}/{target_total} を生成中...")
            print(f"   Rate usage: {total_hour}/{max_per_hour} calls/hour")
            print(f"   Progress: {'█' * int((generated_count / target_total) * 30)}{'░' * (30 - int((generated_count / target_total) * 30))} {generated_count}/{target_total}")
            print(f"{'='*60}")
            
            # レートリミットチェック（予想されるAPI呼び出し数を考慮）
            estimated_calls = current_batch_size * 2  # Stage1 + Stage2
            if total_hour + estimated_calls >= max_per_hour:
                # 次の時間まで待機
                from datetime import datetime as dt
                current_time = dt.now()
                next_hour = current_time.replace(minute=0, second=0, microsecond=0)
                next_hour = next_hour.replace(hour=current_time.hour + 1)
                wait_seconds = int((next_hour - current_time).total_seconds()) + 60
                wait_minutes = int(wait_seconds / 60) + 1
                
                print(f"⏸️  Rate limit would be exceeded ({total_hour + estimated_calls}/{max_per_hour})")
                print(f"   Waiting {wait_minutes} minutes until next hour...")
                
                # 毎秒カウントダウン表示
                for remaining in range(wait_seconds, 0, -1):
                    mins, secs = divmod(remaining, 60)
                    print(f"   ⏱️  残り {mins:02d}:{secs:02d} (MCQ: {generated_count}/{target_total})")
                    time.sleep(1)
            
            # Run実行
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
                new_count = get_current_mcq_count(space_id)
                actual_generated = new_count - generated_count
                generated_count = new_count
                
                progress = (generated_count / target_total) * 100
                elapsed_seconds = time.time() - start_time
                elapsed_hours = elapsed_seconds / 3600
                
                print(f"\n✅ MCQ #{generated_count} 完了！")
                print(f"   Generated: {actual_generated} MCQs")
                print(f"   Total: {generated_count}/{target_total} ({progress:.1f}%)")
                print(f"   Elapsed: {int(elapsed_seconds)}秒 ({elapsed_hours:.2f}時間)")
                if generated_count > 0:
                    avg_time = elapsed_seconds / generated_count
                    remaining = target_total - generated_count
                    eta_seconds = avg_time * remaining
                    eta_mins = int(eta_seconds / 60)
                    print(f"   ETA: 約{eta_mins}分 ({avg_time:.1f}秒/MCQ)")
                
                # 次のバッチまで待機（毎秒カウントダウン表示）
                if generated_count < target_total:
                    wait_seconds = int(batch_interval_minutes * 60)
                    if wait_seconds > 0:
                        print(f"⏳ Waiting {wait_seconds} seconds until next MCQ...")
                        for remaining in range(wait_seconds, 0, -1):
                            print(f"   ⏱️  {remaining}秒... (次のMCQ: {generated_count + 1}/{target_total})")
                            time.sleep(1)
            
            except KeyboardInterrupt:
                raise
            except Exception as e:
                error_msg = str(e)
                
                # レートリミットエラーは予期されるものなので、優雅に処理
                if "Hourly limit reached" in error_msg or "Rate limit" in error_msg:
                    wait_seconds = 3600
                    print(f"⏸️  Rate limit reached, waiting 1 hour...")
                    logger.info(f"Batch {batch_num} paused due to rate limit, waiting 1 hour")
                    
                    # 毎秒カウントダウン表示
                    for remaining in range(wait_seconds, 0, -1):
                        mins, secs = divmod(remaining, 60)
                        print(f"   ⏱️  残り {mins:02d}:{secs:02d} (MCQ: {generated_count}/{target_total})")
                        time.sleep(1)
                else:
                    # その他のエラーはログに記録
                    logger.error(f"Batch {batch_num} failed", exc_info=e)
                    print(f"❌ Batch {batch_num} failed: {error_msg}")
                    print(f"⏸️  Retrying in {batch_interval_minutes} minutes...")
                    time.sleep(batch_interval_minutes * 60)
    
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
    print(f"⏱️  Total time: {total_time:.1f} hours")
    print(f"📈 Average: {total_generated / total_time:.1f} MCQs/hour")
    print("=" * 60)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch MCQ generation with rate limit management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview)
  python -m gmle.app.cli.batch_generate --space-id my-project --target 82 --dry-run
  
  # Execute with default settings
  python -m gmle.app.cli.batch_generate --space-id my-project --target 82 --execute
  
  # Execute with custom settings
  python -m gmle.app.cli.batch_generate \\
    --space-id my-project \\
    --target 82 \\
    --batch-size 15 \\
    --interval 40 \\
    --execute
        """,
    )
    parser.add_argument("--space-id", required=True, help="Space ID")
    parser.add_argument("--target", type=int, required=True, help="Target MCQ count")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Batch size (MCQs per batch, default: 1 for continuous generation)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.083,
        help="Batch interval in minutes (default: 0.083 = 5 seconds)",
    )
    parser.add_argument(
        "--max-per-hour",
        type=int,
        default=40,
        help="Max API calls per hour (default: 40, 10 RPM × 4 batches)",
    )
    parser.add_argument(
        "--max-per-day",
        type=int,
        default=800,
        help="Max API calls per day (default: 800, 80%% of daily limit)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan without execution",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute batch generation",
    )
    
    args = parser.parse_args()
    
    if not args.execute and not args.dry_run:
        parser.error("Use --execute to start or --dry-run to preview")
    
    batch_generate(
        space_id=args.space_id,
        target_total=args.target,
        batch_size=args.batch_size,
        batch_interval_minutes=args.interval,
        max_per_hour=args.max_per_hour,
        max_per_day=args.max_per_day,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()

