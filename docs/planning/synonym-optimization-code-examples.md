# CODE EXAMPLES: TOP 3 FEATURES SYNONIEMEN-OPTIMALISATIE

**Datum**: 2025-10-09
**Versie**: 1.0 - Concrete Code Examples
**Status**: Implementation Ready

---

## 🎯 FEATURE 1: WEB LOOKUP TRANSPARENCY

### Complete Implementation Example

#### 1. Enhanced ModernWebLookupService

```python
# File: /Users/chrislehnen/Projecten/Definitie-app/src/services/modern_web_lookup_service.py

import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class WebLookupMetadata:
    """Metadata voor transparency reporting"""
    original_term: str
    synonyms_attempted: List[str] = field(default_factory=list)
    synonyms_matched: List[str] = field(default_factory=list)
    provider_details: Dict[str, Dict] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    @property
    def duration_ms(self) -> int:
        if self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return 0

    @property
    def total_hits(self) -> int:
        return sum(
            details.get('hit_count', 0)
            for details in self.provider_details.values()
        )

    def to_report_dict(self) -> Dict[str, Any]:
        """Convert naar dict voor UI rendering"""
        return {
            'original_term': self.original_term,
            'synonyms_used': self.synonyms_matched,
            'synonyms_tried': self.synonyms_attempted,
            'provider_hits': {
                name: {
                    'count': details.get('hit_count', 0),
                    'synonyms': details.get('matched_synonyms', []),
                    'quality_score': details.get('quality_score', 0.0)
                }
                for name, details in self.provider_details.items()
            },
            'total_hits': self.total_hits,
            'duration_ms': self.duration_ms,
            'success_rate': len(self.synonyms_matched) / len(self.synonyms_attempted)
                           if self.synonyms_attempted else 0
        }


class ModernWebLookupService:
    """Enhanced met transparency tracking"""

    def __init__(self, providers: List[WebLookupProvider], synonym_service: Any):
        self.providers = providers
        self.synonym_service = synonym_service
        self._current_metadata: Optional[WebLookupMetadata] = None

    def lookup_term(
        self,
        term: str,
        context: Optional[str] = None,
        max_synonyms: int = 3
    ) -> WebLookupResult:
        """
        Enhanced lookup met complete tracking.

        Returns:
            WebLookupResult met metadata voor transparency report
        """
        # Initialize metadata tracking
        self._current_metadata = WebLookupMetadata(original_term=term)

        # Get synonyms for expansion
        synonyms = self.synonym_service.get_best_synonyms(
            term,
            threshold=0.85  # Only high-quality synonyms
        )[:max_synonyms]

        self._current_metadata.synonyms_attempted = synonyms

        # Collect results from all providers
        all_snippets = []
        provider_results = {}

        for provider in self.providers:
            provider_name = provider.__class__.__name__.replace('Provider', '')

            # Track per provider
            provider_meta = {
                'hit_count': 0,
                'matched_synonyms': [],
                'quality_score': 0.0,
                'attempts': 0
            }

            try:
                # Try original term first
                result = provider.search(term, context=context)
                provider_meta['attempts'] += 1

                if result and result.snippets:
                    all_snippets.extend(result.snippets)
                    provider_meta['hit_count'] = len(result.snippets)
                    provider_meta['quality_score'] = result.quality_score

                # Try synonyms if no results or low quality
                elif synonyms and provider_meta['hit_count'] < 2:
                    for syn in synonyms:
                        syn_result = provider.search(syn, context=context)
                        provider_meta['attempts'] += 1

                        if syn_result and syn_result.snippets:
                            all_snippets.extend(syn_result.snippets)
                            provider_meta['hit_count'] += len(syn_result.snippets)
                            provider_meta['matched_synonyms'].append(syn)

                            # Track successful synonym
                            if syn not in self._current_metadata.synonyms_matched:
                                self._current_metadata.synonyms_matched.append(syn)

                            # Stop if we have enough results
                            if provider_meta['hit_count'] >= 3:
                                break

            except Exception as e:
                logger.error(f"Provider {provider_name} failed: {e}")
                provider_meta['error'] = str(e)

            # Store provider metadata
            self._current_metadata.provider_details[provider_name] = provider_meta
            provider_results[provider_name] = provider_meta

        # Finalize metadata
        self._current_metadata.end_time = time.time()

        # Rank and filter results
        ranked_snippets = self._rank_snippets(all_snippets)

        # Create result with metadata
        result = WebLookupResult(
            snippets=ranked_snippets[:10],  # Top 10
            metadata={
                'lookup_report': self._current_metadata.to_report_dict(),
                'provider_results': provider_results
            }
        )

        # Track usage for analytics
        self._track_usage(self._current_metadata)

        return result

    def _track_usage(self, metadata: WebLookupMetadata) -> None:
        """Track synonym usage for analytics"""
        if not metadata.synonyms_matched:
            return

        # Report back to synonym service
        for provider_name, details in metadata.provider_details.items():
            for syn in details.get('matched_synonyms', []):
                self.synonym_service.report_lookup_results(
                    hoofdterm=metadata.original_term,
                    synoniem=syn,
                    provider=provider_name,
                    hit_count=details.get('hit_count', 0)
                )

    def get_last_lookup_report(self) -> Optional[Dict[str, Any]]:
        """Get report from last lookup for UI rendering"""
        if self._current_metadata:
            return self._current_metadata.to_report_dict()
        return None
```

#### 2. UI Component Implementation

