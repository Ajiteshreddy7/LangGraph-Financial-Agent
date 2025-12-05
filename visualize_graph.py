from agent import app

print("Building graph...")
graph = app

output_path = "graph_visualization.png"

print(f"Generating visualization via Mermaid API and saving to '{output_path}'...")
try:
    # Get the graph object
    graph_drawable = graph.get_graph()

    # This method uses an online API to render the PNG, returning the image bytes
    png_bytes = graph_drawable.draw_mermaid_png()

    # Write the received bytes to a file
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"✅ Successfully saved graph visualization to '{output_path}'")

except Exception as e:
    print(f"❌ Could not draw or save graph. Error: {e}")
    print("This may be due to a temporary issue with the Mermaid API or a network problem.") 