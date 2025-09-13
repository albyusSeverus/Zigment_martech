import streamlit as st

from utils import load_env, load_flow, save_flow


st.set_page_config(page_title="Flow Builder", layout="wide")

load_env()

st.title("Flow Builder")
st.caption("Design your content flow with ordered steps. Each step has a label, an output key, and an editable prompt template.")

if "flow_editor" not in st.session_state:
    st.session_state["flow_editor"] = load_flow()

flow = st.session_state["flow_editor"]

st.markdown("Variables available in templates: `{idea}`, `{notes}`, plus any prior step outputs referenced by their `output_key` (e.g., `{outline}`).")

def move_item(idx: int, direction: int) -> None:
    j = idx + direction
    if 0 <= j < len(flow):
        flow[idx], flow[j] = flow[j], flow[idx]

def delete_item(idx: int) -> None:
    del flow[idx]

def add_item() -> None:
    flow.append({"label": "New Step", "output_key": f"step{len(flow)+1}", "template": "Write something about {idea}."})

for i, step in enumerate(flow):
    with st.container(border=True):
        cols = st.columns([6, 2, 2, 2])
        with cols[0]:
            step["label"] = st.text_input(f"Label #{i+1}", value=step.get("label", "Step"), key=f"label_{i}")
        with cols[1]:
            if st.button("Up", key=f"up_{i}"):
                move_item(i, -1)
                st.rerun()
        with cols[2]:
            if st.button("Down", key=f"down_{i}"):
                move_item(i, +1)
                st.rerun()
        with cols[3]:
            if st.button("Delete", key=f"del_{i}"):
                delete_item(i)
                st.rerun()

        step["output_key"] = st.text_input("Output key", value=step.get("output_key", "step"), key=f"key_{i}")
        step["template"] = st.text_area(
            "Prompt template",
            value=step.get("template", ""),
            height=180,
            key=f"tmpl_{i}",
        )

st.divider()

cols = st.columns([1, 1, 2])
with cols[0]:
    if st.button("Add Step", type="secondary"):
        add_item()
        st.rerun()
with cols[1]:
    if st.button("Save Flow", type="primary"):
        try:
            save_flow(flow)
            st.success("Flow saved.")
        except Exception as e:  # noqa: BLE001
            st.error(str(e))