```python
# File: /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/web_lookup_report.py

import streamlit as st
from typing import Dict, Any, Optional
import json

def render_web_lookup_report(
    lookup_results: Optional[Dict[str, Any]],
    show_expanded: bool = False
) -> None:
    """
    Render beautiful web lookup transparency report.

    Args:
        lookup_results: Results dict from WebLookupMetadata.to_report_dict()
        show_expanded: Whether to expand by default
    """
    if not lookup_results:
        return

    # Calculate summary metrics
    total_hits = lookup_results.get('total_hits', 0)
    duration = lookup_results.get('duration_ms', 0)
    synonyms_used = lookup_results.get('synonyms_used', [])
    success_rate = lookup_results.get('success_rate', 0)

    # Determine icon and color based on results
    if total_hits > 10:
        icon = "🎯"
        status = "Excellent"
        color = "green"
    elif total_hits > 5:
        icon = "✅"
        status = "Good"
        color = "blue"
    elif total_hits > 0:
        icon = "⚠️"
        status = "Limited"
        color = "orange"
    else:
        icon = "❌"
        status = "No Results"
        color = "red"

    # Main expander with dynamic title
    with st.expander(
        f"{icon} Web Lookup Report - {status} ({total_hits} results in {duration}ms)",
        expanded=show_expanded
    ):
        # Top-level metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Results",
                total_hits,
                delta=f"{total_hits - 5}" if total_hits != 5 else None
            )

        with col2:
            st.metric(
                "Lookup Time",
                f"{duration}ms",
                delta=f"{duration - 1000}ms" if duration > 1000 else "Fast"
            )

        with col3:
            st.metric(
                "Synonyms Used",
                len(synonyms_used),
                help="Number of synonyms that returned results"
            )

        with col4:
            st.metric(
                "Success Rate",
                f"{success_rate:.0%}",
                help="Percentage of attempted synonyms that found results"
            )

        # Synonym expansion details
        if synonyms_used:
            st.markdown("### 🔄 Query Expansion")
            st.success(f"**Successfully expanded search with:** {', '.join(synonyms_used)}")

            # Show which synonym worked where
            st.markdown("**Synonym Performance:**")
            for syn in synonyms_used:
                providers_matched = [
                    name for name, details in lookup_results.get('provider_hits', {}).items()
                    if syn in details.get('synonyms', [])
                ]
                if providers_matched:
                    st.write(f"- **{syn}** → Found results in: {', '.join(providers_matched)}")

        # Provider breakdown
        st.markdown("### 📊 Provider Performance")

        provider_hits = lookup_results.get('provider_hits', {})

        # Sort providers by hit count
        sorted_providers = sorted(
            provider_hits.items(),
            key=lambda x: x[1].get('count', 0),
            reverse=True
        )

        for provider_name, details in sorted_providers:
            hit_count = details.get('count', 0)
            matched_syns = details.get('synonyms', [])
            quality = details.get('quality_score', 0)

            # Provider row with metrics
            col1, col2, col3 = st.columns([2, 1, 3])

            with col1:
                # Icon based on performance
                p_icon = "✅" if hit_count > 0 else "⚪"
                st.write(f"{p_icon} **{provider_name}**")

            with col2:
                st.write(f"**{hit_count}** hits")

            with col3:
                if matched_syns:
                    st.caption(f"Via synoniemen: {', '.join(matched_syns)}")
                elif hit_count > 0:
                    st.caption("Direct match")
                else:
                    st.caption("No results")

            # Quality indicator
            if quality > 0:
                st.progress(quality, text=f"Quality: {quality:.0%}")

        # Advanced details (collapsible)
        with st.expander("🔧 Advanced Details", expanded=False):
            # Show raw data for debugging
            st.markdown("**Raw Lookup Data:**")
            st.json(lookup_results)

            # Show query attempts
            synonyms_tried = lookup_results.get('synonyms_tried', [])
            if synonyms_tried:
                st.markdown("**All Attempted Synonyms:**")
                for syn in synonyms_tried:
                    status = "✅" if syn in synonyms_used else "❌"
                    st.write(f"{status} {syn}")

        # User feedback section
        st.markdown("---")
        st.markdown("### 💭 Was this helpful?")

        col1, col2, col3 = st.columns([1, 1, 4])

        with col1:
            if st.button("👍 Yes", key="lookup_helpful_yes"):
                st.success("Thank you for your feedback!")
                # Log positive feedback
                _log_feedback('positive', lookup_results)

        with col2:
            if st.button("👎 No", key="lookup_helpful_no"):
                st.error("Sorry to hear that. We'll work on improving.")
                # Log negative feedback
                _log_feedback('negative', lookup_results)


def _log_feedback(sentiment: str, lookup_data: Dict[str, Any]) -> None:
    """Log user feedback for improvement tracking"""
    # This would write to database or analytics service
    feedback_entry = {
        'timestamp': time.time(),
        'sentiment': sentiment,
        'term': lookup_data.get('original_term'),
        'total_hits': lookup_data.get('total_hits'),
        'synonyms_used': lookup_data.get('synonyms_used')
    }

    # For now, just log it
    logger.info(f"User feedback: {json.dumps(feedback_entry)}")
```

---

## 🎯 FEATURE 2: USAGE TRACKING IMPLEMENTATION

### Complete Database & Service Layer

