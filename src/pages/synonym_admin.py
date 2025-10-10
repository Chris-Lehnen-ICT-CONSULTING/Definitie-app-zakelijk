"""
Synonym Admin & Review - Standalone Page (v3.1)

Streamlit multipage app standalone page voor comprehensive synonym management.

Architecture v3.1: Uses SynonymRegistry + SynonymOrchestrator

Features:
- Statistics dashboard (AI-pending, active, rejected counts)
- Advanced filtering (status, term search, confidence threshold)
- Pagination voor large datasets
- Individual review cards met approve/reject/revert
- Bulk operations (approve all, reject all visible)
- GPT-4 synonym generation via SynonymOrchestrator
- Cache metrics monitoring

This page replaces legacy src/pages/synonym_review.py (which used old YAML workflow).
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st

from src.repositories.synonym_registry import SynonymRegistry
from src.services.container import get_container
from src.services.gpt4_synonym_suggester import GPT4SynonymSuggester
from src.services.synonym_orchestrator import SynonymOrchestrator

logger = logging.getLogger(__name__)

# ========================================
# PAGE CONFIG
# ========================================

st.set_page_config(
    page_title="Synonym Admin - DefinitieAgent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========================================
# HEADER
# ========================================

st.markdown(
    """
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>🔍 Synonym Admin & Review (v3.1)</h1>
        <p style="font-size: 16px; color: #666;">
            Comprehensive admin tool voor het beheren van AI-gegenereerde synoniemen
        </p>
    </div>
""",
    unsafe_allow_html=True,
)

# Info banner
st.info(
    """
    **💡 Architecture v3.1 Workflow:**
    1. GPT-4 genereert synonym suggesties via `SynonymOrchestrator.ensure_synonyms()`
    2. Suggesties worden opgeslagen als **ai_pending** members in `synonym_groups` tables
    3. Review suggesties in deze interface
    4. **Approve** → status `active` (gebruikt in web lookups)
    5. **Reject** → status `rejected_auto` (niet gebruikt)

    **📊 Data Source:** SynonymRegistry (v3.1) - `synonym_groups` + `synonym_members` tables
    **🔄 Cache:** TTL cache met invalidatie via SynonymOrchestrator
