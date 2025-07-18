"""Monkey patches for FastMCP compatibility issues."""

from __future__ import annotations


def patch_fastmcp_parameter_parsing() -> None:
    """Patch FastMCP to handle enum parameter locations correctly.
    
    """
    try:
        import fastmcp.utilities.openapi as openapi_utils

        # Store original function
        original_convert = getattr(openapi_utils.OpenAPIParser, '_convert_to_parameter_location', None)

        def patched_convert_to_parameter_location(self, param_in):
            """Patched parameter location converter that handles enum values."""
            # Convert enum to string if needed
            if hasattr(param_in, 'value'):
                param_in = param_in.value
            elif hasattr(param_in, 'name'):
                param_in = param_in.name.lower()

            # Call original function with string value
            if original_convert:
                return original_convert(self, param_in)
            else:
                # Fallback implementation
                if param_in in ["path", "query", "header", "cookie"]:
                    return param_in
                return "query"

        # Apply the patch
        if hasattr(openapi_utils, 'OpenAPIParser'):
            openapi_utils.OpenAPIParser._convert_to_parameter_location = patched_convert_to_parameter_location

    except ImportError:
        # If we can't import the modules, the patch won't work but we'll continue
        pass


# Apply patches when module is imported
patch_fastmcp_parameter_parsing()
