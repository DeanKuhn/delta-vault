{{ config(materialized='incremental') }}

with crm as (

  select
    customer_hk,
    customer_bk,
    load_date,
    record_source

  from {{ ref('stg_crm_customers') }}

),

billing as (

  select
    customer_hk,
    customer_bk,
    load_date,
    record_source

  from {{ ref('stg_billing_customers') }}

),

combined as (

  select * from crm

  union all

  select * from billing

),

numbered as (

  select
    *,
    row_number() over (
      partition by customer_hk
      order by load_date, case when record_source = 'CRM' then 1 else 2 end
    ) as row_num

  from combined

),

tie_breaker as (

  select *

  from numbered

  where row_num = 1

),

final as (

  select
    customer_hk,
    customer_bk,
    load_date,
    record_source

  from tie_breaker

  {% if is_incremental() %}
  where customer_hk not in (
    select customer_hk from {{ this }}
  )
  {% endif %}

)

select * from final
