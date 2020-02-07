drop table if exists vanloocke.raccoon_rots;
create table vanloocke.raccoon_rots as
select
	t1.clukey,
	case
		when t2.crop = 1 then 'Corn'
		when t2.crop = 5 then 'Soybean'
		when t2.crop = 176 then 'Pasture'
	end::text as crop,
	t2.years,
	t1.wkb_geometry
from vanloocke.raccoon_clu t1
inner join clu.clu_cdl t2
on t2.clukey = t1.clukey
where
	t2.crop in ( 1, 5, 176 );
