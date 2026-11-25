{{ config(materialized='incremental') }}

with incoming as (

  select
    customer_hk,
    hashdiff,
    load_date,
    record_source,
    customer_name,
    city

  from {{ ref('stg_crm_customers') }}

),

{% if is_incremental() %}

latest as (

  select *

  from {{ this }}

  qualify row_number() over (
    partition by customer_hk order by load_date desc
  ) = 1

),

{% endif %}

final as (

  select
    incoming.*

  from incoming

  {% if is_incremental() %}
  left join latest on latest.customer_hk = incoming.customer_hk
  where latest.customer_hk is null
  or (
    incoming.load_date > latest.load_date
    and incoming.hashdiff <> latest.hashdiff
  )
  {% endif %}

)

select * from final
