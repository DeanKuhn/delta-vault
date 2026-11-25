{{ config(materialized='incremental') }}

with link as (

  select
    link_customer_subscription_hk,
    customer_hk,
    subscription_hk,
    load_date,
    record_source

  from {{ ref('stg_billing_customers') }}

),

final as (

  select *

  from link

  {% if is_incremental() %}
  where link_customer_subscription_hk not in (
    select link_customer_subscription_hk from {{ this }}
  )
  {% endif %}

)

select * from final
