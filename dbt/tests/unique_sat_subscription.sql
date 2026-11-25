select
  subscription_hk,
  load_date,
  count(*) as row_count

from {{ ref('sat_subscription') }}

group by subscription_hk, load_date

having count(*) > 1
