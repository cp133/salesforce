import pandas as pd
import streamlit as st
from app.matcher import exact_match, fuzzy_match
from app.utils import load_csv
st.set_page_config(layout="wide")
st.title("Duplicate Detection App")
# Initialize session state
if "reviewed_pairs" not in st.session_state:
    st.session_state.reviewed_pairs = set()
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
if uploaded_file:
    df = load_csv(uploaded_file)
    # Fix mixed types (PyArrow compatibility)
    for col in df.columns:
        if (
            df[col].dtype == "object"
            or df[col].apply(lambda x: isinstance(x, (int, float))).any()
        ):
            df[col] = df[col].astype(str)
    st.write("### Data Preview", df.head())
    all_columns = df.columns.tolist()
    selected_columns = st.multiselect("Select column(s) to match on", all_columns)
    match_strategy = st.radio(
        "Select matching strategy", ["Exact Match", "Fuzzy Match"]
    )
    threshold = None
    if match_strategy == "Fuzzy Match":
        threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.85)
    if st.button("Find Duplicates"):
        if not selected_columns:
            st.warning(":warning: Please select at least one column before finding duplicates.")
        else:
            st.session_state.reviewed_pairs.clear()
            if match_strategy == "Exact Match":
                duplicates = exact_match(df, selected_columns)
                # Generate exact match pairs for UI review
                match_rows = []
                for _, group in duplicates.groupby(selected_columns):
                    if len(group) > 1:
                        for i in range(len(group)):
                            for j in range(i + 1, len(group)):
                                match_rows.append(
                                    {
                                        "Row A Index": group.index[i],
                                        "Row B Index": group.index[j],
                                        "Similarity": 1.0,
                                    }
                                )
                st.session_state.matches = pd.DataFrame(match_rows)
                st.success(f":white_check_mark: Found {len(match_rows)} exact duplicate pairs.")
                st.session_state.is_fuzzy = True  # Enables UI
            else:
                matches = fuzzy_match(df, selected_columns, threshold)
                st.success(f":white_check_mark: Found {len(matches)} fuzzy duplicate pairs.")
                st.session_state.matches = matches
                st.session_state.is_fuzzy = True
    # Show review UI
    if "matches" in st.session_state and st.session_state.is_fuzzy:
        matches = st.session_state.matches
        for idx, row in matches.iterrows():
            st.markdown("---")
            st.text(f"Similarity: {row['Similarity']:.2f}")
            col1, col2 = st.columns(2)
            row_a_idx = int(row["Row A Index"])
            row_b_idx = int(row["Row B Index"])
            col1.write(df.iloc[row_a_idx])
            col2.write(df.iloc[row_b_idx])
            checked = (row_a_idx, row_b_idx) in st.session_state.reviewed_pairs
            if st.checkbox(
                f"Mark as duplicate (Row {row_a_idx}, {row_b_idx})",
                key=f"check_{idx}",
                value=checked,
            ):
                st.session_state.reviewed_pairs.add((row_a_idx, row_b_idx))
            else:
                st.session_state.reviewed_pairs.discard((row_a_idx, row_b_idx))
    # Finalize and download
    if st.button("Finalize and Save Cleaned File"):
        reviewed = st.session_state.reviewed_pairs
        if reviewed:
            dropped = set(b for _, b in reviewed)
            final_df = df.drop(index=dropped)
            log_rows = []
            for kept_idx, removed_idx in reviewed:
                kept_row = df.loc[kept_idx].copy()
                removed_row = df.loc[removed_idx].copy()
                kept_row["Change Type"] = "Kept"
                kept_row["Row Index"] = kept_idx
                kept_row["Action Description"] = (
                    f"Row retained from duplicate pair ({kept_idx}, {removed_idx})"
                )
                removed_row["Change Type"] = "Removed"
                removed_row["Row Index"] = removed_idx
                removed_row["Action Description"] = (
                    f"Row removed as duplicate of row {kept_idx}"
                )
                log_rows.extend([kept_row, removed_row])
            change_log_df = pd.DataFrame(log_rows)
            final_df.to_csv("final_output.csv", index=False)
            change_log_df.to_csv("change_log.csv", index=False)
            st.success(
                ":white_check_mark: Final file saved as `final_output.csv` and change log saved as `change_log.csv`"
            )
            st.download_button(
                ":arrow_down: Download Cleaned File",
                data=final_df.to_csv(index=False),
                file_name="final_output.csv",
                mime="text/csv",
            )
            st.download_button(
                ":arrow_down: Download Change Log",
                data=change_log_df.to_csv(index=False),
                file_name="change_log.csv",
                mime="text/csv",
            )
        else:
            st.warning(":warning: No rows marked as duplicates.")
else:
    st.info(":point_up_2: Please upload a CSV file to begin.")
