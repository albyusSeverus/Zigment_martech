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
st.caption("Home shows presets. Click a card to open the editor. In the editor, click Run Flow to execute all nodes and see output on the right.")


# Load flows and pick active
if "flows_state" not in st.session_state:
    st.session_state["flows_state"] = load_flows()

data = st.session_state["flows_state"]
flows = data.get("flows", [])
active = data.get("active", flows[0]["name"] if flows else "Blog")
current = next((f for f in flows if f.get("name") == active), flows[0] if flows else {"name": "Blog", "steps": []})
steps = current.setdefault("steps", [])


def ensure_default_blog_flow() -> None:
    names = [f.get("name") for f in flows]
    if "Blog" in names:
        return
    outline_t = (
        "Create a clear, hierarchical outline for a blog post on growth marketing with agentic AI.\n"
        "Return Markdown headings and bullet points only."
    )
    blog_t = (
        "Using the approved outline below, write a comprehensive blog post in Markdown.\n\n"
        "Outline:\n{outline}\n\n"
        "Use an engaging but precise tone and concrete examples."
    )
    flows.append(
        {
            "name": "Blog",
            "label": "Blog",
            "steps": [
                {
                    "label": "Outline",
                    "output_key": "outline",
                    "template": outline_t,
                    "provider": "Groq",
                    "model": get_default_model("Groq"),
                    "temperature": 0.7,
                    "max_tokens": 800,
                    "top_p": 1.0,
                },
                {
                    "label": "Blog",
                    "output_key": "blog",
                    "template": blog_t,
                    "provider": "Groq",
                    "model": get_default_model("Groq"),
                    "temperature": 0.7,
                    "max_tokens": 1200,
                    "top_p": 1.0,
                },
            ],
            "graph": {},
        }
    )
    data["active"] = "Blog"
    save_flows(data)


# Screen routing: home (cards) -> editor
if "screen" not in st.session_state:
    st.session_state["screen"] = "home"

screen = st.session_state["screen"]


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


def render_editor():
    # Two-column layout: left editor, right outputs
    left, right = st.columns([7, 5])

    with left:
        toolbar = st.columns([1, 1, 1, 2])
        with toolbar[0]:
            if st.button("Add Node"):
                add_item()
                st.rerun()
        with toolbar[1]:
            if st.button("Save Flow"):
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
            if st.button("Run Flow", type="primary"):
                # Ensure we have latest nodes
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
                # Linear run
                st.session_state["node_outputs"] = {}
                for nd in nodes:
                    variables = dict(st.session_state.get("node_outputs", {}))
                    prompt_text = format_prompt(nd.get("template", ""), variables)
                    try:
                        out = generate(
                            nd.get("provider", "Groq"),
                            prompt_text,
                            None,
                            nd.get("model", get_default_model(nd.get("provider", "Groq"))),
                            float(nd.get("temperature", 0.7)),
                            int(nd.get("max_tokens", 1200)),
                            float(nd.get("top_p", 1.0)),
                        )
                        st.session_state["node_outputs"][nd.get("output_key", f"step{nd.get('id','')}")] = out
                    except Exception as e:  # noqa: BLE001
                        st.error(str(e))

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

    with right:
        st.subheader("Output")
        outs = st.session_state.get("node_outputs", {})
        # Show latest output if any; else empty
        if outs:
            # Prefer last node's key
            key_order = [s.get("output_key", f"step{i+1}") for i, s in enumerate(steps)]
            last_key = key_order[-1] if key_order else next(iter(outs))
            st.code(outs.get(last_key, ""), language="markdown")
        else:
            st.caption("Run the flow to see output here.")


# Trigger editor dialog
if "edit_idx" in st.session_state and st.session_state["edit_idx"] is not None:
    edit_node(int(st.session_state["edit_idx"]))
    st.session_state["edit_idx"] = None


# Home vs Editor views
if screen == "home":
    st.subheader("Presets")
    cc = st.columns(3)
    with cc[0]:
        with st.container(border=True):
            st.markdown("**Blogs**")
            st.caption("Outline → Blog flow")
            if st.button("Open", key="open_blog_card"):
                ensure_default_blog_flow()
                st.session_state["screen"] = "editor"
                st.rerun()
else:
    render_editor()

