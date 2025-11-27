"""Mind map exporter for various formats"""

import json
from typing import Dict, Any
from ..models import MindMap, MindMapNode


class MindMapExporter:
    """Exporter for mind maps to various formats"""
    
    def __init__(self, mind_map: MindMap):
        """
        Initialize exporter with a mind map
        
        Args:
            mind_map: MindMap instance to export
        """
        self.mind_map = mind_map
    
    def export_as_json(self) -> bytes:
        """
        Export mind map as JSON
        
        Returns:
            JSON-formatted bytes
        """
        json_str = json.dumps(self.mind_map.to_dict(), indent=2, ensure_ascii=False)
        return json_str.encode('utf-8')
    
    def export_as_markdown(self) -> bytes:
        """
        Export mind map as Markdown with hierarchical structure
        
        Returns:
            Markdown-formatted bytes
        """
        lines = []
        
        lines.append(f"# {self.mind_map.root_node.content}")
        lines.append("")
        lines.append(f"**思维导图版本**: {self.mind_map.version}")
        lines.append(f"**创建时间**: {self.mind_map.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**创建者**: {self.mind_map.created_by}")
        lines.append("")
        
        # Recursively build tree structure
        def build_tree(node_id: str, indent_level: int = 0):
            node = self.mind_map.nodes.get(node_id)
            if not node:
                return
            
            # Skip root node (already in title)
            if node.level > 0:
                indent = "  " * (indent_level - 1)
                lines.append(f"{indent}- {node.content}")
                
                # Add message references if any
                if node.message_references:
                    ref_str = ", ".join(node.message_references[:3])  # Show first 3
                    if len(node.message_references) > 3:
                        ref_str += f" (+{len(node.message_references) - 3} more)"
                    lines.append(f"{indent}  *相关消息: {ref_str}*")
            
            # Process children
            for child_id in node.children_ids:
                build_tree(child_id, indent_level + 1)
        
        # Start from root
        build_tree(self.mind_map.root_node.id, 0)
        
        markdown_str = "\n".join(lines)
        return markdown_str.encode('utf-8')
    
    def export_as_svg(self) -> bytes:
        """
        Export mind map as SVG image
        
        Returns:
            SVG-formatted bytes
        """
        try:
            import graphviz
        except ImportError:
            raise ImportError("graphviz package is required for SVG export. Install with: pip install graphviz")
        
        # Create a new directed graph
        dot = graphviz.Digraph(comment=self.mind_map.root_node.content)
        dot.attr(rankdir='LR')  # Left to right layout
        dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
        
        # Add nodes and edges
        def add_nodes_and_edges(node_id: str):
            node = self.mind_map.nodes.get(node_id)
            if not node:
                return
            
            # Truncate long content for display
            display_content = node.content
            if len(display_content) > 50:
                display_content = display_content[:47] + "..."
            
            # Add node with styling based on level
            if node.level == 0:
                dot.node(node_id, display_content, fillcolor='lightcoral', fontsize='14', fontname='Arial')
            elif node.level == 1:
                dot.node(node_id, display_content, fillcolor='lightgreen', fontsize='12', fontname='Arial')
            else:
                dot.node(node_id, display_content, fillcolor='lightblue', fontsize='10', fontname='Arial')
            
            # Add edges to children
            for child_id in node.children_ids:
                dot.edge(node_id, child_id)
                add_nodes_and_edges(child_id)
        
        # Start from root
        add_nodes_and_edges(self.mind_map.root_node.id)
        
        # Render to SVG
        svg_data = dot.pipe(format='svg')
        return svg_data
    
    def export_as_png(self) -> bytes:
        """
        Export mind map as PNG image
        
        Returns:
            PNG-formatted bytes
        """
        try:
            import graphviz
        except ImportError:
            raise ImportError("graphviz package is required for PNG export. Install with: pip install graphviz")
        
        # Create a new directed graph
        dot = graphviz.Digraph(comment=self.mind_map.root_node.content)
        dot.attr(rankdir='LR')  # Left to right layout
        dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
        dot.attr(dpi='300')  # High resolution
        
        # Add nodes and edges
        def add_nodes_and_edges(node_id: str):
            node = self.mind_map.nodes.get(node_id)
            if not node:
                return
            
            # Truncate long content for display
            display_content = node.content
            if len(display_content) > 50:
                display_content = display_content[:47] + "..."
            
            # Add node with styling based on level
            if node.level == 0:
                dot.node(node_id, display_content, fillcolor='lightcoral', fontsize='14', fontname='Arial')
            elif node.level == 1:
                dot.node(node_id, display_content, fillcolor='lightgreen', fontsize='12', fontname='Arial')
            else:
                dot.node(node_id, display_content, fillcolor='lightblue', fontsize='10', fontname='Arial')
            
            # Add edges to children
            for child_id in node.children_ids:
                dot.edge(node_id, child_id)
                add_nodes_and_edges(child_id)
        
        # Start from root
        add_nodes_and_edges(self.mind_map.root_node.id)
        
        # Render to PNG
        png_data = dot.pipe(format='png')
        return png_data
