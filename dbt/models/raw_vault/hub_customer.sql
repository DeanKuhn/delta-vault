{{ config(materialized='incremental') }}

with incoming as (

  select
    customer_hk,
    customer_bk,
    load_date,
    record_source

  from {{ ref('stg_crm_customers') }}

),

final as (

  select *

  from incoming

  {% if is_incremental() %}
  where customer_hk not in (
    select customer_hk from {{ this }}
  )
  {% endif %}

)

select * from final
