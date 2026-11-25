with raw as (

  select
    batch_id,
    _loaded_at as load_date,
    trim(billing_id) as billing_id,
    trim(account_number) as account_number,
    trim(customer_name) as customer_name,
    trim(city) as city,
    upper(trim(plan)) as plan,
    'BILLING' as record_source
    
  from {{ source('raw', 'billing_customers') }}

  where batch_id = {{ var('batch_id') }}

),

hash_text as (

  select
    *,
    coalesce(
      nullif(upper(account_number), ''), concat(record_source, '||', upper(billing_id))
    ) as customer_bk,
    upper(billing_id) as subscription_bk,
    concat(
      coalesce(nullif(upper(customer_name), ''), '^^'), '||',
        coalesce(nullif(upper(city), ''), '^^')
    ) as hashdiff_text,
    coalesce(nullif(plan, ''), '^^') as subscription_hashdiff_text

  from raw

),

final as (

  select
    *,
    sha2(customer_bk, 256) as customer_hk,
    sha2(hashdiff_text, 256) as hashdiff,
    sha2(subscription_bk, 256) as subscription_hk,
    sha2(subscription_hashdiff_text, 256) as subscription_hashdiff

  from hash_text

)

select * from final