"""
)

st.markdown("---")

# ========================================
# INITIALIZE SERVICES
# ========================================


@st.cache_resource
def get_services():
    """Initialize v3.1 services (cached per session)."""
    container = get_container()
    return {
        "registry": container.synonym_registry(),
        "orchestrator": container.synonym_orchestrator(),
        "gpt4_suggester": container.gpt4_synonym_suggester(),
    }


services = get_services()
registry: SynonymRegistry = services["registry"]
orchestrator: SynonymOrchestrator = services["orchestrator"]
gpt4_suggester: GPT4SynonymSuggester = services["gpt4_suggester"]

# ========================================
# STATISTICS PANEL
# ========================================

st.markdown("## 📊 Statistics Dashboard")

try:
    stats = registry.get_statistics()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        total_groups = stats.get("total_groups", 0)
        st.metric("📊 Totaal Groepen", total_groups)

    with col2:
        ai_pending = stats.get("members_by_status", {}).get("ai_pending", 0)
        st.metric("⏳ AI Pending", ai_pending)

    with col3:
        active = stats.get("members_by_status", {}).get("active", 0)
        st.metric("✅ Active", active)

    with col4:
        rejected = stats.get("members_by_status", {}).get("rejected_auto", 0)
        st.metric("❌ Rejected", rejected)

    with col5:
        total_members = stats.get("total_members", 0)
        st.metric("📈 Totaal Members", total_members)

    # Cache statistics
    cache_stats = orchestrator.get_cache_stats()

    col1, col2, col3 = st.columns(3)
    with col1:
        hit_rate = cache_stats.get("hit_rate", 0.0)
        st.caption(f"💾 Cache Hit Rate: {hit_rate:.1%}")
    with col2:
        cache_size = cache_stats.get("size", 0)
        st.caption(f"📦 Cache Size: {cache_size} entries")
    with col3:
        total_reviewed = active + rejected
        if total_reviewed > 0:
            approval_rate = active / total_reviewed
            st.caption(f"📊 Approval Rate: {approval_rate:.1%}")

except Exception as e:
    st.error(f"❌ Kon statistieken niet laden: {e}")
    logger.error(f"Statistics error: {e}", exc_info=True)

st.markdown("---")

# ========================================
# GPT-4 GENERATION SECTION
# ========================================

st.markdown("## 🚀 Genereer Nieuwe Synoniemen (GPT-4)")
st.markdown("**Genereer AI-gestuurde synonym suggesties via SynonymOrchestrator**")

col1, col2 = st.columns([3, 1])

with col1:
    term = st.text_input(
        "Juridische term",
        placeholder="bijv. verdachte, getuige, rechter...",
        help="Voer een juridische term in waarvoor synoniemen gegenereerd moeten worden",
        key="generate_term",
    )

with col2:
    min_count = st.number_input(
        "Min. Synoniemen",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        help="Minimum aantal synoniemen te genereren",
        key="min_count",
    )

if st.button("🤖 Genereer Suggesties", type="primary", use_container_width=True):
    if not term or not term.strip():
        st.error("❌ Voer eerst een term in")
    else:
        with st.spinner(f"🔄 GPT-4 genereert synoniemen voor '{term}'..."):
            try:
                # Use orchestrator's ensure_synonyms (async)
                synonyms, ai_pending_count = asyncio.run(
                    orchestrator.ensure_synonyms(
                        term=term.strip(), min_count=min_count, context=None
                    )
                )

                if ai_pending_count > 0:
                    st.success(
                        f"✅ {ai_pending_count} nieuwe AI-suggesties gegenereerd en opgeslagen als 'ai_pending'!"
                    )

                    # Show preview
                    st.markdown("**Preview (ai_pending):**")
                    for syn in synonyms[:5]:
                        confidence_pct = syn.weight * 100
                        st.write(
                            f"- **{syn.term}** (confidence: {confidence_pct:.0f}%)"
                        )

                    if len(synonyms) > 5:
                        st.caption(f"... en {len(synonyms) - 5} meer")

                    st.info(
                        "💡 Scroll naar beneden om de suggesties te reviewen en goed te keuren"
                    )

                    st.rerun()
                else:
                    st.info(
                        f"Term '{term}' heeft al voldoende synoniemen ({len(synonyms)} found)"
                    )

            except Exception as e:
                st.error(f"❌ Fout bij genereren: {e}")
                logger.error(f"Generation error: {e}", exc_info=True)

st.markdown("---")

# ========================================
# GROUP VIEW SECTION (NEW!)
# ========================================

st.markdown("## 🗂️ Synonym Groepen & Relaties")
st.markdown("**Browse groepen en bekijk alle synoniemen per groep**")

# View mode selector
view_mode = st.radio(
    "Weergave",
    ["Groepen Browser", "Individuele Members Review"],
    horizontal=True,
    key="view_mode",
    help="Groepen Browser: bekijk groepen met hun synoniemen | Members Review: individuele synoniemen beheren",
)

if view_mode == "Groepen Browser":
    # GROUP BROWSER VIEW
    st.markdown("---")

    # Search/filter for groups
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        group_search = st.text_input(
            "🔍 Zoek Groep",
            placeholder="bijv. voorarrest, getuige, onherroepelijk...",
            key="group_search",
            help="Zoek op begrip/canonical term",
        )

    with col2:
        min_members = st.number_input(
            "Min. Members",
            min_value=0,
            max_value=50,
            value=0,
            key="min_members",
            help="Filter groepen met minimaal X members",
        )

    with col3:
        sort_by = st.selectbox(
            "Sorteer op",
            ["Aantal synoniemen", "Alfabetisch", "Laatst bijgewerkt"],
            key="sort_by",
        )

    # Fetch all groups with member counts
    try:
        with registry._get_connection() as conn:
            # Build query
            query = """
                SELECT
                    g.id,
                    g.canonical_term,
                    g.domain,
                    g.created_at,
                    g.updated_at,
                    COUNT(m.id) as member_count,
                    SUM(CASE WHEN m.status = 'active' THEN 1 ELSE 0 END) as active_count,
                    SUM(CASE WHEN m.status = 'ai_pending' THEN 1 ELSE 0 END) as pending_count
                FROM synonym_groups g
                LEFT JOIN synonym_group_members m ON m.group_id = g.id
                WHERE 1=1
            """
            params = []

            # Apply search filter
            if group_search and group_search.strip():
                query += " AND g.canonical_term LIKE ?"
                params.append(f"%{group_search.strip()}%")

            query += " GROUP BY g.id"

            # Apply min_members filter
            if min_members > 0:
                query += " HAVING COUNT(m.id) >= ?"
                params.append(min_members)

            # Apply sorting
            if sort_by == "Aantal synoniemen":
                query += " ORDER BY member_count DESC, g.canonical_term"
            elif sort_by == "Alfabetisch":
                query += " ORDER BY g.canonical_term"
            else:  # Laatst bijgewerkt
                query += " ORDER BY g.updated_at DESC"

            cursor = conn.execute(query, params)
            groups = cursor.fetchall()

        if not groups:
            st.info("📭 Geen groepen gevonden met de huidige filters")
        else:
            st.markdown(f"### 📊 Gevonden groepen: {len(groups)}")

            # Display groups in a grid
            for group_row in groups:
                group_id = group_row["id"]
                canonical_term = group_row["canonical_term"]
                member_count = group_row["member_count"]
                active_count = group_row["active_count"]
                pending_count = group_row["pending_count"]
                domain = group_row["domain"]

                # Create expander for each group
                with st.expander(
                    f"🗂️ **{canonical_term}** ({member_count} synoniemen: {active_count} actief, {pending_count} pending)",
                    expanded=False,
                ):
                    # Show domain if present
                    if domain:
                        st.caption(f"Domein: {domain}")

                    # Fetch members for this group
                    members = registry.get_group_members(
                        group_id=group_id,
                        statuses=None,  # All statuses
                        min_weight=0.0,
                        order_by="weight",  # Highest weight first
                    )

                    if members:
                        # Create a nice table view
                        st.markdown("**Synoniemen in deze groep:**")

                        # Group by status for better overview
                        active_members = [m for m in members if m.status == "active"]
                        pending_members = [
                            m for m in members if m.status == "ai_pending"
                        ]
                        other_members = [
                            m
                            for m in members
                            if m.status not in ["active", "ai_pending"]
                        ]

                        # Helper function to render interactive member cards
                        def render_member_card(m, status_emoji):
                            """Render expandable member card with edit/delete options."""
                            confidence_pct = m.weight * 100
                            preferred_flag = " ⭐" if m.is_preferred else ""

                            with st.expander(
                                f"{status_emoji} {m.term}{preferred_flag} (weight: {confidence_pct:.0f}%)",
                                expanded=False,
                            ):
                                col1, col2 = st.columns([2, 1])

                                with col1:
                                    st.markdown("**📋 Properties:**")
                                    st.write(f"• Status: {m.status}")
                                    st.write(f"• Weight: {m.weight:.3f}")
                                    st.write(f"• Preferred: {'✅' if m.is_preferred else '❌'}")
                                    st.write(f"• Source: {m.source}")
                                    st.write(f"• Usage: {m.usage_count}x")
                                    if m.created_at:
                                        st.caption(
                                            f"Created: {m.created_at.strftime('%Y-%m-%d %H:%M')}"
                                        )

                                    if m.context_json:
                                        try:
                                            context = json.loads(m.context_json)
                                            with st.expander("📄 Context", expanded=False):
                                                st.json(context)
                                        except Exception:
                                            pass

                                with col2:
                                    st.markdown("**✏️ Edit:**")

                                    new_weight = st.slider(
                                        "Weight",
                                        min_value=0.0,
                                        max_value=1.0,
                                        value=float(m.weight),
                                        step=0.05,
                                        key=f"edit_weight_{m.id}",
                                    )

                                    new_is_preferred = st.checkbox(
                                        "Preferred",
                                        value=bool(m.is_preferred),
                                        key=f"edit_preferred_{m.id}",
                                    )

                                    new_status = st.selectbox(
                                        "Status",
                                        [
                                            "active",
                                            "ai_pending",
                                            "rejected_auto",
                                            "deprecated",
                                        ],
                                        index=[
                                            "active",
                                            "ai_pending",
                                            "rejected_auto",
                                            "deprecated",
                                        ].index(m.status),
                                        key=f"edit_status_{m.id}",
                                    )

                                st.markdown("---")
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    if st.button(
                                        "💾 Opslaan", key=f"save_{m.id}", type="primary"
                                    ):
                                        try:
                                            registry.update_member(
                                                m.id,
                                                weight=new_weight,
                                                is_preferred=new_is_preferred,
                                                status=new_status,
                                                reviewed_by="admin",
                                            )
                                            orchestrator.invalidate_cache(m.term)
                                            st.success("✅ Opgeslagen!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Fout: {e}")

                                with col2:
                                    if st.button("🔗 Ontkoppel", key=f"unlink_{m.id}"):
                                        if st.session_state.get(
                                            f"confirm_unlink_{m.id}", False
                                        ):
                                            try:
                                                registry.delete_member(m.id)
                                                orchestrator.invalidate_cache(m.term)
                                                st.success("✅ Ontkoppeld!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Fout: {e}")
                                        else:
                                            st.session_state[f"confirm_unlink_{m.id}"] = (
                                                True
                                            )
                                            st.warning("Klik nogmaals")

                                with col3:
                                    if st.button("🗑️ Verwijder", key=f"delete_m_{m.id}"):
                                        if st.session_state.get(
                                            f"confirm_delete_m_{m.id}", False
                                        ):
                                            try:
                                                registry.delete_member(m.id)
                                                orchestrator.invalidate_cache(m.term)
                                                st.success("✅ Verwijderd!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Fout: {e}")
                                        else:
                                            st.session_state[f"confirm_delete_m_{m.id}"] = (
                                                True
                                            )
                                            st.warning("Klik nogmaals")

                        # Render active members
                        if active_members:
                            st.markdown("##### ✅ Actieve Synoniemen")
                            for m in active_members:
                                render_member_card(m, "✅")

                        # Render pending members
                        if pending_members:
                            st.markdown("##### ⏳ AI Pending")
                            for m in pending_members:
                                render_member_card(m, "⏳")

                        # Render other status members
                        if other_members:
                            st.markdown("##### 🔴 Overig")
                            for m in other_members:
                                render_member_card(m, "🔴")
                    else:
                        st.info("Deze groep heeft geen members (leeg)")

                    # Group actions
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(
                            "🗑️ Verwijder Groep", key=f"delete_group_{group_id}"
                        ):
                            if st.session_state.get(
                                f"confirm_delete_{group_id}", False
                            ):
                                try:
                                    registry.delete_group(group_id, cascade=True)
                                    st.success(f"Groep '{canonical_term}' verwijderd!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Fout: {e}")
                            else:
                                st.session_state[f"confirm_delete_{group_id}"] = True
                                st.warning("Klik nogmaals om te bevestigen")

                    with col2:
                        st.caption(f"Group ID: {group_id}")

    except Exception as e:
        st.error(f"❌ Fout bij laden groepen: {e}")
        logger.error(f"Group browser error: {e}", exc_info=True)

    st.markdown("---")

elif view_mode == "Individuele Members Review":
    # ORIGINAL MEMBER-BASED VIEW
    st.markdown("---")

# ========================================
# FILTERS SECTION (for member view)
# ========================================

if view_mode == "Individuele Members Review":
    st.markdown("## 🔎 Filters & Review")

    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

    with col1:
        status_options = ["Alle", "AI Pending", "Active", "Rejected"]
        status_filter = st.radio(
            "Status",
            status_options,
            horizontal=True,
            key="status_filter",
            help="Filter op member status",
        )

    with col2:
        search_term = st.text_input(
            "🔍 Zoek Term",
            placeholder="bijv. verdachte...",
            key="search_term",
            help="Zoek op term (fuzzy match)",
        )

    with col3:
        min_weight = st.slider(
            "Min. Weight",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            key="min_weight",
            help="Minimum weight threshold (0.0-1.0)",
        )

    with col4:
        if st.button("🔄 Refresh", key="refresh", help="Herlaad data"):
            st.rerun()

    # Map UI status naar DB status
    status_db_map = {
        "Alle": None,
        "AI Pending": "ai_pending",
        "Active": "active",
        "Rejected": "rejected_auto",
    }

    filters = {
        "status": status_db_map[status_filter],
        "term_search": search_term.strip() if search_term else None,
        "min_weight": min_weight,
    }

    st.markdown("---")

    # ========================================
    # MEMBERS TABLE
    # ========================================

    try:
        # Fetch members based on filters (ONE query instead of N+1!)
        status_filter_db = filters["status"]
        term_search = filters["term_search"]
        min_weight_filter = filters["min_weight"]

        # Query registry - NEW METHOD fixes Bug #1 (get_all_groups) and Bug #2 (N+1)
        all_members = registry.get_all_members(
            statuses=[status_filter_db] if status_filter_db else None,
            min_weight=min_weight_filter,
            term_search=term_search,  # Server-side filtering
            order_by="weight",  # Bug #4 FIX: string instead of list!
            # No limit - we'll paginate client-side
        )

        if not all_members:
            st.info(
                "📭 Geen members gevonden met de huidige filters. "
                "Probeer de filters aan te passen."
            )
        else:
            st.markdown(f"### 📋 Synonym Members ({len(all_members)})")

            # Pagination
            items_per_page = 20
            total_pages = (len(all_members) - 1) // items_per_page + 1

            current_page = st.session_state.get("page", 1)
            if current_page > total_pages:
                current_page = 1

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page = st.number_input(
                    "Pagina",
                    min_value=1,
                    max_value=total_pages,
                    value=current_page,
                    key="page_input",
                )
                st.session_state["page"] = page

            # Paginate
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_members = all_members[start_idx:end_idx]

            # Bulk actions (only for ai_pending)
            ai_pending_on_page = [m for m in page_members if m.status == "ai_pending"]

            if ai_pending_on_page:
                st.markdown("#### ⚡ Bulk Acties")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        f"✅ Approve All Visible ({len(ai_pending_on_page)})",
                        key="bulk_approve",
                    ):
                        st.session_state["confirm_bulk_approve"] = True

                with col2:
                    if st.button(
                        f"❌ Reject All Visible ({len(ai_pending_on_page)})",
                        key="bulk_reject",
                    ):
                        st.session_state["confirm_bulk_reject"] = True

                # Confirmations
                if st.session_state.get("confirm_bulk_approve", False):
                    st.warning(
                        f"⚠️ Weet je zeker dat je {len(ai_pending_on_page)} members wilt approven?"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Ja, Approve All", key="confirm_yes_approve"):
                            user = st.session_state.get("user", "admin")
                            success = 0
                            for m in ai_pending_on_page:
                                try:
                                    registry.update_member_status(m.id, "active", user)
                                    orchestrator.invalidate_cache(m.term)
                                    success += 1
                                except Exception as e:
                                    logger.error(f"Bulk approve failed for {m.id}: {e}")
                            st.success(f"✅ {success} members approved!")
                            st.session_state["confirm_bulk_approve"] = False
                            st.rerun()
                    with col2:
                        if st.button("Annuleer", key="cancel_approve"):
                            st.session_state["confirm_bulk_approve"] = False
                            st.rerun()

                if st.session_state.get("confirm_bulk_reject", False):
                    st.warning(
                        f"⚠️ Weet je zeker dat je {len(ai_pending_on_page)} members wilt rejecten?"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Ja, Reject All", key="confirm_yes_reject"):
                            user = st.session_state.get("user", "admin")
                            success = 0
                            for m in ai_pending_on_page:
                                try:
                                    registry.update_member_status(
                                        m.id, "rejected_auto", user
                                    )
                                    orchestrator.invalidate_cache(m.term)
                                    success += 1
                                except Exception as e:
                                    logger.error(f"Bulk reject failed for {m.id}: {e}")
                            st.warning(f"❌ {success} members rejected!")
                            st.session_state["confirm_bulk_reject"] = False
                            st.rerun()
                    with col2:
                        if st.button("Annuleer", key="cancel_reject"):
                            st.session_state["confirm_bulk_reject"] = False
                            st.rerun()

            st.markdown("---")

            # Render individual cards
            for member in page_members:
                # Color coding
                if member.status == "ai_pending":
                    status_color = "🟡"
                    status_label = "AI Pending"
                elif member.status == "active":
                    status_color = "🟢"
                    status_label = "Active"
                elif member.status == "rejected_auto":
                    status_color = "🔴"
                    status_label = "Rejected"
                else:
                    status_color = "⚪"
                    status_label = member.status

                confidence_pct = member.weight * 100

                with st.expander(
                    f"{status_color} **{member.term}** (weight: {confidence_pct:.0f}%, status: {status_label})",
                    expanded=False,
                ):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        if member.context_json:
                            try:
                                context = json.loads(member.context_json)
                                rationale = context.get("rationale", "")
                                if rationale:
                                    st.markdown("**💡 Rationale:**")
                                    st.info(rationale)

                                st.markdown("**📋 Full Context:**")
                                st.json(context)
                            except Exception:
                                st.caption("(Context parsing failed)")

                    with col2:
                        st.markdown("**Details:**")
                        st.write(f"Status: {status_label}")
                        st.write(f"Weight: {member.weight:.3f}")
                        st.write(f"Source: {member.source or 'N/A'}")
                        st.write(f"ID: {member.id}")
                        if member.created_at:
                            st.write(
                                f"Created: {member.created_at.strftime('%Y-%m-%d %H:%M')}"
                            )

                    st.markdown("---")

                    # Actions
                    if member.status == "ai_pending":
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(
                                "✅ Approve", key=f"approve_{member.id}", type="primary"
                            ):
                                user = st.session_state.get("user", "admin")
                                registry.update_member_status(member.id, "active", user)
                                orchestrator.invalidate_cache(member.term)
                                st.success(f"✅ Approved: {member.term}")
                                st.rerun()
                        with col2:
                            if st.button("❌ Reject", key=f"reject_{member.id}"):
                                user = st.session_state.get("user", "admin")
                                registry.update_member_status(
                                    member.id, "rejected_auto", user
                                )
                                orchestrator.invalidate_cache(member.term)
                                st.warning(f"❌ Rejected: {member.term}")
                                st.rerun()
                    elif st.button("↩️ Revert to Pending", key=f"revert_{member.id}"):
                        user = st.session_state.get("user", "admin")
                        registry.update_member_status(member.id, "ai_pending", user)
                        orchestrator.invalidate_cache(member.term)
                        st.success(f"↩️ Reverted: {member.term}")
                        st.rerun()

    except Exception as e:
        st.error(f"❌ Fout bij laden members: {e}")
        logger.error(f"Members table error: {e}", exc_info=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 2rem;">
        DefinitieAgent Synonym Admin (v3.1) |
        <a href="/" target="_self">← Terug naar hoofdapplicatie</a>
    </div>
""",
    unsafe_allow_html=True,
)
