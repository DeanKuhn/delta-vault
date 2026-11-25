{{ config(materialized='incremental') }}

with incoming as (

  select
    sal_customer_hk,
    fallback_customer_hk,
    customer_hk,
    load_date,
    record_source

  from {{ ref('stg_billing_customers') }}

),

mapped as (

  select *

  from incoming

  where customer_hk <> fallback_customer_hk
    and fallback_customer_hk in (
      select customer_hk from {{ ref('hub_customer') }}
    )

),

final as (

  select *

  from mapped

  {% if is_incremental() %}
  where sal_customer_hk not in (
    select sal_customer_hk from {{ this }}
  )
  {% endif %}

)

select * from final
