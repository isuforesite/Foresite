update raccoon.raccoon_clu_ssurgo_2018 t1
set county = t2.county
from public.us_county t2
where t1.fips = t2.fips