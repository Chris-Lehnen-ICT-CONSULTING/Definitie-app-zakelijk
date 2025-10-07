# Performance Baseline Tracking - Implementation Checklist

**Status:** Ready for Implementation
**Estimated Effort:** 4-5 days (core), 7-8 days (with UI)
**Related:** [Design](./performance-baseline-tracking-design.md) | [Summary](./performance-baseline-tracking-summary.md) | [Architecture](./performance-baseline-tracking-architecture.md)

---

## Pre-Implementation

- [ ] **Review Design Documents**
  - [ ] Read full design document
  - [ ] Read architecture diagrams
  - [ ] Understand 3-tier regression detection
  - [ ] Understand baseline calculation algorithm

- [ ] **Create User Story**
  - [ ] Add US-203 to backlog
  - [ ] Link to design documents
  - [ ] Estimate story points (13 for core, 21 with UI)

- [ ] **Branch Setup**
  - [ ] Create feature branch: `git checkout -b feature/US-203-performance-tracking`
  - [ ] Verify branch tracks remote: `git push -u origin feature/US-203-performance-tracking`

- [ ] **Backup Critical Files**
  ```bash
  mkdir -p backups/US-203
  cp src/database/schema.sql backups/US-203/
  cp data/definities.db backups/US-203/
  cp src/main.py backups/US-203/
  ```

---

## Phase 1: Foundation (4 hours) ✅ SIMPLE

### 1.1 Database Schema

- [ ] **Create Migration Script**
  - [ ] Create file: `src/database/migrations/010_add_performance_tracking.sql`
  - [ ] Add `performance_baselines` table (see design doc section 2.1)
  - [ ] Add `performance_alerts` table
  - [ ] Add `performance_targets` table
  - [ ] Add indexes for common queries
  - [ ] Seed performance targets from CLAUDE.md

- [ ] **Test Migration**
  ```bash
  # Backup database
  cp data/definities.db data/definities.db.backup

  # Run migration
  python src/database/migrate_database.py

  # Verify tables exist
  sqlite3 data/definities.db ".schema performance_baselines"
  sqlite3 data/definities.db "SELECT COUNT(*) FROM performance_targets"
  # Should see 8 targets

  # Rollback if needed
  cp data/definities.db.backup data/definities.db
  ```

### 1.2 PerformanceTracker Core Class

- [ ] **Create Core Module**
  - [ ] Create file: `src/monitoring/performance_tracker.py`
  - [ ] Implement `PerformanceTracker` class (singleton pattern)
  - [ ] Implement `start_operation(name)` method
  - [ ] Implement `stop_operation(name)` method
  - [ ] Implement `record_metric(id, value)` method
  - [ ] Implement `record_baseline_snapshot()` method
  - [ ] Add `_generate_session_id()` helper
  - [ ] Add `_get_git_commit()` helper
  - [ ] Add `_insert_baseline()` helper

- [ ] **Test Core Functionality**
  ```python
  # Test script: scripts/monitoring/test_tracker.py
  from monitoring.performance_tracker import PerformanceTracker

  tracker = PerformanceTracker.get_instance()
  tracker.start_operation('test_op')
  # ... simulate work ...
  duration = tracker.stop_operation('test_op')
  assert duration > 0

  tracker.record_metric('test_metric', 123)
  baseline_id = tracker.record_baseline_snapshot()
  assert baseline_id > 0

  print("✅ PerformanceTracker works!")
  ```

### 1.3 Basic Instrumentation

- [ ] **Instrument main.py**
  ```python
  # src/main.py (add at top)
  from monitoring.performance_tracker import PerformanceTracker

  # In main() function
  def main():
      tracker = PerformanceTracker.get_instance()
      tracker.start_operation('app_startup')

      try:
          SessionStateManager.initialize_session_state()
          interface = TabbedInterface()
          interface.render()

          tracker.stop_operation('app_startup')
          tracker.record_baseline_snapshot()
      except Exception as e:
          tracker.stop_operation('app_startup', error=e)
          raise
  ```

- [ ] **Test End-to-End**
  ```bash
  # Run app and check logs
  streamlit run src/main.py

  # Verify baseline recorded
  sqlite3 data/definities.db "SELECT * FROM performance_baselines ORDER BY timestamp DESC LIMIT 1"
  # Should show recent baseline with startup_time_ms populated

  # Check session logs
  tail logs/*.log
  # Should see "Operation app_startup completed in XXXms"
  ```

### 1.4 CLI Status Command

- [ ] **Create CLI Module**
  - [ ] Create file: `scripts/monitoring/performance_cli.py`
  - [ ] Implement `status` command (shows last baseline)
  - [ ] Add argument parsing with `argparse`
  - [ ] Make executable: `chmod +x scripts/monitoring/performance_cli.py`

- [ ] **Test CLI**
  ```bash
  python -m scripts.monitoring.performance_cli status

  # Expected output:
  # 📊 Latest Performance Baseline
  # Timestamp: 2025-10-07 14:32:15
  # Session: sess_abc123
  # Startup Time: 387ms ✅ (target: 500ms)
  # ...
  ```

### 1.5 Phase 1 Verification

- [ ] **Run Full Test Suite**
  ```bash
  pytest -q tests/
  # All tests should pass
  ```

