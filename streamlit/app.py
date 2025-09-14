import streamlit as st

from utils import (
    load_env,
    load_flows,
    save_flows,
    get_default_model,
    format_prompt,
    generate,
)


st.set_page_config(page_title="Flow Builder", layout="wide")
load_env()

st.title("Flow Builder")
st.caption("Create connected nodes. Click a node to edit its prompt and model parameters in a popup.")


# Load flows and pick active
if "flows_state" not in st.session_state:
    st.session_state["flows_state"] = load_flows()

data = st.session_state["flows_state"]
flows = data.get("flows", [])
active = data.get("active", flows[0]["name"] if flows else "Blog")
current = next((f for f in flows if f.get("name") == active), flows[0] if flows else {"name": "Blog", "steps": []})
steps = current.setdefault("steps", [])


# Outputs storage
if "node_outputs" not in st.session_state:
    st.session_state["node_outputs"] = {}


def step_key(idx: int) -> str:
    return steps[idx].get("output_key", f"step{idx+1}")


def move_item(idx: int, direction: int) -> None:
    j = idx + direction
    if 0 <= j < len(steps):
        steps[idx], steps[j] = steps[j], steps[idx]


def delete_item(idx: int) -> None:
    del steps[idx]


def add_item() -> None:
    i = len(steps)
    steps.append(
        {
            "label": f"Step {i+1}",
            "output_key": f"step{i+1}",
            "template": "",
            "provider": "Groq",
            "model": get_default_model("Groq"),
            "temperature": 0.7,
            "max_tokens": 1200,
            "top_p": 1.0,
        }
    )


def open_editor(idx: int) -> None:
    st.session_state["edit_idx"] = idx


@st.dialog("Edit Node")
def edit_node(idx: int):
    s = steps[idx]
    st.markdown(f"Editing node #{idx+1}")
    cols = st.columns([3, 2])
    with cols[0]:
        s["label"] = st.text_input("Label", value=s.get("label", f"Step {idx+1}"), key=f"label_{idx}")
        s["output_key"] = st.text_input("Output key", value=s.get("output_key", f"step{idx+1}"), key=f"key_{idx}")
        s["template"] = st.text_area("Prompt template", value=s.get("template", ""), height=220, key=f"tmpl_{idx}")
    with cols[1]:
        s["provider"] = st.selectbox("Provider", ["Groq", "Gemini"], index=0 if s.get("provider", "Groq") == "Groq" else 1, key=f"prov_{idx}")
        s["model"] = st.text_input("Model", value=s.get("model", get_default_model(s.get("provider", "Groq"))), key=f"model_{idx}")
        s["temperature"] = float(
            st.number_input("Temperature", min_value=0.0, max_value=2.0, value=float(s.get("temperature", 0.7)), step=0.1, key=f"temp_{idx}")
        )
        s["top_p"] = float(
            st.number_input("Top P", min_value=0.0, max_value=1.0, value=float(s.get("top_p", 1.0)), step=0.05, key=f"topp_{idx}")
        )
        s["max_tokens"] = int(
            st.number_input("Max tokens", min_value=1, max_value=4000, value=int(s.get("max_tokens", 1200)), step=50, key=f"maxtok_{idx}")
        )
    st.divider()
    # Optional quick test-run in dialog
    st.markdown("#### Test run (optional)")
    if st.button("Run Test", key=f"run_test_{idx}"):
        try:
            variables = dict(st.session_state.get("node_outputs", {}))
            prompt_text = format_prompt(s.get("template", ""), variables)
            out = generate(
                s.get("provider", "Groq"),
                prompt_text,
                None,
                s.get("model", get_default_model(s.get("provider", "Groq"))),
                float(s.get("temperature", 0.7)),
                int(s.get("max_tokens", 1200)),
                float(s.get("top_p", 1.0)),
            )
            st.text_area("Output", value=out, height=200)
        except Exception as e:  # noqa: BLE001
            st.error(str(e))
    st.divider()
    if st.button("Done", type="primary"):
        st.rerun()


# Toolbar
toolbar = st.columns([1, 1, 4, 2])
with toolbar[0]:
    if st.button("Add Node"):
        add_item()
        st.rerun()
