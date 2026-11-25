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
    coalesce(nullif(plan, ''), '^^') as subscription_hashdiff_text,
    concat(record_source, '||', upper(billing_id)) as fallback_customer_bk

  from raw

),

link_hash as (

  select
    *,
    concat(customer_bk, '||', subscription_bk) as link_hash_text,
    concat(fallback_customer_bk, '||', customer_bk) as sal_hash_text

  from hash_text

),

final as (

  select
    *,
    sha2(customer_bk, 256) as customer_hk,
    sha2(hashdiff_text, 256) as hashdiff,
    sha2(link_hash_text, 256) as link_customer_subscription_hk,
    sha2(subscription_bk, 256) as subscription_hk,
    sha2(subscription_hashdiff_text, 256) as subscription_hashdiff,
    sha2(fallback_customer_bk, 256) as fallback_customer_hk,
    sha2(sal_hash_text, 256) as sal_customer_hk

  from link_hash

)

select * from final
