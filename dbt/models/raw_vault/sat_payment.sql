{{ config(materialized='incremental') }}

with incoming as (

  select
    payment_hk,
    payment_hashdiff,
    load_date,
    amount,
    record_source

  from {{ ref('stg_payment') }}

),

{% if is_incremental() %}

latest as (

  select *

  from {{ this }}

  qualify row_number() over (
    partition by payment_hk order by load_date desc
  ) = 1

),

{% endif %}

final as (

  select incoming.*

  from incoming

  {% if is_incremental() %}
  left join latest on latest.payment_hk = incoming.payment_hk
  where latest.payment_hk is null
    or (
      incoming.load_date > latest.load_date
      and incoming.payment_hashdiff <> latest.payment_hashdiff
    )
  {% endif %}

)

select * from final
