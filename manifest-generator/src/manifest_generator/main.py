import json
import ast
import logging
from pathlib import Path
import sys
from typing import Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

TYPE_MAP = {
    "str": {"type": "string"},
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "bool": {"type": "boolean"},
}

class ManifestGenerationError(Exception):
    """Raised when manifest generation fails"""
    pass

class ManifestBuilder(ast.NodeVisitor):
    def __init__(self):
        self.input_schema = None
        self.output_schema = None
        self.config_schema = None
        self.type_definitions = {}
        self.current_file_ast = None

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions and process decorators"""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Attribute) and hasattr(decorator.value, 'id'):
                if decorator.value.id == "ManifestMarker":
                    schema = self.extract_class_schema(node)
                    if decorator.attr == "input":
                        self.input_schema = schema
                    elif decorator.attr == "output":
                        self.output_schema = schema
                    elif decorator.attr == "config":
                        self.config_schema = schema

    def extract_field_description(self, node: ast.Call) -> Optional[str]:
        """Extract description from Field if present"""
        for keyword in node.keywords:
            if keyword.arg == "description":
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value
        return None
    
    def clean_ast_nodes(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up AST nodes recursively from the schema"""
        if not isinstance(schema, dict):
            return schema
        
        cleaned = schema.copy()
        # Remove AST nodes
        if "_ast_node" in cleaned:
            del cleaned["_ast_node"]
        if "_field_node" in cleaned:
            del cleaned["_field_node"]
        
        # Clean nested structures
        for key, value in cleaned.items():
            if isinstance(value, dict):
                cleaned[key] = self.clean_ast_nodes(value)
            elif isinstance(value, list):
                cleaned[key] = [self.clean_ast_nodes(item) if isinstance(item, dict) else item 
                            for item in value]
        
        return cleaned
    
    def collect_type_definitions(self, node: ast.AST):
        """First pass: collect all class definitions"""
        for item in ast.walk(node):
            if isinstance(item, ast.ClassDef):
                # Check if it's an enum
                is_enum = any(isinstance(base, ast.Name) and base.id == 'Enum' 
                            for base in item.bases)
                if is_enum:
                    enum_values = []
                    for node in item.body:
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    if isinstance(node.value, ast.Constant):
                                        enum_values.append(node.value.value)
                    self.type_definitions[item.name] = {
                        "type": "string",
                        "enum": enum_values
                    }
                else:
                    # Regular class
                    properties = {}
                    for node in item.body:
                        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                            field_name = node.target.id
                            field_node = None
                            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "Field":
                                field_node = node.value
                            type_info = self.extract_type_annotation(node.annotation, field_node)
                            properties[field_name] = type_info
                    self.type_definitions[item.name] = {
                        "type": "object",
                        "properties": properties
                    }

    def extract_type_annotation(self, node: ast.AST, field_node: Optional[ast.Call] = None) -> Dict[str, Any]:
        """Extract type information from AST node"""
        type_info = {}
        
        if isinstance(node, ast.Name):
            # Check if it's a custom type we've collected
            if node.id in self.type_definitions:
                type_info = self.type_definitions[node.id].copy()
                # Process nested properties recursively
                if "properties" in type_info:
                    processed_properties = {}
                    for prop_name, prop_type in type_info["properties"].items():
                        processed_properties[prop_name] = self.extract_type_annotation(
                            prop_type.get("_ast_node"), 
                            prop_type.get("_field_node")
                        )
                    type_info["properties"] = processed_properties
            else:
                type_info = TYPE_MAP.get(node.id, {"type": "object"})
        
        elif isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                if node.value.id in ["List", "list"]:
                    item_type = self.extract_type_annotation(node.slice)
                    type_info = {
                        "type": "array",
                        "items": item_type
                    }
                elif node.value.id == "Optional":
                    type_info = self.extract_type_annotation(node.slice)
        
        elif isinstance(node, ast.Attribute):
            enum_name = node.attr
            if enum_name in self.type_definitions:
                type_info = self.type_definitions[enum_name].copy()
            else:
                print(f"Warning: Enum type '{enum_name}' not found in type definitions")
                type_info = {"type": "object"}
        else:
            type_info = {"type": "object"}

        # Store AST nodes for later processing
        type_info["_ast_node"] = node
        if field_node:
            type_info["_field_node"] = field_node
            description = self.extract_field_description(field_node)
            if description:
                type_info["description"] = description

        return type_info

    def extract_class_schema(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract complete schema for a class"""
        schema = {
            "type": "object",
            "properties": {}
        }
        
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                field_node = None
                if isinstance(item.value, ast.Call) and isinstance(item.value.func, ast.Name) and item.value.func.id == "Field":
                    field_node = item.value
                
                type_info = self.extract_type_annotation(item.annotation, field_node)
                schema["properties"][field_name] = type_info
        
        # Clean up AST nodes recursively before returning
        return self.clean_ast_nodes(schema)

def generate_manifest(location: str) -> Dict[str, Any]:
    logger.info(f"Starting manifest generation from {location}")
    try:
        # Load base manifest
        base_manifest_path = Path(__file__).parent.parent.parent / "base-manifest.json"
        if not base_manifest_path.exists():
            raise FileNotFoundError(f"Base manifest not found at {base_manifest_path}")
            
        with open(base_manifest_path) as f:
            manifest = json.load(f)

        path = Path(location)
        if not path.exists():
            raise FileNotFoundError(f"Location not found: {location}")

        builder = ManifestBuilder()
        python_files = list(path.rglob("*.py"))
        
        if not python_files:
            raise ValueError(f"No Python files found in {location}")
        
        logger.info(f"Found {len(python_files)} Python files to process")

        # First pass: collect all type definitions
        for py_file in python_files:
            _process_file(py_file, lambda tree: builder.collect_type_definitions(tree))

        # Second pass: process decorated classes
        for py_file in python_files:
            _process_file(py_file, lambda tree: builder.visit(tree))

        # Update manifest with schemas
        _update_manifest(manifest, builder)
        
        return manifest
    
    except Exception as e:
        raise ManifestGenerationError(f"Failed to generate manifest: {str(e)}") from e

def _process_file(file_path: Path, processor: callable):
    """Process a single Python file"""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
            processor(tree)
    except Exception as e:
        print(f"Warning: Could not process {file_path}: {e}")

def _update_manifest(manifest: Dict[str, Any], builder: ManifestBuilder):
    """Update manifest with builder schemas"""

    logger.info("Updating manifest with schemas")
    if builder.input_schema:
        manifest["spec"]["input"] = builder.input_schema
    if builder.output_schema:
        manifest["spec"]["output"] = builder.output_schema
    if builder.config_schema:
        manifest["spec"]["config"] = builder.config_schema


def main():
    import argparse
    parser = argparse.ArgumentParser()
    sys.stdout.flush()  # Force flush stdout
    parser.add_argument("location", help="Location of the Python files to scan")
    parser.add_argument("--output", "-o", default="manifest.json", help="Output file path")
    args = parser.parse_args()

    manifest = generate_manifest(args.location)
    
    with open(args.output, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest generated successfully at {args.output}")

if __name__ == "__main__":
    main()