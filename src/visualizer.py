"""
Interactive Graph Visualization Component for OfferLens AI.
Renders Neo4j graph nodes and edges into an interactive vis.js HTML graph.
"""

import json
from typing import Dict, Any, List


def generate_interactive_graph_html(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    height: int = 500,
) -> str:
    """
    Generate an interactive vis-network HTML canvas from Neo4j nodes and edges.
    """
    vis_nodes = []
    node_id_map = {}

    for idx, node in enumerate(nodes):
        raw_id = node.get("id", idx)
        node_id_map[raw_id] = idx
        node_type = node.get("type", "Unknown")
        label = node.get("name", str(raw_id))

        # Color-coding according to entity type (Editorial Palette: Burgundy #702632, Rose #B77C82, Beige #EDE3D2)
        if "Offer" in node.get("labels", []) or node_type == "Offer":
            color = {"background": "#702632", "border": "#4A1721", "highlight": "#B77C82"}
            shape = "box"
            size = 25
        elif "Company" in node.get("labels", []) or node_type == "Company":
            color = {"background": "#EDE3D2", "border": "#702632", "highlight": "#D8C9B7"}
            shape = "ellipse"
            size = 22
        elif "ContactPerson" in node.get("labels", []) or node_type == "ContactPerson":
            color = {"background": "#B77C82", "border": "#4A1721", "highlight": "#D8C9B7"}
            shape = "diamond"
            size = 24
        elif "Domain" in node.get("labels", []) or node_type == "Domain":
            color = {"background": "#4A1721", "border": "#292320", "highlight": "#702632"}
            shape = "dot"
            size = 18
        else:
            color = {"background": "#EDE3D2", "border": "#D8C9B7", "highlight": "#B77C82"}
            shape = "dot"
            size = 15

        vis_nodes.append({
            "id": idx,
            "label": f"{node_type}\n{label}",
            "title": f"Type: {node_type}<br>Name: {label}",
            "color": color,
            "shape": shape,
            "font": {"color": "#FFFFFF" if shape in ("box", "diamond", "dot") and color["background"] != "#EDE3D2" else "#292320", "size": 12, "face": "Helvetica, Arial, sans-serif"},
            "margin": 10,
        })

    vis_edges = []
    for edge in edges:
        source_id = edge.get("source")
        target_id = edge.get("target")
        edge_type = edge.get("type", "CONNECTED_TO")

        if source_id in node_id_map and target_id in node_id_map:
            vis_edges.append({
                "from": node_id_map[source_id],
                "to": node_id_map[target_id],
                "label": edge_type,
                "arrows": "to",
                "color": {"color": "#B77C82", "highlight": "#702632"},
                "font": {"size": 10, "align": "middle", "color": "#746A61", "face": "Helvetica, Arial, sans-serif"},
            })

    nodes_json = json.dumps(vis_nodes)
    edges_json = json.dumps(vis_edges)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
      <style>
        #network-canvas {{
          width: 100%;
          height: {height}px;
          border: 1px solid #D8C9B7;
          border-radius: 8px;
          background: #F7F2E8;
        }}
        .legend {{
          display: flex;
          gap: 20px;
          padding: 10px 16px;
          background: #EDE3D2;
          border-bottom: 1px solid #D8C9B7;
          border-top-left-radius: 8px;
          border-top-right-radius: 8px;
          font-family: 'Playfair Display', Georgia, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          font-size: 11px;
          color: #746A61;
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }}
        .legend-item {{
          display: flex;
          align-items: center;
          gap: 7px;
        }}
        .legend-badge {{
          width: 11px;
          height: 11px;
          border-radius: 2px;
        }}
      </style>
    </head>
    <body>
      <div class="legend">
        <div class="legend-item"><span class="legend-badge" style="background: #702632;"></span> <strong>Offer</strong></div>
        <div class="legend-item"><span class="legend-badge" style="background: #EDE3D2; border: 1px solid #702632; border-radius: 50%;"></span> <strong>Company</strong></div>
        <div class="legend-item"><span class="legend-badge" style="background: #B77C82; transform: rotate(45deg);"></span> <strong>Contact Person</strong></div>
        <div class="legend-item"><span class="legend-badge" style="background: #4A1721; border-radius: 50%;"></span> <strong>Domain</strong></div>
      </div>
      <div id="network-canvas"></div>
      <script type="text/javascript">


        var container = document.getElementById('network-canvas');
        var data = {{
          nodes: new vis.DataSet({nodes_json}),
          edges: new vis.DataSet({edges_json})
        }};
        var options = {{
          physics: {{
            barnesHut: {{
              gravitationalConstant: -3000,
              springLength: 120,
              springConstant: 0.04
            }}
          }},
          interaction: {{
            hover: true,
            tooltipDelay: 100,
            navigationButtons: true,
            keyboard: true
          }}
        }};
        var network = new vis.Network(container, data, options);
      </script>
    </body>
    </html>
    """
    return html
