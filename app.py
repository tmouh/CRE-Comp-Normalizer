"""
CRE Comp Intake Normalizer
Streamlit entry point — UI layout and session orchestration.
"""

import pandas as pd
import pyperclip
import streamlit as st

import config
import extractor
import normalizer
import exporter
from schema import FIELD_NAMES, CURRENCY_FIELDS, PERCENT_FIELDS

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Comp Intake Normalizer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state initialization ─────────────────────────────────────────────
if "comp_df" not in st.session_state:
    st.session_state["comp_df"] = pd.DataFrame(columns=FIELD_NAMES)
if "log" not in st.session_state:
    st.session_state["log"] = []          # list of (icon, message) tuples
if "total_input_tokens" not in st.session_state:
    st.session_state["total_input_tokens"] = 0
if "total_output_tokens" not in st.session_state:
    st.session_state["total_output_tokens"] = 0

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")

    api_key_input = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Enter your key here, or set ANTHROPIC_API_KEY in .env",
    )
    api_key = config.get_api_key(api_key_input)

    if api_key:
        st.success("API key loaded", icon="✅")
    else:
        st.warning("No API key set", icon="⚠️")
        st.markdown(
            "Get a key at [console.anthropic.com](https://console.anthropic.com)"
        )

    st.divider()
    st.caption(f"Model: `{config.MODEL}`")

    total_cost = config.estimate_cost(
        st.session_state["total_input_tokens"],
        st.session_state["total_output_tokens"],
    )
    st.metric(
        "Session Cost (est.)",
        f"${total_cost:.4f}",
        help=f"In: {st.session_state['total_input_tokens']:,} tokens | Out: {st.session_state['total_output_tokens']:,} tokens",
    )

    st.divider()
    if st.button("🗑️ Reset Session", use_container_width=True):
        st.session_state["comp_df"] = pd.DataFrame(columns=FIELD_NAMES)
        st.session_state["log"] = []
        st.session_state["total_input_tokens"] = 0
        st.session_state["total_output_tokens"] = 0
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏢 CRE Comp Intake Normalizer")
st.caption("Upload broker OMs (PDF) or paste email blasts → extract → review → export.")

st.divider()

# ── Input section ─────────────────────────────────────────────────────────────
tab_pdf, tab_text = st.tabs(["📄 Upload PDFs", "📋 Paste Text"])

pdf_queue = []   # list of (filename, bytes)
text_queue = []  # list of (source_label, text)

