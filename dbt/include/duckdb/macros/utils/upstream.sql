{%- macro register_upstream_external_models() -%}
{% if execute %}
{% set upstream_nodes = {} %}
{% set upstream_schemas = {} %}
{% for node in selected_resources %}
  {% for upstream_node in graph['nodes'][node]['depends_on']['nodes'] %}
    {% if upstream_node not in upstream_nodes and upstream_node not in selected_resources %}
      {% do upstream_nodes.update({upstream_node: None}) %}
      {% set upstream = graph['nodes'].get(upstream_node) %}
      {% if upstream
         and upstream.resource_type in ('model', 'seed')
         and upstream.config.materialized=='external'
      %}
        {%- set upstream_rel = api.Relation.create(
          database=upstream['database'],
          schema=upstream['schema'],
          identifier=upstream['alias']
        ) -%}
        {%- set format = render(upstream.config.get('format', 'parquet')) -%}
        {%- set upstream_location = render(
            upstream.config.get('location', external_location(upstream_rel, format)))
        -%}
        {% if upstream_rel.schema not in upstream_schemas %}
          {% call statement('main', language='sql') -%}
            create schema if not exists {{ upstream_rel.schema }}
          {%- endcall %}
          {% do upstream_schemas.update({upstream_rel.schema: None}) %}
        {% endif %}
        {% call statement('main', language='sql') -%}
          create or replace view {{ upstream_rel.include(database=False) }} as (
            select * from '{{ upstream_location }}'
          );
        {%- endcall %}
      {%- endif %}
    {% endif %}
  {% endfor %}
{% endfor %}
{% endif %}
{%- endmacro -%}