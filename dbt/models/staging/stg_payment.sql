with raw as (

  select
    batch_id,
    _loaded_at as load_date,
    trim(payment_id) as payment_id,
    trim(billing_id) as billing_id,
    trim(amount) as amount,
    'PAYMENT' as record_source
    
  from {{ source('raw', 'payments' }}

  where batch_id = {{ var('batch_id') }}

),

hash_text as (

  select
    *,
    upper(payment_id) as payment_bk,
    upper(billing_id) as subscription_bk,
    coalesce(nullif(upper(amount), ''), '^^') as hashdiff_text

  from raw

),

link_hash as (

  select
    *,
    concat(payment_bk, '||', subscription_bk) as link_hash_text

  from hash_text

),

final as (

  select
    *,
    sha2(payment_bk, 256) as payment_hk,
    sha2(hashdiff_text, 256) as hashdiff,
    sha2(link_hash_text, 256) as link_payment_subscription_hk,
    sha2(subscription_bk, 256) as subscription_hk

  from link_hash

)

select * from final
