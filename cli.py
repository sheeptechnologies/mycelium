#!/usr/bin/env python3
"""
Command-line interface for Mycelium stack graphs.

Usage:
    python cli.py <input_file> [options]
    python -m src.cli <input_file> [options]
"""

import argparse
import sys
from pathlib import Path

from src.graph_builder import StackGraphBuilder
from src.visualizer import visualize_graph


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate stack graph visualization from Python source files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate graph from a Python file
  python cli.py example.py
  
  # Specify output file
  python cli.py example.py -o output.html
  
  # Specify language (default: python)
  python cli.py example.py -l python
  
  # Add custom title
  python cli.py example.py -t "My Project Graph"
        """
    )
    
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the Python source file to analyze"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output HTML file path (default: <input_file>.html)"
    )
    
    parser.add_argument(
        "-l", "--language",
        type=str,
        default="python",
        choices=["python"],
        help="Programming language (default: python)"
    )
    
    parser.add_argument(
        "-t", "--title",
        type=str,
        default=None,
        help="Title for the graph visualization"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    
    if not input_path.is_file():
        print(f"Error: Not a file: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    
    # Determine output file
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix(".html")
    
    # Determine title
    if args.title:
        title = args.title
    else:
        title = f"Stack Graph: {input_path.name}"
    
    if args.verbose:
        print(f"Input file: {input_path}")
        print(f"Output file: {output_path}")
        print(f"Language: {args.language}")
        print(f"Title: {title}")
        print()
    
    try:
        # Build stack graph
        if args.verbose:
            print("Building stack graph...")
        
        builder = StackGraphBuilder(language=args.language)
        roots = builder.build_from_file(str(input_path))
        
        if args.verbose:
            print(f"Graph built successfully with {len(roots)} root node(s)")
        
        # Generate visualization
        if args.verbose:
            print("Generating HTML visualization...")
        
        output_file = visualize_graph(roots, str(output_path), title=title)
        
        if args.verbose:
            print()
        
        print(f"✓ Successfully generated graph visualization")
        print(f"  Output: {output_file}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
