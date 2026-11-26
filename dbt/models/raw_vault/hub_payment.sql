{{ config(materialized='incremental') }}

with payments as (

  select
    payment_hk,
    payment_bk,
    load_date,
    record_source

  from {{ ref('stg_payment') }}

),

final as (

  select *

  from payments

  {% if is_incremental() %}
  where payment_hk not in (
    select payment_hk from {{ this }}
  )
  {% endif %}

)

select * from final

