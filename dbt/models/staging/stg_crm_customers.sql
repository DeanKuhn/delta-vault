with raw as (

  select
    batch_id,
    _loaded_at as load_date,
    trim(crm_id) as crm_id,
    trim(account_number) as account_number,
    trim(customer_name) as customer_name,
    trim(city) as city,
    'CRM' as record_source
    
  from {{ source('raw', 'crm_customers') }}

  where batch_id = {{ var('batch_id') }}

),

hash_text as (

  select
    *,
    coalesce(
      nullif(upper(account_number), ''), concat(record_source, '||', upper(crm_id))
    ) as customer_bk,
    concat(
      coalesce(nullif(upper(customer_name), ''), '^^'), '||',
        coalesce(nullif(upper(city), ''), '^^')
    ) as hashdiff_text

  from raw

),

final as (

  select
    *,
    sha2(customer_bk, 256) as customer_hk,
    sha2(hashdiff_text, 256) as hashdiff

  from hash_text

)

select * from final
