select
  customer_hk,
  load_date,
  count(*) as row_count

from {{ ref('sat_customer_crm') }}

group by customer_hk, load_date

having count(*) > 1