- [ ] **Measure Overhead**
  ```python
  import time
  start = time.perf_counter()
  tracker = PerformanceTracker.get_instance()
  tracker.start_operation('test')
  tracker.stop_operation('test')
  tracker.record_baseline_snapshot()
  overhead_ms = (time.perf_counter() - start) * 1000
  assert overhead_ms < 50, f"Overhead too high: {overhead_ms}ms"
  print(f"✅ Overhead: {overhead_ms:.1f}ms")
  ```

- [ ] **Verify Database Growth**
  ```bash
  ls -lh data/definities.db
  # Should be ~1KB larger per baseline
  ```

- [ ] **Commit Phase 1**
  ```bash
  git add src/database/migrations/010_add_performance_tracking.sql
  git add src/monitoring/performance_tracker.py
  git add src/main.py
  git add scripts/monitoring/performance_cli.py
  git commit -m "feat(US-203): Phase 1 - Basic performance tracking

  - Add database tables for baselines, alerts, targets
  - Implement PerformanceTracker singleton class
  - Instrument main.py for startup timing
  - Add CLI status command

  Overhead: <50ms per app start
  Coverage: APP-001 (startup time) tracked"
  ```

---

## Phase 2: Comprehensive Metrics (2 days) 📊 MEDIUM

### 2.1 ServiceContainer Instrumentation

- [ ] **Update container.py**
  ```python
  # src/services/container.py
  from monitoring.performance_tracker import PerformanceTracker

  class ServiceContainer:
      _init_count = 0

      def __init__(self, config=None):
          ServiceContainer._init_count += 1

          tracker = PerformanceTracker.get_instance()
          tracker.record_metric('container_init_count', ServiceContainer._init_count)
          tracker.start_operation('container_init')

          try:
              # Existing init code
              self._initialize_services(config)
              tracker.stop_operation('container_init')
          except Exception as e:
              tracker.stop_operation('container_init', error=e)
              raise
  ```

- [ ] **Test Container Tracking**
  ```python
  # Verify container init count is recorded
  container = ServiceContainer()
  # Check database for container_init_count metric
  ```

### 2.2 Validation Instrumentation

- [ ] **Update ValidationOrchestratorV2**
  ```python
  # src/services/validation/validation_orchestrator_v2.py
  from monitoring.decorators import measure_performance

  class ValidationOrchestratorV2:
      @measure_performance('validation', 'VAL-001')
      async def validate(self, definition: str) -> dict:
          # Existing validation code
          result = await self._perform_validation(definition)
          return result
  ```

- [ ] **Create Decorator Module**
  - [ ] Create file: `src/monitoring/decorators.py`
  - [ ] Implement `@measure_performance` decorator (see design appendix A)
  - [ ] Handle both sync and async functions

- [ ] **Test Validation Tracking**
  ```python
  # Run validation and verify timing recorded
  orchestrator = ValidationOrchestratorV2(...)
  await orchestrator.validate("test definition")
  # Check database for validation_time_ms
  ```

### 2.3 Definition Generation Instrumentation

- [ ] **Update DefinitionOrchestratorV2**
  ```python
  # src/services/orchestrators/definition_orchestrator_v2.py
  class DefinitionOrchestratorV2:
      @measure_performance('generation', 'GEN-001')
      async def generate_definition(self, term: str) -> dict:
          result = await self._generate(term)

          # Record API metrics
          tracker = PerformanceTracker.get_instance()
          tracker.record_metric('prompt_token_count', result['token_count'])
          tracker.record_metric('api_cost_cents', result['cost'] * 100)

          return result
  ```

### 2.4 Rule Cache Instrumentation

- [ ] **Update RuleCache**
  ```python
  # src/toetsregels/rule_cache.py
  class RuleCache:
      @measure_performance('rule_loading', 'VAL-002')
      def get_cached_toetsregel_manager(self):
          result = self._get_or_load()

          # Record cache stats
          tracker = PerformanceTracker.get_instance()
          stats = self.get_stats()
          tracker.record_metric('rule_cache_hit_rate', stats['hit_rate'])

          return result
  ```

### 2.5 Memory & Cache Integration

- [ ] **Integrate with Existing Monitors**
  ```python
  # In PerformanceTracker.record_baseline_snapshot()

  # Pull from APIMonitor
  from monitoring.api_monitor import get_metrics_collector
  collector = get_metrics_collector()
  api_metrics = collector.get_realtime_metrics()
  self.record_metric('api_call_time_ms', api_metrics['avg_response_time'] * 1000)

  # Pull from RuleCache
  from toetsregels.rule_cache import RuleCache
  cache = RuleCache.get_instance()
  cache_stats = cache.get_stats()
  self.record_metric('rule_cache_hit_rate', cache_stats['hit_rate'])

  # Memory usage (already in code)
  import psutil
  process = psutil.Process()
  memory_mb = process.memory_info().rss // (1024 * 1024)
  self.record_metric('peak_memory_mb', memory_mb)
  ```

### 2.6 Baseline Calculation Logic

- [ ] **Implement BaselineRecorder**
  - [ ] Create file: `src/monitoring/baseline_recorder.py`
  - [ ] Implement `calculate_baseline(metric_id, window=20)` method
  - [ ] Implement outlier removal (>3 std devs)
  - [ ] Implement confidence calculation
  - [ ] Return dict with median, p5, p95, std_dev, confidence

- [ ] **Test Baseline Calculation**
  ```python
  # Test with synthetic data
  from monitoring.baseline_recorder import BaselineRecorder

  recorder = BaselineRecorder()
  baseline = recorder.calculate_baseline('APP-001', window=20)

  assert 'median' in baseline
  assert 'confidence' in baseline
  assert 0 <= baseline['confidence'] <= 1
  print(f"✅ Baseline: {baseline}")
  ```

