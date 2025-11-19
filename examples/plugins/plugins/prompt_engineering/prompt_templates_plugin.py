"""
Prompt Templates Advanced Plugin
Create, manage, and version control sophisticated prompt templates
"""

from typing import Dict, Any, Optional, List
import re


class PromptTemplatesPlugin:
    """Plugin for advanced prompt template management"""

    name = "prompt_templates_advanced"
    version = "1.0.0"
    description = "Advanced prompt template system with versioning and composition"
    author = "Windows AI Team"

    def __init__(self):
        self.templates = {}
        self.template_versions = {}
        self.template_categories = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Prompt Templates plugin"""
        try:
            # Initialize default template categories
            self.template_categories = {
                "instruction": [],
                "conversation": [],
                "analysis": [],
                "generation": [],
                "extraction": [],
                "transformation": []
            }
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Prompt Templates plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Prompt Templates action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_template":
                return self._create_template(params)
            elif action == "render_template":
                return self._render_template(params)
            elif action == "compose_templates":
                return self._compose_templates(params)
            elif action == "version_template":
                return self._version_template(params)
            elif action == "validate_template":
                return self._validate_template(params)
            elif action == "list_templates":
                return self._list_templates(params)
            elif action == "clone_template":
                return self._clone_template(params)
            elif action == "create_variant":
                return self._create_variant(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new prompt template"""
        template_id = params.get("template_id", f"template_{len(self.templates)}")
        template_text = params.get("template", "")
        category = params.get("category", "general")
        description = params.get("description", "")
        variables = params.get("variables", [])
        metadata = params.get("metadata", {})

        # Extract variables from template if not provided
        if not variables:
            variables = self._extract_variables(template_text)

        template = {
            "id": template_id,
            "template": template_text,
            "category": category,
            "description": description,
            "variables": variables,
            "metadata": metadata,
            "version": 1,
            "created_at": "now",
            "updated_at": "now"
        }

        self.templates[template_id] = template

        # Add to category
        if category in self.template_categories:
            if template_id not in self.template_categories[category]:
                self.template_categories[category].append(template_id)
        else:
            self.template_categories[category] = [template_id]

        # Initialize version history
        self.template_versions[template_id] = [template.copy()]

        return {
            "success": True,
            "template": template,
            "template_id": template_id,
            "variables_found": len(variables)
        }

    def _extract_variables(self, template_text: str) -> List[str]:
        """Extract variable placeholders from template"""
        # Find {variable_name} patterns
        variables = re.findall(r'\{(\w+)\}', template_text)
        return list(set(variables))  # Remove duplicates

    def _render_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Render a template with provided variables"""
        template_id = params.get("template_id", "")
        variables = params.get("variables", {})
        version = params.get("version", None)  # None = latest

        if template_id not in self.templates:
            return {"success": False, "error": f"Template {template_id} not found"}

        # Get template (specific version or latest)
        if version is not None:
            if template_id in self.template_versions and version <= len(self.template_versions[template_id]):
                template = self.template_versions[template_id][version - 1]
            else:
                return {"success": False, "error": f"Version {version} not found"}
        else:
            template = self.templates[template_id]

        # Check for missing variables
        required_vars = template["variables"]
        missing_vars = [var for var in required_vars if var not in variables]

        if missing_vars:
            return {
                "success": False,
                "error": "Missing required variables",
                "missing_variables": missing_vars,
                "required_variables": required_vars
            }

        # Render template
        try:
            rendered = template["template"].format(**variables)
        except KeyError as e:
            return {"success": False, "error": f"Variable error: {str(e)}"}

        return {
            "success": True,
            "rendered_prompt": rendered,
            "template_id": template_id,
            "version": version or template["version"],
            "variables_used": list(variables.keys())
        }

    def _compose_templates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compose multiple templates together"""
        template_ids = params.get("template_ids", [])
        composition_strategy = params.get("strategy", "sequential")  # sequential, nested, conditional
        separator = params.get("separator", "\n\n")
        variables = params.get("variables", {})

        if not template_ids:
            return {"success": False, "error": "No templates provided"}

        # Validate all templates exist
        for tid in template_ids:
            if tid not in self.templates:
                return {"success": False, "error": f"Template {tid} not found"}

        templates = [self.templates[tid] for tid in template_ids]

        # Compose based on strategy
        if composition_strategy == "sequential":
            # Render each template and concatenate
            rendered_parts = []
            for template in templates:
                # Filter variables for this template
                template_vars = {k: v for k, v in variables.items() if k in template["variables"]}
                rendered = template["template"].format(**template_vars)
                rendered_parts.append(rendered)

            composed = separator.join(rendered_parts)

        elif composition_strategy == "nested":
            # Each template wraps the next
            composed = variables.get("content", "")
            for template in reversed(templates):
                template_vars = {**variables, "content": composed}
                template_vars = {k: v for k, v in template_vars.items() if k in template["variables"] or k == "content"}
                composed = template["template"].format(**template_vars)

        elif composition_strategy == "conditional":
            # Conditional composition based on variables
            composed_parts = []
            for template in templates:
                condition_met = template.get("metadata", {}).get("condition", True)
                if condition_met:
                    template_vars = {k: v for k, v in variables.items() if k in template["variables"]}
                    rendered = template["template"].format(**template_vars)
                    composed_parts.append(rendered)

            composed = separator.join(composed_parts)

        else:
            composed = ""

        return {
            "success": True,
            "composed_prompt": composed,
            "template_ids": template_ids,
            "strategy": composition_strategy,
            "num_templates": len(template_ids)
        }

    def _version_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new version of an existing template"""
        template_id = params.get("template_id", "")
        new_template_text = params.get("new_template", "")
        change_description = params.get("change_description", "")

        if template_id not in self.templates:
            return {"success": False, "error": f"Template {template_id} not found"}

        template = self.templates[template_id]

        # Create new version
        new_version = template["version"] + 1
        new_variables = self._extract_variables(new_template_text)

        updated_template = {
            **template,
            "template": new_template_text,
            "variables": new_variables,
            "version": new_version,
            "updated_at": "now",
            "change_description": change_description
        }

        # Update current template
        self.templates[template_id] = updated_template

        # Save to version history
        self.template_versions[template_id].append(updated_template.copy())

        return {
            "success": True,
            "template_id": template_id,
            "new_version": new_version,
            "previous_version": new_version - 1,
            "change_description": change_description,
            "total_versions": len(self.template_versions[template_id])
        }

    def _validate_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate template syntax and structure"""
        template_id = params.get("template_id", "")
        template_text = params.get("template_text", None)

        # Get template text
        if template_id:
            if template_id not in self.templates:
                return {"success": False, "error": f"Template {template_id} not found"}
            template_text = self.templates[template_id]["template"]
        elif not template_text:
            return {"success": False, "error": "No template provided"}

        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "variables_found": []
        }

        # Check for balanced braces
        open_braces = template_text.count('{')
        close_braces = template_text.count('}')

        if open_braces != close_braces:
            validation_results["is_valid"] = False
            validation_results["errors"].append(f"Unbalanced braces: {open_braces} open, {close_braces} close")

        # Extract and validate variables
        try:
            variables = self._extract_variables(template_text)
            validation_results["variables_found"] = variables

            # Check for duplicate variables (informational)
            if len(variables) != len(set(variables)):
                validation_results["warnings"].append("Template uses same variable multiple times")

        except Exception as e:
            validation_results["is_valid"] = False
            validation_results["errors"].append(f"Variable extraction error: {str(e)}")

        # Check for empty template
        if not template_text.strip():
            validation_results["is_valid"] = False
            validation_results["errors"].append("Template is empty")

        # Check for common issues
        if '{{' in template_text or '}}' in template_text:
            validation_results["warnings"].append("Double braces detected - may cause issues")

        # Test rendering with dummy values
        if validation_results["is_valid"] and variables:
            try:
                dummy_values = {var: f"[{var}]" for var in variables}
                template_text.format(**dummy_values)
            except Exception as e:
                validation_results["is_valid"] = False
                validation_results["errors"].append(f"Rendering test failed: {str(e)}")

        return {
            "success": True,
            "validation": validation_results
        }

    def _list_templates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List templates by category or all"""
        category = params.get("category", None)
        include_versions = params.get("include_versions", False)

        if category:
            if category not in self.template_categories:
                return {"success": False, "error": f"Category {category} not found"}

            template_ids = self.template_categories[category]
            templates = [self.templates[tid] for tid in template_ids if tid in self.templates]
        else:
            templates = list(self.templates.values())

        # Optionally include version information
        if include_versions:
            templates_with_versions = []
            for template in templates:
                tid = template["id"]
                version_count = len(self.template_versions.get(tid, []))
                templates_with_versions.append({
                    **template,
                    "version_count": version_count
                })
            templates = templates_with_versions

        return {
            "success": True,
            "templates": templates,
            "num_templates": len(templates),
            "category": category,
            "total_categories": len(self.template_categories)
        }

    def _clone_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clone an existing template"""
        source_template_id = params.get("source_template_id", "")
        new_template_id = params.get("new_template_id", f"{source_template_id}_clone")

        if source_template_id not in self.templates:
            return {"success": False, "error": f"Source template {source_template_id} not found"}

        if new_template_id in self.templates:
            return {"success": False, "error": f"Template {new_template_id} already exists"}

        # Clone template
        source_template = self.templates[source_template_id]
        cloned_template = {
            **source_template,
            "id": new_template_id,
            "version": 1,
            "created_at": "now",
            "updated_at": "now",
            "metadata": {
                **source_template.get("metadata", {}),
                "cloned_from": source_template_id
            }
        }

        self.templates[new_template_id] = cloned_template

        # Add to category
        category = cloned_template["category"]
        if category in self.template_categories:
            self.template_categories[category].append(new_template_id)

        # Initialize version history
        self.template_versions[new_template_id] = [cloned_template.copy()]

        return {
            "success": True,
            "new_template_id": new_template_id,
            "source_template_id": source_template_id,
            "template": cloned_template
        }

    def _create_variant(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a template variant with modifications"""
        base_template_id = params.get("base_template_id", "")
        variant_id = params.get("variant_id", f"{base_template_id}_variant")
        modifications = params.get("modifications", {})

        if base_template_id not in self.templates:
            return {"success": False, "error": f"Base template {base_template_id} not found"}

        base_template = self.templates[base_template_id]

        # Apply modifications
        variant = base_template.copy()
        variant["id"] = variant_id
        variant["version"] = 1
        variant["created_at"] = "now"
        variant["updated_at"] = "now"

        # Apply specific modifications
        if "template" in modifications:
            variant["template"] = modifications["template"]
            variant["variables"] = self._extract_variables(variant["template"])

        if "description" in modifications:
            variant["description"] = modifications["description"]

        if "category" in modifications:
            variant["category"] = modifications["category"]

        variant["metadata"] = {
            **base_template.get("metadata", {}),
            "variant_of": base_template_id,
            "modifications": list(modifications.keys())
        }

        self.templates[variant_id] = variant

        # Add to category
        category = variant["category"]
        if category in self.template_categories:
            self.template_categories[category].append(variant_id)
        else:
            self.template_categories[category] = [variant_id]

        # Initialize version history
        self.template_versions[variant_id] = [variant.copy()]

        return {
            "success": True,
            "variant_id": variant_id,
            "base_template_id": base_template_id,
            "modifications_applied": list(modifications.keys()),
            "template": variant
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.templates = {}
        self.template_versions = {}
        self.template_categories = {}
        return True
