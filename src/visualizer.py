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

        # Color-coding according to entity type
        if "Offer" in node.get("labels", []) or node_type == "Offer":
            color = {"background": "#3B82F6", "border": "#1D4ED8", "highlight": "#60A5FA"}
            shape = "box"
            size = 25
        elif "Company" in node.get("labels", []) or node_type == "Company":
            color = {"background": "#10B981", "border": "#047857", "highlight": "#34D399"}
            shape = "ellipse"
            size = 20
        elif "ContactPerson" in node.get("labels", []) or node_type == "ContactPerson":
            color = {"background": "#F59E0B", "border": "#B45309", "highlight": "#FBBF24"}
            shape = "diamond"
            size = 22
        elif "Domain" in node.get("labels", []) or node_type == "Domain":
            color = {"background": "#8B5CF6", "border": "#6D28D9", "highlight": "#A78BFA"}
            shape = "dot"
            size = 18
        else:
            color = {"background": "#9CA3AF", "border": "#4B5563", "highlight": "#D1D5DB"}
            shape = "dot"
            size = 15

        vis_nodes.append({
            "id": idx,
            "label": f"{node_type}\n{label}",
            "title": f"Type: {node_type}<br>Name: {label}",
            "color": color,
            "shape": shape,
            "font": {"color": "#FFFFFF" if shape in ("box", "ellipse") else "#1F2937", "size": 13, "face": "Helvetica"},
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
                "color": {"color": "#64748B", "highlight": "#3B82F6"},
                "font": {"size": 10, "align": "middle", "color": "#475569"},
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
          border: 1px solid #E2E8F0;
          border-radius: 8px;
          background: #F8FAFC;
        }}
        .legend {{
          display: flex;
          gap: 16px;
          padding: 8px 12px;
          background: #FFFFFF;
          border-bottom: 1px solid #E2E8F0;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          font-size: 12px;
        }}
        .legend-item {{
          display: flex;
          align-items: center;
          gap: 6px;
        }}
        .legend-badge {{
          width: 12px;
          height: 12px;
          border-radius: 3px;
        }}
      </style>
    </head>
    <body>
      <div class="legend">
        <div class="legend-item"><span class="legend-badge" style="background: #3B82F6;"></span> <strong>Offer</strong></div>
        <div class="legend-item"><span class="legend-badge" style="background: #10B981; border-radius: 50%;"></span> <strong>Company</strong></div>
        <div class="legend-item"><span class="legend-badge" style="background: #F59E0B; transform: rotate(45deg);"></span> <strong>Contact Person</strong></div>
        <div class="legend-item"><span class="legend-badge" style="background: #8B5CF6; border-radius: 50%;"></span> <strong>Domain</strong></div>
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
