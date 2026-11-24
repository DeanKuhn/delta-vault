{%- macro generate_schema_name(schema, node) -%}

{%- if schema is none or schema | trim == '' -%}
{{ exceptions.raise_compiler_error("No +schema set for " ~ node.name) }}

{%- else -%}
{{ schema | trim }}

{%- endif -%}

{%- endmacro -%}
