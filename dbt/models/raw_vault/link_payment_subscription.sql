{{ config(materialized='incremental') }}

with link as (

  select
    link_payment_subscription_hk,
    payment_hk,
    subscription_hk,
    load_date,
    record_source

  from {{ ref('stg_payment') }}

),

final as (

  select *

  from link

  {% if is_incremental() %}
  where link_payment_subscription_hk not in (
    select link_payment_subscription_hk from {{ this }}
  )
  {% endif %}

)

select * from final