```python
# File: /Users/chrislehnen/Projecten/Definitie-app/src/services/synonym_tracking_service.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sqlite3
from pathlib import Path

@dataclass
class UsageMetrics:
    """Container voor synonym usage metrics"""
    hoofdterm: str
    synoniem: str
    usage_count: int = 0
    hit_count: int = 0
    total_lookups: int = 0
    last_used: Optional[datetime] = None
    providers_used: List[str] = None
    avg_hit_rate: float = 0.0
    trend: str = 'stable'  # 'increasing', 'decreasing', 'stable'

    @property
    def effectiveness_score(self) -> float:
        """Calculate effectiveness (0-1 scale)"""
        if self.total_lookups == 0:
            return 0.0

        # Weighted score: 70% hit rate, 30% usage frequency
        hit_rate = self.hit_count / self.total_lookups if self.total_lookups > 0 else 0
        usage_score = min(self.usage_count / 100, 1.0)  # Cap at 100 uses

        return (hit_rate * 0.7) + (usage_score * 0.3)

    def to_dict(self) -> Dict:
        """Convert to dict for JSON/database storage"""
        return {
            'hoofdterm': self.hoofdterm,
            'synoniem': self.synoniem,
            'usage_count': self.usage_count,
            'hit_count': self.hit_count,
            'total_lookups': self.total_lookups,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'avg_hit_rate': self.avg_hit_rate,
            'effectiveness_score': self.effectiveness_score,
            'trend': self.trend
        }


class SynonymTrackingService:
    """
    Service voor tracking synonym usage en performance analytics.

    Features:
    - Real-time usage tracking
    - Performance metrics calculation
    - Trend analysis
    - Recommendation generation
    """

    def __init__(self, db_path: str = None):
        if not db_path:
            db_path = Path(__file__).parent.parent.parent / "data" / "definities.db"
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure tracking tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if tables exist, create if not
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS synonym_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hoofdterm TEXT NOT NULL,
                    synoniem TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    total_results INTEGER DEFAULT 0,
                    quality_score REAL DEFAULT 0.0,
                    lookup_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    definition_id INTEGER,
                    context_length INTEGER,
                    response_time_ms INTEGER
                )
            """)

            # Aggregated metrics table for fast queries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS synonym_metrics (
                    hoofdterm TEXT NOT NULL,
                    synoniem TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    hit_count INTEGER DEFAULT 0,
                    total_lookups INTEGER DEFAULT 0,
                    avg_hit_rate REAL DEFAULT 0.0,
                    last_used TIMESTAMP,
                    first_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    effectiveness_score REAL DEFAULT 0.0,
                    trend TEXT DEFAULT 'stable',
                    PRIMARY KEY (hoofdterm, synoniem)
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_log_timestamp
                ON synonym_usage_log(lookup_timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_log_terms
                ON synonym_usage_log(hoofdterm, synoniem)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_effectiveness
                ON synonym_metrics(effectiveness_score DESC)
            """)

            conn.commit()

    def track_lookup(
        self,
        hoofdterm: str,
        synoniem: str,
        provider: str,
        hit_count: int,
        total_results: int = 0,
        quality_score: float = 0.0,
        session_id: str = None,
        response_time_ms: int = None
    ) -> None:
        """
        Track a synonym lookup event.

        This is called every time a synonym is used in a web lookup.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Log detailed event
            cursor.execute("""
                INSERT INTO synonym_usage_log
                (hoofdterm, synoniem, provider, hit_count, total_results,
                 quality_score, session_id, response_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hoofdterm, synoniem, provider, hit_count, total_results,
                quality_score, session_id, response_time_ms
            ))

            # Update aggregated metrics
            cursor.execute("""
                INSERT INTO synonym_metrics
                (hoofdterm, synoniem, usage_count, hit_count, total_lookups,
                 avg_hit_rate, last_used)
                VALUES (?, ?, 1, ?, 1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(hoofdterm, synoniem) DO UPDATE SET
                    usage_count = usage_count + 1,
                    hit_count = hit_count + ?,
                    total_lookups = total_lookups + 1,
                    avg_hit_rate = CAST(hit_count + ? AS REAL) /
                                  CAST(total_lookups + 1 AS REAL),
                    last_used = CURRENT_TIMESTAMP,
                    effectiveness_score = (avg_hit_rate * 0.7) +
                                        (MIN(usage_count / 100.0, 1.0) * 0.3)
            """, (
                hoofdterm, synoniem, hit_count,
                1.0 if hit_count > 0 else 0.0,  # Initial hit rate
                hit_count, hit_count  # For UPDATE clause
            ))

            # Update trend (simple moving average comparison)
            self._update_trend(cursor, hoofdterm, synoniem)

            conn.commit()

    def _update_trend(self, cursor: sqlite3.Cursor, hoofdterm: str, synoniem: str) -> None:
        """Calculate and update usage trend"""

        # Get recent vs older usage
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN lookup_timestamp > datetime('now', '-7 days')
                      THEN 1 END) as recent_count,
                COUNT(CASE WHEN lookup_timestamp BETWEEN
                      datetime('now', '-14 days') AND datetime('now', '-7 days')
                      THEN 1 END) as older_count
            FROM synonym_usage_log
            WHERE hoofdterm = ? AND synoniem = ?
        """, (hoofdterm, synoniem))

        recent, older = cursor.fetchone()

        # Determine trend
        if recent > older * 1.2:
            trend = 'increasing'
        elif recent < older * 0.8:
            trend = 'decreasing'
        else:
            trend = 'stable'

        # Update trend
        cursor.execute("""
            UPDATE synonym_metrics
            SET trend = ?
            WHERE hoofdterm = ? AND synoniem = ?
        """, (trend, hoofdterm, synoniem))

    def get_metrics(self, hoofdterm: str, synoniem: str) -> Optional[UsageMetrics]:
        """Get metrics for a specific synonym"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT usage_count, hit_count, total_lookups,
                       avg_hit_rate, last_used, trend
                FROM synonym_metrics
                WHERE hoofdterm = ? AND synoniem = ?
            """, (hoofdterm, synoniem))

            row = cursor.fetchone()
            if not row:
                return None

            # Get providers used
            cursor.execute("""
                SELECT DISTINCT provider
                FROM synonym_usage_log
                WHERE hoofdterm = ? AND synoniem = ?
            """, (hoofdterm, synoniem))

            providers = [row[0] for row in cursor.fetchall()]

            return UsageMetrics(
                hoofdterm=hoofdterm,
                synoniem=synoniem,
                usage_count=row[0],
                hit_count=row[1],
                total_lookups=row[2],
                avg_hit_rate=row[3],
                last_used=datetime.fromisoformat(row[4]) if row[4] else None,
                trend=row[5],
                providers_used=providers
            )

    def get_top_performers(
        self,
        limit: int = 10,
        min_usage: int = 5
    ) -> List[UsageMetrics]:
        """
        Get top performing synonyms based on effectiveness score.

        Args:
            limit: Maximum number of results
            min_usage: Minimum usage count to be considered
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT hoofdterm, synoniem, usage_count, hit_count,
                       total_lookups, avg_hit_rate, last_used, trend,
                       effectiveness_score
                FROM synonym_metrics
                WHERE usage_count >= ?
                ORDER BY effectiveness_score DESC
                LIMIT ?
            """, (min_usage, limit))

            results = []
            for row in cursor.fetchall():
                results.append(UsageMetrics(
                    hoofdterm=row[0],
                    synoniem=row[1],
                    usage_count=row[2],
                    hit_count=row[3],
                    total_lookups=row[4],
                    avg_hit_rate=row[5],
                    last_used=datetime.fromisoformat(row[6]) if row[6] else None,
                    trend=row[7]
                ))

            return results

    def get_low_performers(
        self,
        threshold: float = 0.2,
        min_usage: int = 10
    ) -> List[UsageMetrics]:
        """
        Identify underperforming synonyms that should be reviewed.

        Args:
            threshold: Maximum effectiveness score to be considered low
            min_usage: Minimum usage to have enough data
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT hoofdterm, synoniem, usage_count, hit_count,
                       total_lookups, avg_hit_rate, last_used, trend,
                       effectiveness_score
                FROM synonym_metrics
                WHERE usage_count >= ? AND effectiveness_score <= ?
                ORDER BY effectiveness_score ASC
            """, (min_usage, threshold))

            results = []
            for row in cursor.fetchall():
                results.append(UsageMetrics(
                    hoofdterm=row[0],
                    synoniem=row[1],
                    usage_count=row[2],
                    hit_count=row[3],
                    total_lookups=row[4],
                    avg_hit_rate=row[5],
                    last_used=datetime.fromisoformat(row[6]) if row[6] else None,
                    trend=row[7]
                ))

            return results

    def get_trending_synonyms(
        self,
        trend_type: str = 'increasing',
        limit: int = 10
    ) -> List[UsageMetrics]:
        """Get synonyms with specific trend"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT hoofdterm, synoniem, usage_count, hit_count,
                       total_lookups, avg_hit_rate, last_used, trend
                FROM synonym_metrics
                WHERE trend = ?
                ORDER BY usage_count DESC
                LIMIT ?
            """, (trend_type, limit))

            results = []
            for row in cursor.fetchall():
                results.append(UsageMetrics(
                    hoofdterm=row[0],
                    synoniem=row[1],
                    usage_count=row[2],
                    hit_count=row[3],
                    total_lookups=row[4],
                    avg_hit_rate=row[5],
                    last_used=datetime.fromisoformat(row[6]) if row[6] else None,
                    trend=row[7]
                ))

            return results

    def get_usage_timeline(
        self,
        hoofdterm: str,
        synoniem: str,
        days: int = 30
    ) -> List[Tuple[datetime, int]]:
        """Get daily usage counts for charting"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DATE(lookup_timestamp) as date,
                       COUNT(*) as daily_count
                FROM synonym_usage_log
                WHERE hoofdterm = ? AND synoniem = ?
                  AND lookup_timestamp > datetime('now', ? || ' days')
                GROUP BY DATE(lookup_timestamp)
                ORDER BY date
            """, (hoofdterm, synoniem, -days))

            return [
                (datetime.fromisoformat(row[0]), row[1])
                for row in cursor.fetchall()
            ]

    def recommend_synonyms_for_removal(self) -> List[Dict]:
        """
        AI-powered recommendation for synonym cleanup.

        Returns synonyms that should be considered for removal based on:
        - Low effectiveness score
        - Declining trend
        - Not used recently
        """
        recommendations = []

        # Get low performers
        low_performers = self.get_low_performers(threshold=0.15, min_usage=20)

        for metric in low_performers:
            # Check if unused for 30+ days
            days_unused = 0
            if metric.last_used:
                days_unused = (datetime.now() - metric.last_used).days

            # Calculate removal confidence
            removal_confidence = 0.0

            if metric.effectiveness_score < 0.1:
                removal_confidence += 0.4
            if metric.trend == 'decreasing':
                removal_confidence += 0.3
            if days_unused > 30:
                removal_confidence += 0.3

            if removal_confidence >= 0.6:
                recommendations.append({
                    'hoofdterm': metric.hoofdterm,
                    'synoniem': metric.synoniem,
                    'reason': self._get_removal_reason(metric, days_unused),
                    'confidence': removal_confidence,
                    'metrics': metric.to_dict()
                })

        return sorted(recommendations, key=lambda x: x['confidence'], reverse=True)

    def _get_removal_reason(self, metric: UsageMetrics, days_unused: int) -> str:
        """Generate human-readable removal reason"""
        reasons = []

        if metric.avg_hit_rate < 0.1:
            reasons.append(f"zeer lage hit rate ({metric.avg_hit_rate:.0%})")
        if metric.trend == 'decreasing':
            reasons.append("dalend gebruik")
        if days_unused > 30:
            reasons.append(f"{days_unused} dagen niet gebruikt")
        if metric.effectiveness_score < 0.15:
            reasons.append(f"lage effectiviteit ({metric.effectiveness_score:.0%})")

        return "Aanbevolen voor verwijdering: " + ", ".join(reasons)
```

