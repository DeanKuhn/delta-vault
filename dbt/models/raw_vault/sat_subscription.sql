{{ config(materialized='incremental') }}

with incoming as (

  select
    subscription_hk,
    subscription_hashdiff,
    load_date,
    plan,
    record_source

  from {{ ref('stg_billing_customers') }}

),

{% if is_incremental() %}

latest as (

  select *

  from {{ this }}

  qualify row_number() over (
    partition by subscription_hk order by load_date desc
  ) = 1

),

{% endif %}

final as (

  select incoming.*

  from incoming

  {% if is_incremental() %}
  left join latest on latest.subscription_hk = incoming.subscription_hk
  where latest.subscription_hk is null
    or (
      incoming.load_date > latest.load_date
      and incoming.subscription_hashdiff <> latest.subscription_hashdiff
    )
  {% endif %}

)

select * from final