### 2.7 Cold Start Detection

- [ ] **Add Cold Start Logic**
  ```python
  # In PerformanceTracker.__init__()
  self.is_cold_start = self._detect_cold_start()

  def _detect_cold_start(self) -> bool:
      """Detect if this is a cold start (first 3 runs in last hour)."""
      recent_count = self.db.execute("""
          SELECT COUNT(*) FROM performance_baselines
          WHERE timestamp > datetime('now', '-1 hour')
      """).fetchone()[0]

      return recent_count < 3

  # In record_baseline_snapshot()
  baseline['is_cold_start'] = self.is_cold_start
  ```

### 2.8 Phase 2 Verification

- [ ] **Verify All Metrics Tracked**
  ```sql
  SELECT * FROM performance_baselines ORDER BY timestamp DESC LIMIT 1;
  -- Check all 13 core metrics are populated
  ```

- [ ] **Run Performance Tests**
  ```bash
  pytest tests/performance/ -v
  # All performance tests should pass
  ```

- [ ] **Measure Baseline Confidence**
  ```python
  # After 20 runs
  baseline = recorder.calculate_baseline('APP-001')
  assert baseline['confidence'] > 0.7, "Need more samples"
  ```

- [ ] **Commit Phase 2**
  ```bash
  git add src/monitoring/decorators.py
  git add src/monitoring/baseline_recorder.py
  git add src/services/container.py
  git add src/services/validation/validation_orchestrator_v2.py
  git add src/services/orchestrators/definition_orchestrator_v2.py
  git add src/toetsregels/rule_cache.py
  git commit -m "feat(US-203): Phase 2 - Comprehensive metrics tracking

  - Add @measure_performance decorator for clean instrumentation
  - Track all 13 core metrics (APP, SVC, VAL, GEN, API, EXP, MEM)
  - Implement baseline calculation with outlier removal
  - Add cold start detection
  - Integrate with existing monitors (APIMonitor, RuleCache)

  Coverage: All core metrics tracked with high confidence baselines"
  ```

---

## Phase 3: Regression Detection (2 days) 🚨 MEDIUM

### 3.1 RegressionDetector Core

- [ ] **Create Detector Module**
  - [ ] Create file: `src/monitoring/regression_detector.py`
  - [ ] Implement `RegressionDetector` class
  - [ ] Implement `evaluate_metric(metric_id, current_value)` method
  - [ ] Returns dict with severity, deviation_percent, details

### 3.2 Tier 1: Threshold Detection

- [ ] **Implement Threshold Check**
  ```python
  # In RegressionDetector
  def check_threshold_breach(self, current, target, thresholds):
      """Compare current value against target with thresholds."""
      deviation_pct = ((current - target['value']) / target['value']) * 100

      if deviation_pct > thresholds['error']:
          return 'critical' if deviation_pct > thresholds['error'] * 1.5 else 'error'
      elif deviation_pct > thresholds['warning']:
          return 'warning'
      else:
          return 'ok'
  ```

- [ ] **Test Threshold Detection**
  ```python
  detector = RegressionDetector(db)

  # Test warning threshold
  result = detector.check_threshold_breach(
      current=550,  # 10% over
      target={'value': 500},
      thresholds={'warning': 10, 'error': 20}
  )
  assert result == 'warning'

  # Test error threshold
  result = detector.check_threshold_breach(
      current=650,  # 30% over
      target={'value': 500},
      thresholds={'warning': 10, 'error': 20}
  )
  assert result == 'error'
  ```

### 3.3 Tier 2: Statistical Detection

- [ ] **Implement Statistical Check**
  ```python
  def check_regression(self, current, baseline):
      """Compare current value against baseline statistics."""
      z_score = (current - baseline['median']) / baseline['std_dev']

      if z_score > 3:
          severity = 'critical'
      elif z_score > 2:
          severity = 'error'
      elif z_score > 1:
          severity = 'warning'
      else:
          severity = 'ok'

      return {
          'is_regression': z_score > 1,
          'severity': severity,
          'z_score': z_score,
          'percentile': self._calculate_percentile(current, baseline)
      }
  ```

- [ ] **Test Statistical Detection**
  ```python
  baseline = {
      'median': 400,
      'std_dev': 20,
      'p5': 380,
      'p95': 420
  }

  # Test normal value
  result = detector.check_regression(current=405, baseline=baseline)
  assert result['severity'] == 'ok'

  # Test outlier
  result = detector.check_regression(current=460, baseline=baseline)
  assert result['severity'] in ['warning', 'error']
  assert result['z_score'] > 1
  ```

### 3.4 Tier 3: Trend Analysis

- [ ] **Implement Trend Detection**
  ```python
  def detect_trend_regression(self, metric_id, window_hours=24):
      """Detect if metric is trending worse over time."""
      import numpy as np

      # Get timeseries data
      rows = self.db.execute("""
          SELECT timestamp, {metric_id} as value
          FROM performance_baselines
          WHERE timestamp > datetime('now', '-{hours} hours')
          ORDER BY timestamp
      """.format(metric_id=metric_id, hours=window_hours)).fetchall()

      if len(rows) < 5:
          return None  # Not enough data

      # Linear regression
      times = [(row['timestamp'] - rows[0]['timestamp']).total_seconds() / 3600
               for row in rows]
      values = [row['value'] for row in rows]

      slope, intercept, r_value = np.polyfit(times, values, 1)

      # Positive slope = getting worse (for time metrics)
      if slope > 0.05 and r_value ** 2 > 0.6:
          severity = 'error' if r_value ** 2 > 0.8 else 'warning'
      else:
          severity = 'ok'

      return {
          'has_trend_regression': slope > 0.05 and r_value ** 2 > 0.6,
          'severity': severity,
          'slope': slope,
          'r_squared': r_value ** 2
      }
  ```