with tab_pdf:
    uploaded_files = st.file_uploader(
        "Drop PDF files here",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files:
        for f in uploaded_files:
            size_mb = len(f.getvalue()) / (1024 * 1024)
            if size_mb > config.PDF_SIZE_WARN_MB:
                st.warning(f"⚠️ {f.name} is {size_mb:.1f} MB — large files use more tokens.")
            pdf_queue.append((f.name, f.getvalue()))
        st.info(f"{len(pdf_queue)} PDF(s) ready to extract.")

with tab_text:
    col1, col2 = st.columns([3, 1])
    with col1:
        pasted_text = st.text_area(
            "Paste broker email or blast text here",
            height=200,
            placeholder="39 Clifton Place | Clinton Hill, Brooklyn | 5 Units | Mixed-Use\nAsking: $5,000,000 | Cap Rate: 5.7% | NOI: $286,388\n...",
        )
    with col2:
        source_label = st.text_input(
            "Source label",
            value="pasted_text",
            help="A name for this input (used as source_file in the output)",
        )
    if pasted_text and pasted_text.strip():
        text_queue.append((source_label or "pasted_text", pasted_text.strip()))
        st.info("Text ready to extract.")

# ── Extract button ─────────────────────────────────────────────────────────────
total_queue = len(pdf_queue) + len(text_queue)
col_btn, col_est = st.columns([1, 3])
with col_btn:
    extract_clicked = st.button(
        "⚡ Extract All",
        disabled=(total_queue == 0 or not api_key),
        type="primary",
        use_container_width=True,
    )
with col_est:
    if total_queue > 0:
        est_cost = total_queue * 0.06  # rough estimate per document
        st.caption(f"~{total_queue} document(s) queued — estimated cost: ${est_cost:.2f}")
    if not api_key and total_queue > 0:
        st.error("Add your API key in the sidebar to extract.")

# ── Extraction logic ──────────────────────────────────────────────────────────
if extract_clicked and total_queue > 0 and api_key:
    progress_bar = st.progress(0, text="Starting extraction...")
    total = total_queue
    done = 0

    for filename, pdf_bytes in pdf_queue:
        progress_bar.progress(done / total, text=f"Extracting {filename}…")
        try:
            raw, inp_tok, out_tok = extractor.extract_from_pdf(pdf_bytes, filename, api_key)
            row = normalizer.normalize(raw, filename)
            new_row = pd.DataFrame([row])
            st.session_state["comp_df"] = pd.concat(
                [st.session_state["comp_df"], new_row], ignore_index=True
            )
            st.session_state["total_input_tokens"] += inp_tok
            st.session_state["total_output_tokens"] += out_tok
            conf = row.get("confidence_score", "?")
            filled = sum(1 for v in row.values() if v is not None)
            st.session_state["log"].append(
                ("✅", f"**{filename}** — {conf} confidence ({filled}/{len(FIELD_NAMES)} fields)")
            )
        except Exception as e:
            st.session_state["log"].append(("❌", f"**{filename}** — Error: {e}"))
        done += 1

    for source_label, text in text_queue:
        progress_bar.progress(done / total, text="Extracting " + source_label + "...")
        try:
            raw, inp_tok, out_tok = extractor.extract_from_text(text, source_label, api_key)
            row = normalizer.normalize(raw, source_label)
            new_row = pd.DataFrame([row])
            st.session_state["comp_df"] = pd.concat(
                [st.session_state["comp_df"], new_row], ignore_index=True
            )
            st.session_state["total_input_tokens"] += inp_tok
            st.session_state["total_output_tokens"] += out_tok
            conf = row.get("confidence_score", "?")
            filled = sum(1 for v in row.values() if v is not None)
            st.session_state["log"].append(
                ("✅", f"**{source_label}** — {conf} confidence ({filled}/{len(FIELD_NAMES)} fields)")
            )
        except Exception as e:
            st.session_state["log"].append(("❌", f"**{source_label}** — Error: {e}"))
        done += 1

    progress_bar.progress(1.0, text="Done!")
    st.rerun()

# ── Processing log ─────────────────────────────────────────────────────────────
if st.session_state["log"]:
    st.subheader("Processing Log")
    for icon, msg in reversed(st.session_state["log"]):
        st.markdown(f"{icon} {msg}")
    st.divider()

# ── Review table ──────────────────────────────────────────────────────────────
df = st.session_state["comp_df"]

if not df.empty:
    st.subheader(f"Review Table — {len(df)} row(s)")

    # Confidence filter
    conf_filter = st.radio(
        "Show:",
        ["All", "High", "Medium", "Low", "Failed"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if conf_filter != "All":
        display_df = df[df["confidence_score"] == conf_filter].copy()
    else:
        display_df = df.copy()

    if display_df.empty:
        st.info(f"No rows with confidence = {conf_filter}.")
    else:
        # Highlight null cells yellow
        def highlight_nulls(df_in):
            return df_in.map(
                lambda v: "background-color: #FFF9C4" if v is None or (isinstance(v, float) and pd.isna(v)) else ""
            )

        styled = display_df.style.apply(highlight_nulls, axis=None)

        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic",
            key="review_editor",
        )

        # Sync edits back to session state
        if conf_filter == "All":
            st.session_state["comp_df"] = edited_df
        else:
            # Merge edited rows back into the full df
            st.session_state["comp_df"].update(edited_df)

    st.divider()

    # ── Export section ─────────────────────────────────────────────────────────
    st.subheader("Export")
    col_csv, col_xl, col_clip = st.columns(3)

    with col_csv:
        csv_bytes = exporter.to_csv(df)
        st.download_button(
            "⬇️ Download CSV",
            data=csv_bytes,
            file_name="comps.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_xl:
        xl_bytes = exporter.to_excel(df)
        st.download_button(
            "⬇️ Download Excel",
            data=xl_bytes,
            file_name="comps.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_clip:
        if st.button("📋 Copy to Clipboard", use_container_width=True):
            tsv = exporter.to_clipboard_tsv(df)
            try:
                pyperclip.copy(tsv)
                st.success("Copied! Paste into Excel with Ctrl+V.")
            except Exception:
                st.warning("Clipboard not available in this environment. Use Download instead.")

else:
    st.info("Upload PDFs or paste text above, then click **Extract All** to begin.")
