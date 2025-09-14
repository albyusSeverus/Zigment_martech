import streamlit as st

from utils import load_env, load_flows, save_flows, get_default_model


st.set_page_config(page_title="Flow Builder", layout="wide")
load_env()

st.title("Flow Builder")
st.caption("Create connected nodes. Click a node to edit its prompt and model parameters in a popup.")

# Load flows; use single active flow
if "flows_state" not in st.session_state:
    st.session_state["flows_state"] = load_flows()

data = st.session_state["flows_state"]
flows = data.get("flows", [])
active = data.get("active", flows[0]["name"] if flows else "Blog")
current = next((f for f in flows if f.get("name") == active), flows[0] if flows else {"name": "Blog", "steps": []})
steps = current.setdefault("steps", [])

# Maintain connections as key-based edges for stability across reorders
if "edge_keys" not in st.session_state:
    # Initialize from any persisted graph
    ek: list[tuple[str, str]] = []
    graph = current.get("graph", {}) or {}
    nodes = graph.get("nodes", []) or []
    edges = graph.get("edges", []) or []
    id_to_key = {int(n.get("id", i + 1)): n.get("output_key", f"step{i+1}") for i, n in enumerate(nodes)}
    for e in edges:
        try:
            sk = id_to_key.get(int(e.get("source")))
            tk = id_to_key.get(int(e.get("target")))
            if sk and tk:
                ek.append((sk, tk))
        except Exception:
            pass
    st.session_state["edge_keys"] = ek

edge_keys: list[tuple[str, str]] = st.session_state["edge_keys"]

# Helpers
def step_key(idx: int) -> str:
    return steps[idx].get("output_key", f"step{idx+1}")

def move_item(idx: int, direction: int) -> None:
    j = idx + direction
    if 0 <= j < len(steps):
        steps[idx], steps[j] = steps[j], steps[idx]

def delete_item(idx: int) -> None:
    key = step_key(idx)
    del steps[idx]
    # Drop edges referencing this key
    st.session_state["edge_keys"] = [(s, t) for (s, t) in st.session_state["edge_keys"] if s != key and t != key]

def add_item() -> None:
    i = len(steps)
    steps.append({
        "label": f"Step {i+1}",
        "output_key": f"step{i+1}",
        "template": "Write about {idea}.",
        "provider": "Groq",
        "model": get_default_model("Groq"),
        "temperature": 0.7,
        "max_tokens": 1200,
        "top_p": 1.0,
    })


# Editor dialog
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
        s["temperature"] = float(st.number_input("Temperature", min_value=0.0, max_value=2.0, value=float(s.get("temperature", 0.7)), step=0.1, key=f"temp_{idx}"))
        s["top_p"] = float(st.number_input("Top P", min_value=0.0, max_value=1.0, value=float(s.get("top_p", 1.0)), step=0.05, key=f"topp_{idx}"))
        s["max_tokens"] = int(st.number_input("Max tokens", min_value=1, max_value=4000, value=int(s.get("max_tokens", 1200)), step=50, key=f"maxtok_{idx}"))
    st.divider()
    # Connections from this node
    keys = [step_key(i) for i in range(len(steps)) if i != idx]
    current_outs = [t for (skey, t) in edge_keys if skey == step_key(idx)]
    new_outs = st.multiselect("Connect to (downstream)", options=keys, default=current_outs, help="Edges from this node")
    # Update edges: remove old outs for this src; add new ones
    src = step_key(idx)
    kept = [(skey, t) for (skey, t) in edge_keys if skey != src]
    for tgt in new_outs:
        kept.append((src, tgt))
    st.session_state["edge_keys"] = kept
    st.divider()
    if st.button("Done", type="primary"):
        st.rerun()


# Toolbar
toolbar = st.columns([1, 1, 6])
with toolbar[0]:
    if st.button("Add Node"):
        add_item()
        st.rerun()
with toolbar[1]:
    if st.button("Save Flow", type="primary"):
        # Build nodes and edges and persist
        nodes = []
        for i, s in enumerate(steps):
            nodes.append({
                "id": i + 1,
                "label": s.get("label", f"Step {i+1}"),
                "output_key": s.get("output_key", f"step{i+1}"),
                "template": s.get("template", ""),
                "provider": s.get("provider", "Groq"),
                "model": s.get("model", get_default_model(s.get("provider", "Groq"))),
                "temperature": float(s.get("temperature", 0.7)),
                "max_tokens": int(s.get("max_tokens", 1200)),
                "top_p": float(s.get("top_p", 1.0)),
            })
        key_to_id = {n["output_key"]: n["id"] for n in nodes}
        edges = []
        for (skey, tkey) in st.session_state["edge_keys"]:
            if skey in key_to_id and tkey in key_to_id and skey != tkey:
                edges.append({"source": key_to_id[skey], "target": key_to_id[tkey]})
        current["graph"] = {"nodes": nodes, "edges": edges}
        save_flows(data)
        st.success("Flow saved.")


# Node grid (compact boxes)
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
                bcols = st.columns([1, 1, 1])
                with bcols[0]:
                    if st.button("Edit", key=f"edit_{i}"):
                        open_editor(i)
                with bcols[1]:
                    if st.button("Up", key=f"up_{i}"):
                        move_item(i, -1)
                        st.rerun()
                with bcols[2]:
                    if st.button("Down", key=f"down_{i}"):
                        move_item(i, +1)
                        st.rerun()
                if st.button("Delete", key=f"del_{i}"):
                    delete_item(i)
                    st.rerun()
else:
    st.info("No nodes yet. Click 'Add Node'.")


# Connections summary
st.subheader("Connections")
if edge_keys:
    for sk, tk in edge_keys:
        st.write(f"{sk} → {tk}")
else:
    st.caption("No connections defined.")


# Trigger editor dialog
if "edit_idx" in st.session_state and st.session_state["edit_idx"] is not None:
    edit_node(int(st.session_state["edit_idx"]))
    st.session_state["edit_idx"] = None

