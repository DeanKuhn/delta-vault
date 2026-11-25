{{ config(materialized='incremental') }}

with subs as (

  select
    subscription_hk,
    subscription_bk,
    load_date,
    record_source

  from {{ ref('stg_billing_customers') }}

),

final as (

  select *

  from subs

  {% if is_incremental() %}
  where subscription_hk not in (
    select subscription_hk from {{ this }}
  )
  {% endif %}

)

select * from final