with toolbar[1]:
    if st.button("Save Flow", type="primary"):
        # Build nodes and auto-connect linearly
        nodes = []
        for i, s in enumerate(steps):
            nodes.append(
                {
                    "id": i + 1,
                    "label": s.get("label", f"Step {i+1}"),
                    "output_key": s.get("output_key", f"step{i+1}"),
                    "template": s.get("template", ""),
                    "provider": s.get("provider", "Groq"),
                    "model": s.get("model", get_default_model(s.get("provider", "Groq"))),
                    "temperature": float(s.get("temperature", 0.7)),
                    "max_tokens": int(s.get("max_tokens", 1200)),
                    "top_p": float(s.get("top_p", 1.0)),
                }
            )
        edges = []
        for i in range(1, len(nodes)):
            edges.append({"source": i, "target": i + 1})
        current["graph"] = {"nodes": nodes, "edges": edges}
        save_flows(data)
        st.success("Flow saved.")
with toolbar[2]:
    # Export JSON
    import json

    export_payload = {
        "name": current.get("name", "Flow"),
        "label": current.get("label", current.get("name", "Flow")),
        "steps": steps,
        "graph": current.get("graph", {}),
    }
    st.download_button(
        "Export JSON",
        data=json.dumps(export_payload, indent=2),
        file_name=f"{current.get('name','flow')}.json",
        mime="application/json",
    )
with toolbar[3]:
    up = st.file_uploader("Import JSON", type=["json"], label_visibility="collapsed")
    if up is not None:
        try:
            payload = json.loads(up.getvalue().decode("utf-8"))
            current["name"] = payload.get("name", current.get("name", "Flow"))
            current["label"] = payload.get("label", current.get("label", current.get("name", "Flow")))
            current["steps"] = payload.get("steps", [])
            current["graph"] = payload.get("graph", {})
            save_flows(data)
            st.success("Imported flow JSON.")
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Import failed: {e}")


# Node grid
st.subheader("Nodes")
if steps:
    cols = st.columns(4)
    for i, s in enumerate(steps):
        c = cols[i % 4]
        with c:
            with st.container(border=True):
                lbl = s.get("label", f"Step {i+1}")
                keyv = s.get("output_key", f"step{i+1}")
                st.markdown(f"**{i+1}. {lbl}**\n\n`{keyv}`")
                bcols = st.columns([1, 1, 1, 1])
                with bcols[0]:
                    if st.button("Edit", key=f"edit_{i}"):
                        open_editor(i)
                with bcols[1]:
                    if st.button("Run", key=f"run_{i}"):
                        try:
                            variables = dict(st.session_state.get("node_outputs", {}))
                            prompt_text = format_prompt(s.get("template", ""), variables)
                            out = generate(
                                s.get("provider", "Groq"),
                                prompt_text,
                                None,
                                s.get("model", get_default_model(s.get("provider", "Groq"))),
                                float(s.get("temperature", 0.7)),
                                int(s.get("max_tokens", 1200)),
                                float(s.get("top_p", 1.0)),
                            )
                            st.session_state["node_outputs"][s.get("output_key", f"step{i+1}")] = out
                            st.rerun()
                        except Exception as e:  # noqa: BLE001
                            st.error(str(e))
                with bcols[2]:
                    if st.button("Up", key=f"up_{i}"):
                        move_item(i, -1)
                        st.rerun()
                with bcols[3]:
                    if st.button("Down", key=f"down_{i}"):
                        move_item(i, +1)
                        st.rerun()
                if st.button("Delete", key=f"del_{i}"):
                    delete_item(i)
                    st.rerun()
else:
    st.info("No nodes yet. Click 'Add Node'.")


# Outputs
st.subheader("Outputs")
outs = st.session_state.get("node_outputs", {})
if outs:
    for i, s in enumerate(steps):
        key = s.get("output_key", f"step{i+1}")
        if key in outs:
            st.markdown(f"### {i+1}. {s.get('label', f'Step {i+1}')} ({key})")
            st.code(outs[key] or "<empty>", language="markdown")
    if st.button("Clear Outputs"):
        st.session_state["node_outputs"] = {}
        st.rerun()