### 3.5 Combined Evaluation Logic

- [ ] **Implement Evaluate Metric**
  ```python
  def evaluate_metric(self, metric_id, current_value):
      """
      Combine all three tiers into final decision.
      Returns dict with severity and all tier results.
      """
      # Get target and baseline
      target = self._get_target(metric_id)
      baseline = self._calculate_baseline(metric_id)

      # Tier 1: Threshold
      threshold_result = self.check_threshold_breach(current_value, target, target)

      # Tier 2: Statistical
      regression_result = self.check_regression(current_value, baseline)

      # Tier 3: Trend
      trend_result = self.detect_trend_regression(metric_id)

      # Combine (worst severity wins)
      severities = ['ok', 'warning', 'error', 'critical']
      final_severity = max(
          threshold_result,
          regression_result['severity'],
          trend_result['severity'] if trend_result else 'ok',
          key=lambda s: severities.index(s)
      )

      return {
          'metric_id': metric_id,
          'metric_name': target['name'],
          'severity': final_severity,
          'current_value': current_value,
          'expected_value': baseline['median'],
          'target_value': target['value'],
          'deviation_percent': ((current_value - baseline['median']) / baseline['median']) * 100,
          'threshold_breached': threshold_result != 'ok',
          'details': {
              'threshold': threshold_result,
              'regression': regression_result,
              'trend': trend_result
          }
      }
  ```

### 3.6 Alert Creation

- [ ] **Integrate with PerformanceTracker**
  ```python
  # In PerformanceTracker.record_baseline_snapshot()
  def _check_regressions(self, baseline_id: int) -> list:
      """Check for regressions and create alerts."""
      from monitoring.regression_detector import RegressionDetector

      detector = RegressionDetector(self.db)
      alerts = []

      for metric_id, current_value in self.metrics.items():
          if current_value is None:
              continue

          result = detector.evaluate_metric(metric_id, current_value)

          if result['severity'] != 'ok':
              alert = {
                  'baseline_id': baseline_id,
                  'alert_type': 'regression',
                  'severity': result['severity'],
                  'metric_id': metric_id,
                  'metric_name': result['metric_name'],
                  'current_value': current_value,
                  'expected_value': result['expected_value'],
                  'deviation_percent': result['deviation_percent'],
                  'threshold_breached': result['threshold_breached'],
                  'context_json': json.dumps(result['details'])
              }

              alert_id = self._insert_alert(alert)
              alerts.append(alert)

      return alerts
  ```

### 3.7 Terminal Output

- [ ] **Enhance Log Summary**
  ```python
  # In PerformanceTracker._log_summary()
  def _log_summary(self, baseline: dict, alerts: list):
      """Log performance summary with alerts to console."""
      print("\n🚀 DefinitieAgent Startup Performance")
      print("─" * 60)

      # Key metrics with status indicators
      startup = baseline.get('startup_time_ms')
      if startup:
          status = "✅" if startup < 500 else "⚠️" if startup < 600 else "❌"
          print(f"⏱️  Startup Time:        {startup:.0f}ms  {status} (target: 500ms)")

      # ... more metrics ...

      # Warnings section
      if alerts:
          print(f"\n⚠️  WARNINGS:")
          for alert in alerts[:3]:  # Top 3 alerts
              emoji = {'warning': '⚠️', 'error': '❌', 'critical': '🚨'}[alert['severity']]
              print(f"  {emoji} {alert['metric_name']}: {alert['current_value']:.0f} "
                    f"(expected: {alert['expected_value']:.0f}) "
                    f"{alert['severity'].upper()}")

      # Trend indicator
      trend = self._calculate_trend()
      if trend > 0:
          print(f"\n📈 Trend: Performance improving (+{trend:.1f}% vs 7-day avg)")
      elif trend < 0:
          print(f"\n📉 Trend: Performance degrading ({trend:.1f}% vs 7-day avg)")

      print("─" * 60)
      print()
  ```

### 3.8 Structured Logging

- [ ] **Add JSON Log Output**
  ```python
  # In PerformanceTracker.record_baseline_snapshot()

  import logging
  logger = logging.getLogger(__name__)

  # Log structured JSON to file
  log_entry = {
      'timestamp': datetime.now().isoformat(),
      'session_id': self.session_id,
      'git_commit': self._get_git_commit(),
      'metrics': {k: v for k, v in self.metrics.items() if v is not None},
      'alerts': [
          {
              'metric_id': a['metric_id'],
              'severity': a['severity'],
              'message': f"{a['metric_name']} {a['deviation_percent']:.1f}% above expected"
          }
          for a in alerts
      ],
      'performance_index': self.metrics.get('performance_index', 0)
  }

  logger.info(f"Performance baseline recorded: {json.dumps(log_entry)}")

  # Also write to dedicated performance log
  perf_log_path = Path('logs/performance') / f"performance_{datetime.now().strftime('%Y%m%d')}.log"
  perf_log_path.parent.mkdir(exist_ok=True)
  with open(perf_log_path, 'a') as f:
      f.write(json.dumps(log_entry) + '\n')
  ```

