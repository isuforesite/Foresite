
here's another catch
in my data sets at least, the "mass" variable was reported as a flow variable, i.e., mass per seconds
mass per second*
so for example an observation with cycle = .5 and mass = 2 would have a total mass of .5 * 2 kilograms
what I ended up doing, which was a real pain in the ass all up to the neck, was to figure out the quantities I needed, i.e. mass at std mkt moisture and distance, then see if I could reconstruct the "yield bu/ac" column up to a small precision error
if that checked passed, I was more or less certain that my mass at std mkt moisture and distance were consistent with whatever a student would get by plugging the crappy files on arcGIS and plotting a map

calling ym file to create grid is different than in docs
Rscript bin/create-grid.R C:\\Users\\mjn\\Documents\\Dev\\ritas-deploy\\data\\cas_south_2016_maize.csv "Cas_South" "10," "+proj=utm +zone=15 +ellps=GRS80 +datum=NAD83 +units=m +no_defs" --output cas_test
Rscript bin/create-map.R C:\\Users\\mjn\\Documents\\Dev\\ritas-deploy\\data\\cas_south_2016_maize.csv Cas_South 2016 "10," 30 "+proj=utm +zone=15 +ellps=GRS80 +datum=NAD83 +units=m +no_defs" --nCores 6 --output cas_test


[11:45 AM] Damiano, Luis Antonio [STAT]
if you're doing kilograms, then MgHa = 10 * (massKg / areaM2)
 like 1

[11:45 AM] Damiano, Luis Antonio [STAT]
for a 10x10 grid reduces to simply massKg / 10, hence 145 -> 14.5

