alter table biocent_farms.accola_ssurgo
add acres float8;
update biocent_farms.accola_ssurgo
set acres=shape_area * 0.000247105;