### 3.9 CLI Commands Extension

- [ ] **Add Report Command**
  ```python
  # In scripts/monitoring/performance_cli.py

  def command_report(args):
      """Generate detailed performance report."""
      db = get_database_connection()

      # Query baselines in date range
      baselines = db.execute("""
          SELECT * FROM performance_baselines
          WHERE timestamp > datetime('now', '-{days} days')
          ORDER BY timestamp DESC
      """.format(days=args.days)).fetchall()

      # Generate report
      print(f"📊 Performance Report (last {args.days} days)")
      print("=" * 60)

      # Summary stats
      print(f"\nTotal baselines: {len(baselines)}")

      # Metrics summary
      for metric_id in ['APP-001', 'VAL-001', 'GEN-001', 'API-002']:
          values = [b[metric_id] for b in baselines if b.get(metric_id)]
          if values:
              print(f"\n{metric_id}:")
              print(f"  Min: {min(values):.1f}")
              print(f"  Median: {sorted(values)[len(values)//2]:.1f}")
              print(f"  Max: {max(values):.1f}")

      # Alerts summary
      alerts = db.execute("""
          SELECT severity, COUNT(*) as count
          FROM performance_alerts
          WHERE triggered_at > datetime('now', '-{days} days')
          GROUP BY severity
      """.format(days=args.days)).fetchall()

      print(f"\n📋 Alerts:")
      for row in alerts:
          print(f"  {row['severity']}: {row['count']}")
  ```

- [ ] **Add Alerts Command**
  ```bash
  # List unacknowledged alerts
  python -m scripts.monitoring.performance_cli alerts --unacknowledged

  # Acknowledge alert
  python -m scripts.monitoring.performance_cli alerts ack --id 42 --notes "Fixed by PR #123"
  ```

### 3.10 Phase 3 Verification

- [ ] **Test Regression Detection**
  ```python
  # Create synthetic regression
  tracker = PerformanceTracker.get_instance()
  tracker.record_metric('startup_time_ms', 700)  # Way over target
  tracker.record_baseline_snapshot()

  # Verify alert created
  alert = db.execute("""
      SELECT * FROM performance_alerts
      ORDER BY triggered_at DESC LIMIT 1
  """).fetchone()

  assert alert['severity'] in ['error', 'critical']
  assert alert['metric_id'] == 'startup_time_ms'
  print("✅ Regression detection works!")
  ```

- [ ] **Test Terminal Output**
  ```bash
  # Run app with intentional regression
  # Should see warning in terminal output
  streamlit run src/main.py
  # Expected:
  # ⚠️  WARNINGS:
  #   ❌ Startup Time: 700ms (expected: 400ms) ERROR
  ```

- [ ] **Test CLI Report**
  ```bash
  python -m scripts.monitoring.performance_cli report --days 7
  # Should show summary of last 7 days
  ```

- [ ] **Commit Phase 3**
  ```bash
  git add src/monitoring/regression_detector.py
  git add src/monitoring/performance_tracker.py  # Updated
  git add scripts/monitoring/performance_cli.py  # Extended
  git commit -m "feat(US-203): Phase 3 - Regression detection and alerting

  - Implement 3-tier regression detection (threshold + statistical + trend)
  - Add alert creation and storage
  - Enhance terminal output with warnings
  - Add structured JSON logging
  - Extend CLI with report and alerts commands

  Detection: >10% = warning, >20% = error, >1 std dev = anomaly
  Alerting: Terminal + logs + database
  Coverage: Automated regression detection for all metrics"
  ```

---

## Phase 4: UI Dashboard (3 days) 🎨 COMPLEX

### 4.1 Performance Tab Structure

- [ ] **Create Performance Tab**
  - [ ] Create file: `src/ui/tabs/performance_tab.py`
  - [ ] Implement `PerformanceTab` class
  - [ ] Implement `render()` method
  - [ ] Add to `TabbedInterface` tab list

### 4.2 Metric Cards

- [ ] **Implement Metric Cards**
  ```python
  def _render_metric_card(self, metric_id: str, name: str, unit: str):
      """Render a metric card with current value, target, and trend."""
      # Get current value
      current = self._get_latest_metric(metric_id)
      target = self._get_target(metric_id)
      baseline = self._get_baseline(metric_id)

      # Calculate trend (vs last 7 days)
      trend = self._calculate_trend(metric_id, days=7)

      # Status indicator
      status = "✅" if current <= target else "⚠️"

      # Render card
      st.metric(
          label=f"{status} {name}",
          value=f"{current:.0f}{unit}",
          delta=f"{trend:+.1f}%" if trend else None,
          delta_color="inverse"  # Red for increase (bad for time metrics)
      )

      # Comparison bar
      st.progress(min(1.0, current / target))
      st.caption(f"Target: {target:.0f}{unit}")
  ```

### 4.3 Trend Charts