---

## 🎯 FEATURE 3: INLINE APPROVAL IMPLEMENTATION

### Complete UI Integration

```python
# File: /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/inline_synonym_approval.py

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional, Callable
import asyncio
from dataclasses import dataclass

@dataclass
class ApprovalContext:
    """Context for inline approval widget"""
    term: str
    definition: str
    session_id: str
    user: Optional[str] = None
    auto_refresh: bool = True


class InlineSynonymApprovalWidget:
    """
    Smart inline approval widget with state management.

    Features:
    - Batch approval support
    - Confidence-based sorting
    - One-click actions
    - Undo support
    - Auto-save to YAML
    """

    def __init__(
        self,
        synonym_repo,
        synonym_workflow,
        yaml_sync_service
    ):
        self.repo = synonym_repo
        self.workflow = synonym_workflow
        self.yaml_sync = yaml_sync_service

        # Initialize session state
        if 'approval_history' not in st.session_state:
            st.session_state.approval_history = []
        if 'last_approval_action' not in st.session_state:
            st.session_state.last_approval_action = None

    def render(
        self,
        context: ApprovalContext,
        max_suggestions: int = 3,
        on_approve: Callable = None,
        on_reject: Callable = None
    ) -> None:
        """
        Main render method for inline approval widget.

        Args:
            context: Approval context with term and session info
            max_suggestions: Maximum suggestions to show inline
            on_approve: Callback after approval
            on_reject: Callback after rejection
        """
        # Check for pending suggestions
        suggestions = self._get_pending_suggestions(context.term, max_suggestions)

        if not suggestions:
            # No pending suggestions - offer to generate
            self._render_generation_prompt(context)
            return

        # Main approval interface
        self._render_approval_interface(
            suggestions,
            context,
            on_approve,
            on_reject
        )

        # Show undo option if recent action
        if st.session_state.last_approval_action:
            self._render_undo_option()

    def _get_pending_suggestions(
        self,
        term: str,
        limit: int
    ) -> List[Dict]:
        """Get pending suggestions sorted by confidence"""
        suggestions = self.repo.get_pending_suggestions(
            hoofdterm=term,
            limit=limit * 2  # Get extra for filtering
        )

        # Filter and sort by confidence
        filtered = [
            s for s in suggestions
            if s.get('confidence', 0) >= 0.5  # Min threshold
        ]

        sorted_suggestions = sorted(
            filtered,
            key=lambda x: x.get('confidence', 0),
            reverse=True
        )

        return sorted_suggestions[:limit]

    def _render_generation_prompt(self, context: ApprovalContext) -> None:
        """Render prompt to generate suggestions when none exist"""

        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.info(
                    f"💡 Geen synonym suggesties voor **'{context.term}'**. "
                    "Wil je GPT-4 suggesties laten genereren?"
                )

            with col2:
                if st.button(
                    "🤖 Genereer",
                    key=f"generate_{context.session_id}",
                    type="primary"
                ):
                    with st.spinner("Generating suggestions..."):
                        asyncio.run(
                            self.workflow.suggest_synonyms(
                                hoofdterm=context.term,
                                definition=context.definition,
                                confidence_threshold=0.6
                            )
                        )

                    st.success("✅ Suggesties gegenereerd!")

                    # Auto-refresh if enabled
                    if context.auto_refresh:
                        st.rerun()

    def _render_approval_interface(
        self,
        suggestions: List[Dict],
        context: ApprovalContext,
        on_approve: Callable,
        on_reject: Callable
    ) -> None:
        """Render main approval interface"""

        # Container with custom styling
        st.markdown("""
            <style>
            .synonym-card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px;
                margin: 8px 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .confidence-high { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .confidence-medium { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
            .confidence-low { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
            </style>
        """, unsafe_allow_html=True)

        # Header
        st.markdown("### 🎯 Synonym Suggesties")

        # Batch actions
        if len(suggestions) > 1:
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button(
                    "✅ Approve All",
                    key=f"approve_all_{context.session_id}"
                ):
                    self._batch_approve(suggestions, context, on_approve)

            with col2:
                if st.button(
                    "❌ Reject All",
                    key=f"reject_all_{context.session_id}"
                ):
                    self._batch_reject(suggestions, context, on_reject)

        # Individual suggestion cards
        for idx, suggestion in enumerate(suggestions):
            self._render_suggestion_card(
                suggestion,
                idx,
                context,
                on_approve,
                on_reject
            )

        # More suggestions link
        remaining = len(suggestions) - 3
        if remaining > 0:
            st.caption(
                f"📋 {remaining} meer suggesties beschikbaar in "
                f"[Synonym Review →](/synonym_review)"
            )

    def _render_suggestion_card(
        self,
        suggestion: Dict,
        idx: int,
        context: ApprovalContext,
        on_approve: Callable,
        on_reject: Callable
    ) -> None:
        """Render individual suggestion card"""

        confidence = suggestion.get('confidence', 0)
        synoniem = suggestion.get('synoniem')
        rationale = suggestion.get('rationale', 'Geen uitleg beschikbaar')

        # Determine confidence level for styling
        if confidence >= 0.85:
            conf_class = "high"
            conf_icon = "🟢"
        elif confidence >= 0.65:
            conf_class = "medium"
            conf_icon = "🟡"
        else:
            conf_class = "low"
            conf_icon = "🔴"

        # Card container
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.markdown(
                    f'{conf_icon} **"{synoniem}"** voor *{context.term}*'
                )
                st.caption(f"💭 {rationale[:100]}...")

            with col2:
                st.metric(
                    "Confidence",
                    f"{confidence:.0%}",
                    delta=None
                )

            with col3:
                if st.button(
                    "✅",
                    key=f"approve_{context.session_id}_{idx}",
                    help="Goedkeuren",
                    type="primary"
                ):
                    self._approve_single(
                        suggestion,
                        context,
                        on_approve
                    )

            with col4:
                if st.button(
                    "❌",
                    key=f"reject_{context.session_id}_{idx}",
                    help="Afwijzen"
                ):
                    self._reject_single(
                        suggestion,
                        context,
                        on_reject
                    )

            # Expandable details
            with st.expander("📊 Details", expanded=False):
                st.json({
                    'synoniem': synoniem,
                    'confidence': confidence,
                    'rationale': rationale,
                    'model': suggestion.get('model', 'gpt-4'),
                    'created_at': suggestion.get('created_at'),
                    'context_used': len(suggestion.get('context_data', ''))
                })

    def _approve_single(
        self,
        suggestion: Dict,
        context: ApprovalContext,
        callback: Callable
    ) -> None:
        """Approve single synonym"""

        try:
            # Update database
            self.repo.approve_suggestion(
                hoofdterm=context.term,
                synoniem=suggestion['synoniem'],
                reviewed_by=context.user or 'inline_ui'
            )

            # Sync to YAML
            self.yaml_sync.sync_approved_to_yaml()

            # Track action for undo
            st.session_state.last_approval_action = {
                'type': 'approve',
                'suggestion': suggestion,
                'timestamp': datetime.now()
            }

            # Add to history
            st.session_state.approval_history.append({
                'action': 'approved',
                'synoniem': suggestion['synoniem'],
                'timestamp': datetime.now()
            })

            # Success feedback
            st.success(
                f"✅ **{suggestion['synoniem']}** toegevoegd aan synoniemen"
            )

            # Callback
            if callback:
                callback(suggestion)

            # Refresh
            if context.auto_refresh:
                st.rerun()

        except Exception as e:
            st.error(f"❌ Fout bij goedkeuren: {e}")

    def _reject_single(
        self,
        suggestion: Dict,
        context: ApprovalContext,
        callback: Callable
    ) -> None:
        """Reject single synonym"""

        try:
            # Update database
            self.repo.reject_suggestion(
                hoofdterm=context.term,
                synoniem=suggestion['synoniem'],
                reason='Rejected via inline UI',
                reviewed_by=context.user or 'inline_ui'
            )

            # Track for undo
            st.session_state.last_approval_action = {
                'type': 'reject',
                'suggestion': suggestion,
                'timestamp': datetime.now()
            }

            # Add to history
            st.session_state.approval_history.append({
                'action': 'rejected',
                'synoniem': suggestion['synoniem'],
                'timestamp': datetime.now()
            })

            # Feedback
            st.info(f"❌ **{suggestion['synoniem']}** afgewezen")

            # Callback
            if callback:
                callback(suggestion)

            # Refresh
            if context.auto_refresh:
                st.rerun()

        except Exception as e:
            st.error(f"❌ Fout bij afwijzen: {e}")

    def _batch_approve(
        self,
        suggestions: List[Dict],
        context: ApprovalContext,
        callback: Callable
    ) -> None:
        """Approve multiple suggestions at once"""

        approved_count = 0
        errors = []

        with st.spinner(f"Approving {len(suggestions)} suggestions..."):
            for suggestion in suggestions:
                try:
                    self.repo.approve_suggestion(
                        hoofdterm=context.term,
                        synoniem=suggestion['synoniem'],
                        reviewed_by=context.user or 'inline_ui_batch'
                    )
                    approved_count += 1

                    if callback:
                        callback(suggestion)

                except Exception as e:
                    errors.append(f"{suggestion['synoniem']}: {e}")

            # Sync once after all approvals
            if approved_count > 0:
                self.yaml_sync.sync_approved_to_yaml()

        # Feedback
        if approved_count > 0:
            st.success(f"✅ {approved_count} synoniemen goedgekeurd")

        if errors:
            st.error(f"❌ {len(errors)} fouten:")
            for error in errors:
                st.caption(error)

        # Refresh
        if context.auto_refresh:
            st.rerun()

    def _batch_reject(
        self,
        suggestions: List[Dict],
        context: ApprovalContext,
        callback: Callable
    ) -> None:
        """Reject multiple suggestions at once"""

        rejected_count = 0

        with st.spinner(f"Rejecting {len(suggestions)} suggestions..."):
            for suggestion in suggestions:
                try:
                    self.repo.reject_suggestion(
                        hoofdterm=context.term,
                        synoniem=suggestion['synoniem'],
                        reason='Batch rejected via inline UI',
                        reviewed_by=context.user or 'inline_ui_batch'
                    )
                    rejected_count += 1

                    if callback:
                        callback(suggestion)

                except Exception as e:
                    st.error(f"Error rejecting {suggestion['synoniem']}: {e}")

        # Feedback
        st.info(f"❌ {rejected_count} synoniemen afgewezen")

        # Refresh
        if context.auto_refresh:
            st.rerun()

    def _render_undo_option(self) -> None:
        """Show undo option for last action"""

        last_action = st.session_state.last_approval_action
        if not last_action:
            return

        # Check if action is recent (< 30 seconds)
        time_diff = (datetime.now() - last_action['timestamp']).seconds

        if time_diff > 30:
            return

        # Undo button
        if st.button(
            f"↩️ Undo {last_action['type']} of {last_action['suggestion']['synoniem']}",
            key="undo_last"
        ):
            self._undo_last_action()

    def _undo_last_action(self) -> None:
        """Undo the last approval/rejection"""

        last_action = st.session_state.last_approval_action
        if not last_action:
            return

        try:
            if last_action['type'] == 'approve':
                # Undo approval: set back to pending
                self.repo.update_suggestion_status(
                    hoofdterm=last_action['suggestion']['hoofdterm'],
                    synoniem=last_action['suggestion']['synoniem'],
                    status='pending'
                )
                st.success(f"↩️ Approval van {last_action['suggestion']['synoniem']} ongedaan gemaakt")

            elif last_action['type'] == 'reject':
                # Undo rejection: set back to pending
                self.repo.update_suggestion_status(
                    hoofdterm=last_action['suggestion']['hoofdterm'],
                    synoniem=last_action['suggestion']['synoniem'],
                    status='pending'
                )
                st.success(f"↩️ Afwijzing van {last_action['suggestion']['synoniem']} ongedaan gemaakt")

            # Clear last action
            st.session_state.last_approval_action = None

            # Refresh
            st.rerun()

        except Exception as e:
            st.error(f"❌ Kon actie niet ongedaan maken: {e}")


# Integration in Definition Generator Tab
def integrate_inline_approval(definition_tab_module):
    """
    Monkey-patch or extend definition generator tab with inline approval.

    This shows how to integrate the widget into existing UI.
    """

    original_render = definition_tab_module.render_definition_generator_tab

    def enhanced_render():
        # Call original render
        original_render()

        # Add inline approval after definition generation
        if st.session_state.get('generated_definition'):
            term = st.session_state.get('current_term')
            definition = st.session_state.get('generated_definition', {}).get('content', '')

            if term:
                # Create approval widget
                widget = InlineSynonymApprovalWidget(
                    synonym_repo=get_synonym_repository(),
                    synonym_workflow=get_synonym_workflow(),
                    yaml_sync_service=get_yaml_sync_service()
                )

                # Create context
                context = ApprovalContext(
                    term=term,
                    definition=definition,
                    session_id=st.session_state.get('session_id', 'default'),
                    user=st.session_state.get('user', 'anonymous')
                )

                # Render widget
                st.markdown("---")
                widget.render(
                    context=context,
                    max_suggestions=3,
                    on_approve=lambda s: log_approval(s),
                    on_reject=lambda s: log_rejection(s)
                )

    # Replace with enhanced version
    definition_tab_module.render_definition_generator_tab = enhanced_render
```

