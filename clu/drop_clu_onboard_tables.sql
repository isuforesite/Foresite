do $$
declare
	spec_table text := null;
begin
---

---
for spec_table in
	select
		table_name,
		upper( left( split_part( table_name, '_', 4 ), 2 ) ) as state,
		upper( split_part( table_name, '_', 4 ) ) as fips
	from information_schema.tables
	where
		table_name ~ 'clu_public_a_[a-z]{2}'
		and table_schema = 'clu_onboard'
		and table_type = 'BASE TABLE'
	order by
		table_name
	limit 500
loop
raise notice 'Dropping table clu_onboard.%', spec_table;
execute 'drop table clu_onboard.' || spec_table;

end loop;

---
end
$$
language plpgsql