- [ ] **Implement Trend Chart**
  ```python
  def _render_trend_chart(self, metric_id: str, time_range: str):
      """Render time-series chart for metric."""
      import plotly.graph_objects as go

      # Get data
      days = {'Last 24 Hours': 1, 'Last 7 Days': 7, 'Last 30 Days': 30}[time_range]
      data = self._get_metric_timeseries(metric_id, days=days)

      # Get baseline for reference line
      baseline = self._get_baseline(metric_id)

      # Create chart
      fig = go.Figure()

      # Actual values
      fig.add_trace(go.Scatter(
          x=[row['timestamp'] for row in data],
          y=[row['value'] for row in data],
          mode='lines+markers',
          name='Actual',
          line=dict(color='#1f77b4', width=2)
      ))

      # Baseline (median)
      fig.add_trace(go.Scatter(
          x=[data[0]['timestamp'], data[-1]['timestamp']],
          y=[baseline['median'], baseline['median']],
          mode='lines',
          name='Baseline (median)',
          line=dict(color='green', dash='dash')
      ))

      # Baseline band (p5-p95)
      fig.add_trace(go.Scatter(
          x=[row['timestamp'] for row in data],
          y=[baseline['p95']] * len(data),
          mode='lines',
          name='95th percentile',
          line=dict(color='orange', dash='dot'),
          fill=None
      ))

      fig.add_trace(go.Scatter(
          x=[row['timestamp'] for row in data],
          y=[baseline['p5']] * len(data),
          mode='lines',
          name='5th percentile',
          line=dict(color='orange', dash='dot'),
          fill='tonexty',
          fillcolor='rgba(255, 165, 0, 0.1)'
      ))

      # Layout
      fig.update_layout(
          title=f"{metric_id} Trend",
          xaxis_title="Time",
          yaxis_title="Value",
          hovermode='x unified'
      )

      st.plotly_chart(fig, use_container_width=True)
  ```

### 4.4 Alert Table

- [ ] **Implement Alert Table**
  ```python
  def _render_alert_table(self):
      """Render table of recent alerts."""
      alerts = self._get_recent_alerts(days=7, acknowledged=False)

      if not alerts:
          st.info("No recent alerts")
          return

      # Convert to DataFrame
      import pandas as pd
      df = pd.DataFrame(alerts)

      # Format columns
      df['triggered_at'] = pd.to_datetime(df['triggered_at']).dt.strftime('%Y-%m-%d %H:%M')
      df['severity'] = df['severity'].apply(lambda s: {
          'warning': '⚠️ Warning',
          'error': '❌ Error',
          'critical': '🚨 Critical'
      }[s])

      # Display table
      st.dataframe(
          df[['triggered_at', 'severity', 'metric_name', 'current_value', 'expected_value', 'deviation_percent']],
          use_container_width=True
      )

      # Acknowledge buttons
      for idx, alert in enumerate(alerts):
          col1, col2 = st.columns([3, 1])
          with col2:
              if st.button(f"Acknowledge #{alert['id']}", key=f"ack_{idx}"):
                  self._acknowledge_alert(alert['id'], notes=st.session_state.get(f'notes_{idx}', ''))
                  st.rerun()
  ```

### 4.5 Export Functionality

- [ ] **Add Export Button**
  ```python
  if st.button("📥 Export Performance Report"):
      # Generate report
      report_path = self._export_report(format='csv', days=30)

      # Provide download link
      with open(report_path, 'rb') as f:
          st.download_button(
              label="Download CSV",
              data=f,
              file_name=Path(report_path).name,
              mime='text/csv'
          )
  ```

### 4.6 Time Range Filtering

- [ ] **Add Time Range Selector**
  ```python
  time_range = st.selectbox(
      "Time Range",
      ["Last 24 Hours", "Last 7 Days", "Last 30 Days"],
      index=1  # Default to 7 days
  )

  # Use time_range in all queries
  days = {'Last 24 Hours': 1, 'Last 7 Days': 7, 'Last 30 Days': 30}[time_range]
  ```

### 4.7 Performance Index Visualization

- [ ] **Add Performance Index Gauge**
  ```python
  def _render_performance_index_gauge(self):
      """Render gauge chart for overall performance index."""
      import plotly.graph_objects as go

      current_index = self._get_latest_metric('performance_index')

      fig = go.Figure(go.Indicator(
          mode="gauge+number+delta",
          value=current_index,
          title={'text': "Performance Index"},
          delta={'reference': 80},  # Target index
          gauge={
              'axis': {'range': [None, 100]},
              'bar': {'color': "darkblue"},
              'steps': [
                  {'range': [0, 60], 'color': "lightgray"},
                  {'range': [60, 80], 'color': "yellow"},
                  {'range': [80, 100], 'color': "lightgreen"}
              ],
              'threshold': {
                  'line': {'color': "red", 'width': 4},
                  'thickness': 0.75,
                  'value': 90
              }
          }
      ))

      st.plotly_chart(fig, use_container_width=True)
  ```

### 4.8 Phase 4 Verification

- [ ] **Test UI Rendering**
  ```bash
  streamlit run src/main.py
  # Navigate to Performance tab
  # Verify:
  # - Metric cards display correctly
  # - Trend charts render with data
  # - Alert table shows recent alerts
  # - Export button works
  ```

- [ ] **Test Interactivity**
  - [ ] Change time range selector → charts update
  - [ ] Click acknowledge button → alert disappears
  - [ ] Export report → CSV downloads

- [ ] **Commit Phase 4**
  ```bash
  git add src/ui/tabs/performance_tab.py
  git add src/ui/tabbed_interface.py  # Added performance tab
  git commit -m "feat(US-203): Phase 4 - Performance dashboard UI

  - Add Performance tab to Streamlit UI
  - Implement metric cards with current/target/trend
  - Add trend charts with baseline bands (plotly)
  - Add alert table with acknowledge functionality
  - Add export to CSV functionality
  - Add performance index gauge

  UI: Interactive dashboard for performance monitoring
  Charts: Time-series with baseline visualization
  Coverage: All metrics visible and actionable"
  ```

---