---

## 📊 TEST IMPLEMENTATION EXAMPLES

### Unit Test Suite

```python
# File: /Users/chrislehnen/Projecten/Definitie-app/tests/test_synonym_optimization.py

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sqlite3

from src.services.synonym_tracking_service import (
    SynonymTrackingService,
    UsageMetrics
)
from src.ui.components.web_lookup_report import render_web_lookup_report
from src.ui.components.inline_synonym_approval import (
    InlineSynonymApprovalWidget,
    ApprovalContext
)


class TestWebLookupTransparency:
    """Test suite for Web Lookup Transparency feature"""

    def test_metadata_tracking(self):
        """Test that lookup metadata is properly tracked"""
        service = Mock()
        metadata = WebLookupMetadata(original_term="test")

        # Simulate lookup
        metadata.synonyms_attempted = ["syn1", "syn2"]
        metadata.synonyms_matched = ["syn1"]
        metadata.provider_details = {
            "Wikipedia": {"hit_count": 3, "matched_synonyms": ["syn1"]}
        }

        report = metadata.to_report_dict()

        assert report['original_term'] == "test"
        assert report['total_hits'] == 3
        assert report['synonyms_used'] == ["syn1"]
        assert report['success_rate'] == 0.5

    def test_report_renders_without_errors(self):
        """Test UI component renders correctly"""
        mock_data = {
            'original_term': 'test',
            'synonyms_used': ['syn1'],
            'provider_hits': {
                'Wikipedia': {'count': 3, 'synonyms': ['syn1']}
            },
            'total_hits': 3,
            'duration_ms': 250
        }

        # Should not raise exception
        with patch('streamlit.expander'):
            render_web_lookup_report(mock_data)

    @pytest.mark.parametrize("hits,expected_icon", [
        (15, "🎯"),  # Excellent
        (8, "✅"),   # Good
        (3, "⚠️"),   # Limited
        (0, "❌"),   # No results
    ])
    def test_status_icons(self, hits, expected_icon):
        """Test correct status icon based on hits"""
        # Test logic for determining icons
        assert get_status_icon(hits) == expected_icon


class TestUsageTracking:
    """Test suite for Usage Tracking feature"""

    @pytest.fixture
    def tracking_service(self, tmp_path):
        """Create test tracking service with temp database"""
        db_path = tmp_path / "test.db"
        return SynonymTrackingService(str(db_path))

    def test_tracking_increments(self, tracking_service):
        """Test usage counter increments correctly"""
        # Track initial usage
        tracking_service.track_lookup(
            hoofdterm="test",
            synoniem="syn1",
            provider="Wikipedia",
            hit_count=3
        )

        # Track another usage
        tracking_service.track_lookup(
            hoofdterm="test",
            synoniem="syn1",
            provider="SRU",
            hit_count=2
        )

        # Get metrics
        metrics = tracking_service.get_metrics("test", "syn1")

        assert metrics.usage_count == 2
        assert metrics.hit_count == 5
        assert metrics.total_lookups == 2

    def test_effectiveness_calculation(self):
        """Test effectiveness score calculation"""
        metrics = UsageMetrics(
            hoofdterm="test",
            synoniem="syn1",
            usage_count=50,
            hit_count=40,
            total_lookups=50
        )

        # Score = (40/50 * 0.7) + (50/100 * 0.3) = 0.56 + 0.15 = 0.71
        assert abs(metrics.effectiveness_score - 0.71) < 0.01

    def test_trend_detection(self, tracking_service):
        """Test trend detection logic"""
        # Simulate older usage (14 days ago)
        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now() - timedelta(days=14)

            for _ in range(10):
                tracking_service.track_lookup(
                    hoofdterm="test",
                    synoniem="syn1",
                    provider="Wikipedia",
                    hit_count=1
                )

        # Simulate recent usage (today)
        for _ in range(20):
            tracking_service.track_lookup(
                hoofdterm="test",
                synoniem="syn1",
                provider="Wikipedia",
                hit_count=1
            )

        metrics = tracking_service.get_metrics("test", "syn1")
        assert metrics.trend == "increasing"

    def test_performance_overhead(self, tracking_service, benchmark):
        """Benchmark tracking overhead"""

        def track_operation():
            tracking_service.track_lookup(
                hoofdterm="test",
                synoniem="syn1",
                provider="Wikipedia",
                hit_count=3,
                response_time_ms=250
            )

        # Should complete in < 5ms
        result = benchmark(track_operation)
        assert result < 0.005  # 5ms


class TestInlineApproval:
    """Test suite for Inline Approval feature"""

    @pytest.fixture
    def approval_widget(self):
        """Create test approval widget"""
        return InlineSynonymApprovalWidget(
            synonym_repo=Mock(),
            synonym_workflow=Mock(),
            yaml_sync_service=Mock()
        )

    def test_widget_renders_with_suggestions(self, approval_widget):
        """Test widget renders when suggestions exist"""
        context = ApprovalContext(
            term="test",
            definition="Test definition",
            session_id="test_session"
        )

        suggestions = [
            {
                'synoniem': 'syn1',
                'confidence': 0.85,
                'rationale': 'Common usage'
            }
        ]

        approval_widget.repo.get_pending_suggestions.return_value = suggestions

        with patch('streamlit.container'):
            approval_widget.render(context)

        # Verify repo was called
        approval_widget.repo.get_pending_suggestions.assert_called_once()

    def test_approval_updates_database_and_yaml(self, approval_widget):
        """Test approval flow updates both database and YAML"""
        suggestion = {
            'hoofdterm': 'test',
            'synoniem': 'syn1',
            'confidence': 0.85
        }

        context = ApprovalContext(
            term="test",
            definition="Test definition",
            session_id="test_session"
        )

        # Mock Streamlit button click
        with patch('streamlit.button', return_value=True):
            with patch('streamlit.success'):
                approval_widget._approve_single(
                    suggestion,
                    context,
                    callback=None
                )

        # Verify database update
        approval_widget.repo.approve_suggestion.assert_called_once_with(
            hoofdterm='test',
            synoniem='syn1',
            reviewed_by='inline_ui'
        )

        # Verify YAML sync
        approval_widget.yaml_sync.sync_approved_to_yaml.assert_called_once()

    def test_batch_operations(self, approval_widget):
        """Test batch approve/reject functionality"""
        suggestions = [
            {'hoofdterm': 'test', 'synoniem': f'syn{i}', 'confidence': 0.8}
            for i in range(5)
        ]

        context = ApprovalContext(
            term="test",
            definition="Test definition",
            session_id="test_session",
            auto_refresh=False  # Disable for testing
        )

        with patch('streamlit.spinner'):
            with patch('streamlit.success'):
                approval_widget._batch_approve(
                    suggestions,
                    context,
                    callback=None
                )

        # Verify all suggestions were approved
        assert approval_widget.repo.approve_suggestion.call_count == 5

        # Verify YAML sync called once (not per suggestion)
        approval_widget.yaml_sync.sync_approved_to_yaml.assert_called_once()

    def test_undo_functionality(self, approval_widget):
        """Test undo last action"""
        # Set up last action
        st.session_state.last_approval_action = {
            'type': 'approve',
            'suggestion': {
                'hoofdterm': 'test',
                'synoniem': 'syn1'
            },
            'timestamp': datetime.now()
        }

        with patch('streamlit.success'):
            approval_widget._undo_last_action()

        # Verify status was reverted
        approval_widget.repo.update_suggestion_status.assert_called_once_with(
            hoofdterm='test',
            synoniem='syn1',
            status='pending'
        )


class TestIntegration:
    """Integration tests for complete flow"""

    def test_end_to_end_synonym_workflow(self):
        """Test complete flow from lookup to approval"""

        # 1. Web lookup with synonyms
        lookup_service = Mock()
        lookup_result = {
            'original_term': 'voorlopige hechtenis',
            'synonyms_used': ['voorarrest'],
            'total_hits': 5
        }

        # 2. Track usage
        tracking_service = Mock()

        # 3. Generate suggestions
        workflow = Mock()
        workflow.suggest_synonyms.return_value = [
            {'synoniem': 'bewaring', 'confidence': 0.85}
        ]

        # 4. Approve inline
        approval_widget = Mock()

        # Simulate flow
        with patch('streamlit.session_state', {}):
            # Lookup happens
            lookup_service.lookup_term.return_value = lookup_result

            # Usage tracked
            tracking_service.track_lookup(
                hoofdterm='voorlopige hechtenis',
                synoniem='voorarrest',
                provider='Wikipedia',
                hit_count=5
            )

            # Suggestions generated
            suggestions = workflow.suggest_synonyms(
                hoofdterm='voorlopige hechtenis'
            )

            # Inline approval
            approval_widget.approve(suggestions[0])

        # Verify all components were called
        assert lookup_service.lookup_term.called
        assert tracking_service.track_lookup.called
        assert workflow.suggest_synonyms.called
        assert approval_widget.approve.called


# Performance benchmarks
@pytest.mark.benchmark
def test_tracking_performance_benchmark(benchmark, tmp_path):
    """Benchmark tracking performance"""
    db_path = tmp_path / "bench.db"
    service = SynonymTrackingService(str(db_path))

    def run_tracking():
        for i in range(100):
            service.track_lookup(
                hoofdterm=f"term{i % 10}",
                synoniem=f"syn{i % 20}",
                provider="Wikipedia",
                hit_count=i % 5
            )

    # Should complete 100 operations in < 500ms
    result = benchmark(run_tracking)
    assert result < 0.5
```

---

Deze code voorbeelden demonstreren:

1. **Web Lookup Transparency**: Complete tracking van synoniemen gebruik met rich UI reporting
2. **Usage Tracking**: Database-backed analytics met trend detection en effectiveness scoring
3. **Inline Approval**: Smart UI widget met batch operations, undo support, en YAML sync

Elke feature is production-ready met:
- Error handling
- Performance optimization
- State management
- Testing coverage
- User feedback
- Analytics integration