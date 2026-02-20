import streamlit as st
import requests
from typing import Dict

st.set_page_config(page_title="OptimQL", page_icon="⚡", layout="wide")

# --- Minimal CSS to approximate the React/Tailwind dark UI ---
st.markdown(
    """
    <style>
    .page-background { background-color: #000; color: #e5e7eb; }
    .editor-card { background: #000; border: 1px solid #2b2b2b; padding: 12px; }
    .line-count { color: #9ca3af; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, 'Roboto Mono', 'Segoe UI Mono', monospace; font-size:12px }
    .metric { border:1px solid #2b2b2b; padding:18px; background: rgba(15,15,15,0.6); }
    .metric-title { color:#9ca3af; font-size:12px; text-transform:uppercase; }
    .metric-value { color:#e5e7eb; font-size:24px; }
    .suggestion { border:1px solid #2b2b2b; padding:12px; background: rgba(11,11,11,0.6); }
    pre.sql { background:#000; border:1px solid #2b2b2b; padding:12px; color:#e5e7eb; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Optimize your SQL queries")
st.caption("Analyze and improve database query performance with Python-powered optimization")

# Top-level layout: editor on left, results on right
editor_col, results_col = st.columns([2, 1])

with editor_col:
    st.subheader("Input Query")
    # Editor area
    query = st.text_area("", height=300, placeholder="SELECT * FROM users WHERE ...", key="query_input")

    # Small status row
    line_count = len(query.splitlines()) if query else 0
    char_count = len(query)
    cols = st.columns([1, 1, 6])
    with cols[0]:
        if st.button("Optimize", key="optimize_btn"):
            st.session_state["_opt_now"] = True
    with cols[1]:
        if st.button("Load example"):
            st.session_state["query_input"] = "SELECT * FROM users u\nJOIN orders o ON u.id = o.user_id\nWHERE u.created_at > '2024-01-01' AND o.status = 'completed'"
    with cols[2]:
        if query:
            st.markdown(f"<div class='line-count'>{line_count} lines · {char_count} chars</div>", unsafe_allow_html=True)

with results_col:
    st.subheader("Performance Metrics")
    # default metrics placeholder
    metrics_container = st.container()
    suggestions_container = st.container()

# Handle optimization action
opt_now = st.session_state.get("_opt_now", False)
if opt_now:
    if not query or not query.strip():
        st.warning("Please enter a SQL query.")
    else:
        with st.spinner("Agents are analyzing your query..."):
            try:
                payload_query = query.strip()
                if payload_query.endswith(";"):
                    payload_query = payload_query[:-1].strip()

                response = requests.post("http://localhost:8000/analyze", json={"query": payload_query}, timeout=20)
                if response.status_code == 200:
                    result: Dict = response.json()
                    st.success("Analysis Complete!")

                    # Render metrics
                    with metrics_container:
                        mcols = st.columns(4)
                        mcols[0].markdown("<div class='metric'><div class='metric-title'>Time</div><div class='metric-value'>{}</div></div>".format(result.get("baseline_time_ms", "N/A")), unsafe_allow_html=True)
                        mcols[1].markdown("<div class='metric'><div class='metric-title'>Rows</div><div class='metric-value'>{}</div></div>".format(result.get("rows_scanned", "N/A")), unsafe_allow_html=True)
                        mcols[2].markdown("<div class='metric'><div class='metric-title'>Faster</div><div class='metric-value'>{}%</div></div>".format(result.get("improvement_percentage", 0)), unsafe_allow_html=True)
                        mcols[3].markdown("<div class='metric'><div class='metric-title'>Confidence</div><div class='metric-value'>{}</div></div>".format(round(result.get("confidence_score", 0) * 100, 1)), unsafe_allow_html=True)

                    # Render suggestion and details
                    with suggestions_container:
                        st.subheader("Suggested Optimization")
                        suggested = result.get("suggested_query", "") or ""
                        st.markdown(f"<pre class='sql'>{suggested}</pre>", unsafe_allow_html=True)

                        # Helpful production note for pg_trgm / CONCURRENTLY
                        note_lines = []
                        if 'gin_trgm_ops' in suggested.lower() or 'pg_trgm' in suggested.lower():
                            note_lines.append("This suggestion requires the pg_trgm extension for trigram indexes.")
                            note_lines.append("Recommended production DDL:")
                            note_lines.append("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                            note_lines.append(suggested)
                        if 'concurrently' in suggested.lower():
                            if not note_lines:
                                note_lines.append("This suggestion uses CONCURRENTLY to avoid write locks.")
                            note_lines.append("Run the CREATE INDEX CONCURRENTLY statement in a maintenance window or with sufficient privileges.")

                        if note_lines:
                            st.info('\n'.join(note_lines))

                        st.markdown("### Details")
                        st.text(result.get("details", ""))
                else:
                    st.error(f"Error from backend: {response.status_code} {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")
            finally:
                st.session_state["_opt_now"] = False

st.markdown("---")
st.caption("Powered by PostgreSQL & FastAPI")