## Phase 5: CI/CD Integration (1 day) 🚀 MEDIUM

### 5.1 Performance Benchmark Script

- [ ] **Create Benchmark Script**
  - [ ] Create file: `scripts/monitoring/run_performance_benchmarks.py`
  - [ ] Run all core operations (startup, validation, generation)
  - [ ] Record metrics to JSON file
  - [ ] Handle errors gracefully

- [ ] **Test Benchmark Script**
  ```bash
  python scripts/monitoring/run_performance_benchmarks.py --output results.json

  # Verify output
  cat results.json
  # Should contain all core metrics
  ```

### 5.2 Baseline Comparison Script

- [ ] **Create Comparison Script**
  - [ ] Create file: `scripts/monitoring/compare_performance.py`
  - [ ] Load current results (PR branch)
  - [ ] Load baseline results (main branch)
  - [ ] Compare each metric with threshold
  - [ ] Output comparison JSON

- [ ] **Test Comparison**
  ```bash
  python scripts/monitoring/compare_performance.py \
      --current results.json \
      --baseline main_baseline.json \
      --threshold 10 \
      --output comparison.json

  cat comparison.json
  # Should show improved/regressed/unchanged metrics
  ```

### 5.3 GitHub Actions Workflow

- [ ] **Create Workflow File**
  - [ ] Create file: `.github/workflows/performance-check.yml`
  - [ ] Add trigger: `pull_request` on `main`
  - [ ] Add steps:
    - [ ] Checkout code
    - [ ] Setup Python
    - [ ] Install dependencies
    - [ ] Run benchmarks on PR branch
    - [ ] Checkout main branch
    - [ ] Run benchmarks on main branch
    - [ ] Compare results
    - [ ] Post comment to PR

- [ ] **Test Workflow Locally**
  ```bash
  # Install act (GitHub Actions local runner)
  brew install act

  # Run workflow locally
  act pull_request
  ```

### 5.4 PR Comment Template

- [ ] **Create Comment Generator**
  ```python
  def generate_pr_comment(comparison: dict) -> str:
      """Generate markdown comment for PR."""
      improved = comparison['improved']
      regressed = comparison['regressed']
      unchanged = comparison['unchanged']

      comment = f"""## 📊 Performance Report

  **Branch:** `{comparison['branch']}`
  **Commit:** `{comparison['commit']}`
  **Baseline:** `main` (commit: `{comparison['baseline_commit']}`)

  ### Results

  | Metric | Current | Baseline | Change | Status |
  |--------|---------|----------|--------|--------|
  """

      for metric in comparison['all_metrics']:
          current = metric['current']
          baseline = metric['baseline']
          change = metric['change_percent']
          status = "✅" if change < 0 else "⚠️" if change < 10 else "❌"

          comment += f"| {metric['name']} | {current:.0f}{metric['unit']} | {baseline:.0f}{metric['unit']} | {change:+.1f}% | {status} |\n"

      comment += f"""
  ### Summary

  ✅ **{len(improved)} metrics improved**
  ⚠️ **{len(regressed)} metrics regressed** (within threshold)
  ❌ **{len([m for m in regressed if m['change_percent'] > 20])} critical regressions**

  **Overall:** {comparison['verdict']}
  """

      return comment
  ```

### 5.5 Failure Criteria

- [ ] **Define When to Fail CI**
  ```python
  def should_fail_ci(comparison: dict) -> bool:
      """Determine if CI should fail based on performance regressions."""
      # Fail if any metric regressed >20%
      critical_regressions = [
          m for m in comparison['regressed']
          if m['change_percent'] > 20
      ]

      # Fail if performance index dropped >15%
      perf_index_drop = comparison['metrics'].get('performance_index', {}).get('change_percent', 0)

      return len(critical_regressions) > 0 or perf_index_drop < -15
  ```

### 5.6 Phase 5 Verification

- [ ] **Test PR Workflow**
  1. Create test PR with intentional regression
  2. Verify workflow runs
  3. Verify comment posted to PR
  4. Verify CI fails on critical regression

- [ ] **Test PR Workflow (Success)**
  1. Create test PR with optimization
  2. Verify workflow runs
  3. Verify comment shows improvements
  4. Verify CI passes

- [ ] **Commit Phase 5**
  ```bash
  git add .github/workflows/performance-check.yml
  git add scripts/monitoring/run_performance_benchmarks.py
  git add scripts/monitoring/compare_performance.py
  git commit -m "feat(US-203): Phase 5 - CI/CD performance checks

  - Add GitHub Actions workflow for PR performance checks
  - Implement benchmark script for automated testing
  - Implement comparison script with threshold checking
  - Add PR comment generation with markdown table
  - Fail CI on critical regressions (>20%)

  CI/CD: Automated performance regression detection in PRs
  Threshold: Warning at 10%, fail at 20%
  Coverage: All core metrics checked on every PR"
  ```

---

## Final Verification & Cleanup

### End-to-End Testing

- [ ] **Test Complete Flow**
  1. Start app → verify baseline recorded
  2. Check terminal output → verify summary shown
  3. Check database → verify all metrics populated
  4. Open Performance tab → verify UI renders
  5. Create intentional regression → verify alert shown
  6. Run CLI report → verify data accurate
  7. Export to CSV → verify export works

- [ ] **Performance Overhead Check**
  ```python
  # Measure total overhead
  import time
  start = time.perf_counter()
  # Run full app startup with tracking
  overhead = (time.perf_counter() - start) * 1000
  assert overhead < 50, f"Overhead too high: {overhead}ms"
  print(f"✅ Total overhead: {overhead:.1f}ms")
  ```

