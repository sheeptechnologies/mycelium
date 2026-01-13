#!/usr/bin/env python3
"""
Command-line interface for Mycelium stack graphs.

Usage:
    python cli.py visualize <input_file> [options]
    python cli.py serialize <input_file> [options]
    python cli.py deserialize <graph_file> [options]
    python cli.py validate <graph_file>
"""

import argparse
import sys
import json
from pathlib import Path

from src.graph_builder import StackGraphBuilder
from src.visualizer import visualize_graph
from src.serialization import (
    serialize_graph,
    deserialize_graph,
    save_graph,
    load_graph,
    GraphSerializer
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Mycelium - Stack graph library for Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize a Python file (generates HTML)
  python cli.py visualize example.py
  python cli.py visualize example.py -o graph.html

  # Serialize a graph to JSON
  python cli.py serialize example.py -o graph.json

  # Deserialize and visualize from JSON
  python cli.py deserialize graph.json -o restored.html

  # Validate a serialized graph
  python cli.py validate graph.json

  # Backward compatibility (no subcommand defaults to visualize)
  python cli.py example.py -o graph.html
        """
    )

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # === VISUALIZE SUBCOMMAND ===
    visualize_parser = subparsers.add_parser(
        "visualize",
        help="Generate HTML visualization from source code"
    )
    visualize_parser.add_argument("input_file", help="Python source file")
    visualize_parser.add_argument("-o", "--output", help="Output HTML file")
    visualize_parser.add_argument("-l", "--language", default="python", choices=["python"])
    visualize_parser.add_argument("-t", "--title", help="Graph title")
    visualize_parser.add_argument("-v", "--verbose", action="store_true")

    # === SERIALIZE SUBCOMMAND ===
    serialize_parser = subparsers.add_parser(
        "serialize",
        help="Serialize graph to JSON"
    )
    serialize_parser.add_argument("input_file", help="Python source file")
    serialize_parser.add_argument("-o", "--output", required=True, help="Output JSON file")
    serialize_parser.add_argument("-l", "--language", default="python", choices=["python"])
    serialize_parser.add_argument("-v", "--verbose", action="store_true")

    # === DESERIALIZE SUBCOMMAND ===
    deserialize_parser = subparsers.add_parser(
        "deserialize",
        help="Deserialize graph from JSON and visualize"
    )
    deserialize_parser.add_argument("graph_file", help="Serialized graph JSON file")
    deserialize_parser.add_argument("-o", "--output", help="Output HTML file (default: <graph_file>.html)")
    deserialize_parser.add_argument("-t", "--title", help="Graph title")
    deserialize_parser.add_argument("-v", "--verbose", action="store_true")
    deserialize_parser.add_argument("--no-validate", action="store_true", help="Skip schema validation")

    # === VALIDATE SUBCOMMAND ===
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a serialized graph JSON"
    )
    validate_parser.add_argument("graph_file", help="Serialized graph JSON file")
    validate_parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    # Backward compatibility: if no command and first arg looks like a file, default to visualize
    if not args.command:
        if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            # Treat as visualize command
            sys.argv.insert(1, 'visualize')
            return main()
        else:
            parser.print_help()
            sys.exit(0)

    # Dispatch to appropriate handler
    try:
        if args.command == "visualize":
            handle_visualize(args)
        elif args.command == "serialize":
            handle_serialize(args)
        elif args.command == "deserialize":
            handle_deserialize(args)
        elif args.command == "validate":
            handle_validate(args)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def handle_visualize(args):
    """Handle visualize command."""
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

    source_bytes = input_path.read_bytes()
    source_code = source_bytes.decode("utf-8", errors="replace")
    output_file = visualize_graph(
        roots,
        str(output_path),
        title=title,
        source_code=source_code,
        source_path=str(input_path),
    )

    if args.verbose:
        print()

    print(f"✓ Successfully generated graph visualization")
    print(f"  Output: {output_file}")


def handle_serialize(args):
    """Handle serialize command."""
    input_path = Path(args.input_file)

    if not input_path.exists():
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    if not input_path.is_file():
        print(f"Error: Not a file: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)

    if args.verbose:
        print(f"Input file: {input_path}")
        print(f"Output file: {output_path}")
        print(f"Language: {args.language}")
        print()

    # Build stack graph
    if args.verbose:
        print("Building stack graph...")

    builder = StackGraphBuilder(language=args.language)
    roots = builder.build_from_file(str(input_path))

    if args.verbose:
        print(f"Graph built successfully with {len(roots)} root node(s)")

    # Serialize to JSON
    if args.verbose:
        print("Serializing graph to JSON...")

    metadata = {
        "source_file": str(input_path),
        "language": args.language,
    }

    save_graph(roots, str(output_path), metadata=metadata)

    if args.verbose:
        print()

    print(f"✓ Successfully serialized graph")
    print(f"  Output: {output_path}")
    print(f"  Nodes: {len(roots)}")


def handle_deserialize(args):
    """Handle deserialize command."""
    graph_path = Path(args.graph_file)

    if not graph_path.exists():
        print(f"Error: File not found: {args.graph_file}", file=sys.stderr)
        sys.exit(1)

    if not graph_path.is_file():
        print(f"Error: Not a file: {args.graph_file}", file=sys.stderr)
        sys.exit(1)

    # Determine output file
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = graph_path.with_suffix(".html")

    # Determine title
    if args.title:
        title = args.title
    else:
        title = f"Stack Graph (Deserialized): {graph_path.stem}"

    if args.verbose:
        print(f"Graph file: {graph_path}")
        print(f"Output file: {output_path}")
        print(f"Title: {title}")
        print()

    # Deserialize graph
    if args.verbose:
        print("Deserializing graph from JSON...")

    validate = not args.no_validate
    roots, metadata = load_graph(str(graph_path), validate=validate)

    if args.verbose:
        print(f"Graph loaded successfully with {len(roots)} root node(s)")
        if metadata:
            print(f"Metadata: {metadata}")

    # Generate visualization
    if args.verbose:
        print("Generating HTML visualization...")

    # Try to load source code from metadata
    source_code = None
    source_path = metadata.get("source_file", "unknown")

    if source_path and source_path != "unknown":
        try:
            source_code = Path(source_path).read_text()
        except:
            pass

    output_file = visualize_graph(
        roots,
        str(output_path),
        title=title,
        source_code=source_code,
        source_path=source_path,
    )

    if args.verbose:
        print()

    print(f"✓ Successfully deserialized and visualized graph")
    print(f"  Output: {output_file}")


def handle_validate(args):
    """Handle validate command."""
    graph_path = Path(args.graph_file)

    if not graph_path.exists():
        print(f"Error: File not found: {args.graph_file}", file=sys.stderr)
        sys.exit(1)

    if not graph_path.is_file():
        print(f"Error: Not a file: {args.graph_file}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Validating: {graph_path}")
        print()

    try:
        # Load and validate
        json_str = graph_path.read_text()
        data = json.loads(json_str)

        # Validate schema
        serializer = GraphSerializer()
        serializer._validate_schema(data)

        # Check version
        version = data.get("version", "unknown")
        if not serializer._is_compatible_version(version):
            print(f"⚠ Warning: Incompatible version {version}", file=sys.stderr)

        # Deserialize to ensure graph can be reconstructed
        roots, metadata = deserialize_graph(json_str, validate=True)

        # Print summary
        print(f"✓ Graph is valid")
        print(f"  Version: {version}")
        print(f"  Nodes: {len(data['nodes'])}")
        print(f"  Roots: {len(data['roots'])}")

        if metadata:
            print(f"  Metadata:")
            for key, value in metadata.items():
                print(f"    {key}: {value}")

        if args.verbose:
            print()
            print("Schema validation passed")
            print("Graph deserialization successful")

    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"✗ Validation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