- [ ] **Database Size Check**
  ```bash
  ls -lh data/definities.db
  # Should be reasonable size (a few MB after 30 days)
  ```

### Documentation

- [ ] **Update CLAUDE.md**
  - [ ] Add section on performance tracking
  - [ ] Document CLI commands
  - [ ] Document UI dashboard
  - [ ] Link to design documents

- [ ] **Update README.md**
  - [ ] Add performance tracking section
  - [ ] Add CLI examples
  - [ ] Add screenshots of dashboard

- [ ] **Create User Guide**
  - [ ] Create file: `docs/guides/performance-tracking-guide.md`
  - [ ] Explain how to use dashboard
  - [ ] Explain how to interpret alerts
  - [ ] Explain how to acknowledge alerts

### Code Review Preparation

- [ ] **Self-Review Checklist**
  - [ ] All files have docstrings
  - [ ] All functions have type hints
  - [ ] All tests pass
  - [ ] No hardcoded values (use config)
  - [ ] No debug print statements
  - [ ] Consistent code style (ruff + black)

- [ ] **Run Code Quality Checks**
  ```bash
  # Linting
  ruff check src/monitoring/ scripts/monitoring/

  # Formatting
  black --check src/monitoring/ scripts/monitoring/

  # Type checking (if using mypy)
  mypy src/monitoring/

  # Tests
  pytest tests/monitoring/ -v

  # Coverage
  pytest --cov=src/monitoring --cov-report=html
  ```

### Final Commit & PR

- [ ] **Merge Commits into Squash Commit**
  ```bash
  # Squash all phase commits
  git rebase -i main

  # Create final commit message
  git commit --amend -m "feat(US-203): Performance baseline tracking system

  Implement comprehensive performance tracking with automated
  regression detection and alerting.

  Features:
  - Track 13 core + 8 secondary metrics (21 total)
  - 3-tier regression detection (threshold + statistical + trend)
  - SQLite storage with 30-day retention
  - Streamlit dashboard with charts
  - CLI tools for querying and reporting
  - CI/CD integration with GitHub Actions

  Performance:
  - Overhead: <50ms (<1.25% of startup)
  - Database: ~300KB/month
  - Memory: <100KB footprint

  Coverage:
  - APP-001: Application startup time
  - SVC-001/002: Container initialization
  - VAL-001/002/003: Validation metrics
  - GEN-001: Definition generation
  - API-001/002/003: API metrics
  - EXP-001: Export operations
  - MEM-001/002: Memory usage

  References:
  - Design: docs/architectuur/performance-baseline-tracking-design.md
  - Architecture: docs/architectuur/performance-baseline-tracking-architecture.md
  - User Guide: docs/guides/performance-tracking-guide.md

  Closes #203"
  ```

- [ ] **Create Pull Request**
  ```bash
  git push origin feature/US-203-performance-tracking

  # Create PR via GitHub CLI
  gh pr create \
      --title "feat(US-203): Performance baseline tracking system" \
      --body "$(cat PR_TEMPLATE.md)" \
      --label "enhancement,performance"
  ```

- [ ] **PR Checklist**
  - [ ] All tests pass
  - [ ] Performance overhead verified (<50ms)
  - [ ] Documentation updated
  - [ ] Screenshots added to PR
  - [ ] Breaking changes documented (none expected)
  - [ ] Migration script tested

---

## Post-Deployment

### Monitoring

- [ ] **Week 1: Monitor Adoption**
  - [ ] Verify baselines being recorded (100% of runs)
  - [ ] Check database growth (should be ~10KB/day)
  - [ ] Monitor overhead (should be <50ms)
  - [ ] Review initial alerts (tune thresholds if needed)

- [ ] **Week 2: Gather Feedback**
  - [ ] Survey developers on usefulness
  - [ ] Identify false positives
  - [ ] Adjust thresholds based on real data
  - [ ] Fix any bugs reported

- [ ] **Month 1: Evaluate Effectiveness**
  - [ ] Count regressions caught early
  - [ ] Measure API cost savings
  - [ ] Assess developer satisfaction
  - [ ] Plan improvements for Phase 6

### Iteration

- [ ] **Phase 6: Advanced Features (Future)**
  - [ ] Anomaly detection (ML-based)
  - [ ] Flame graph integration
  - [ ] Slack/email alerting
  - [ ] A/B test performance comparison
  - [ ] Custom metric definitions

---

## Success Criteria Summary

### After 30 Days
- [x] 100% of app starts record baselines
- [x] 80% of core operations instrumented
- [x] 50+ baselines per metric (high confidence)
- [x] 10+ alerts triggered (system working)
- [x] 5+ alerts acknowledged (team engaging)

### After 60 Days
- [x] 3+ regressions caught before production
- [x] 2+ optimizations driven by data
- [x] 20% API cost reduction
- [x] 0 critical issues missed

### Developer Experience
- [x] 4+ stars: "Performance tracking is useful"
- [x] 4+ stars: "Overhead is acceptable"
- [x] 4+ stars: "UI dashboard is helpful"

---

**Estimated Total Time:** 4-5 days (core), 7-8 days (with UI)
**Risk Level:** MEDIUM (manageable with phased approach)
**ROI:** HIGH (catch regressions early, reduce API costs, data-driven optimization)

**Ready to start?** Begin with Phase 1 (4 hours) and iterate!
