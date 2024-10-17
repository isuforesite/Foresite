"""
Created as part of ISU C-CHANGE Foresite system on 13 Jan 2020

@author: Matt Nowatzke
@email: mnowatz@iastate.edu
"""

import pandas as pd


def get_prod_costs(dbconn, schema, table, year):
    pass


class Budget:
    """
    Calculates profitability for rotation, management, and acres.
    """

    # Get basic field info
    def __init__(self, rotation, current_crop, buac, acres=1, year=2019):
        self.rotation = rotation
        self.current_crop = current_crop
        self.buac = buac
        self.acres = acres
        self.expenses = {
            "fert": 0,
            "seed": 0,
            "preharv_mach": 0,
            "harv_mach": 0,
            "processing": 0,
            "chemicals": 0,
            "extra": 0,
            "labor": 0,
        }
        self.year = year

    def fert_cost(
        self,
        n_lbs=0,
        n_price=0,
        phos_lbs=0,
        phos_price=0,
        potash_lbs=0,
        potash_price=0,
    ):
        """Calculates cost of fertilizer per acre
        Arguments:
            n_lbs {float} -- pounds of nitrogen applied per acre
            phos_lbs {float} -- pounds of phosphorous applied per acre
            potash_lbs {float} -- pounds of potash/potassium applied per acre
            n_price {float} -- price of nitrogen per pound
            phos_price {float} -- price of phosphorous per pound
            potash_price {float} -- price of potash/potassium per pound
            acres {float} -- number of acres in field or area
        Returns:
            float -- total price of fertilizer per acre
        """
        n_cost = (n_lbs * n_price) * self.acres
        phos_cost = (phos_lbs * phos_price) * self.acres
        potash_cost = (potash_lbs * potash_price) * self.acres
        self.total_fert_cost = n_cost + phos_cost + potash_cost
        self.expenses["fert"] = self.total_fert_cost
        return self.total_fert_cost

    def seed_cost(self, seed_rate, seed_price):
        """Calculates cost of seed for one acre
        Arguments:
            seed_rate {int} -- number of seeds planted per acre
            seed_price {float} -- cost per 1000 seeds
            acres {float} -- number of acres in field or area
        Returns:
            float -- cost of seed per acre
        """
        if self.current_crop == "corn":
            self.seed_cost_acre = ((seed_rate / 1000) * seed_price) * self.acres
        elif self.current_crop == "soybean":
            self.seed_cost_acre = ((seed_rate / 140000) * seed_price) * self.acres
        self.expenses["seed"] = self.seed_cost_acre
        return self.seed_cost_acre

    def preharvest_machinery_cost(
        self,
        fix_chisel=0,
        var_chisel=0,
        fix_disk=0,
        var_disk=0,
        fix_applicator=0,
        var_applicator=0,
        fix_cultivator=0,
        var_cultivator=0,
        fix_planter=0,
        var_planter=0,
        fix_sprayer=0,
        var_sprayer=0,
    ):
        """Calculates per acre cost of preharvest machinery
        Arguments:
            var_chisel {float} -- variable chisel cost
            fix_chisel {float} -- fixed chisel cost
            var_disk {float} -- variable disk cost
            fix_disk {float} -- fixed disk cost
            var_applicator {float} -- variable fertilizer application cost
            fix_applicator {float} -- fixed fertilizer application cost
            var_cultivator {float} -- variable field cultivator cost
            fix_cultivator {float} -- fixed field cultivator cost
            fix_planter {float} -- fixed planter cost
            var_planter {float} -- variable planter cost
            var_sprayer {float} -- variable sprayer cost
            fix_sprayer {float} -- fixed sprayer cost
            acres {float} -- number of acres in field or area
        Returns:
            float -- cost of preharvest machinery per acre
        """
        tillage_cost = (var_chisel + fix_chisel + var_disk + fix_disk) * self.acres
        applicator_cost = (var_applicator + fix_applicator) * self.acres
        cultivator_cost = (var_cultivator + fix_cultivator) * self.acres
        planter_cost = (var_planter + fix_planter) * self.acres
        sprayer_cost = (var_sprayer + fix_planter) * self.acres
        self.total_preharvest = tillage_cost + applicator_cost + cultivator_cost + planter_cost + sprayer_cost
        self.expenses["preharv_mach"] = self.total_preharvest
        return self.total_preharvest

    def harvest_machinery_cost(self, fix_combine, var_combine, fix_wagon, var_wagon):
        """Calculates per acre cost of harvest machinery
        Arguments:
            fix_combine {float} -- fixed cost of combine/harvester
            var_combine {float} -- variable cost of combine/harvester
            fix_wagon {float} -- fixed cost of wagon/grain cart
            var_wagon {float} -- variable cost of wagon/grain cart
            acres {float} -- number of acres in field or area
        Returns:
            float -- total cost per acre of harvest machinery
        """
        combine_cost = (fix_combine + var_combine) * self.acres
        wagon_cost = (fix_wagon + var_wagon) * self.acres
        self.total_harvest_machinery = combine_cost + wagon_cost
        self.expenses["harv_mach"] = self.total_harvest_machinery
        return self.total_harvest_machinery

    def processing_cost(
        self,
        fix_hauling,
        var_hauling,
        fix_drying,
        var_drying,
        fix_handling,
        var_handling,
    ):
        """Calculate cost per bushel of processing
        Arguments:
            buac {float} -- bushels of grain per acre
            fix_hauling {float} -- fixed cost of hauling
            var_hauling {float} -- variable cost of hauling
            fix_drying {float} -- fixed cost of drying
            var_drying {float} -- variable cost drying
            fix_handling {float} -- fixed cost of handling
            var_handling {float} -- variable cost of handling
            acres {float} -- number of acres in field or area
        Returns:
            float -- total cost of processing per acre
        """
        hauling_cost = ((var_hauling + fix_hauling) * self.buac) * self.acres
        drying_cost = ((var_drying + fix_drying) * self.buac) * self.acres
        handling_cost = ((var_hauling + fix_hauling) * self.buac) * self.acres
        self.total_processing = hauling_cost + drying_cost + handling_cost
        self.expenses["processing"] = self.total_processing
        return self.total_processing

    def chemicals_cost(self, herbicide, insecticide=0):
        """Calculate cost of herbicides and pesticides per acre
        Arguments:
            herbicide {float} -- cost per acre of herbicide
            insecticide {float} -- cost per acre of insecticide
            acres {float} -- number of acres in field or area
        Returns:
            float -- cost of herbicide and pesticide per acre
        """
        herb_cost = herbicide
        insect_cost = insecticide
        self.total_chemical = (herb_cost + insect_cost) * self.acres
        self.expenses["chemicals"] = self.total_chemical
        return self.total_chemical

    def extra_costs(self, misc, crop_insurance=0, rent_cost=0, rent=False):
        """calculate cost of extra costs like rent and insurance per acre
        Arguments:
            misc {float} -- miscellaneous costs per acre
            rent {float} -- cost of rent per acre
            crop_insurance {float} -- cost of insurance per acre
            acres {float} -- number of acres to analyze
        Returns:
            float -- total extra costs per acre
        """
        if rent == True:
            self.extra_rent_cost = (rent_cost + crop_insurance + misc) * self.acres
            self.expenses["extra"] = self.extra_rent_cost
            return self.extra_rent_cost
        else:
            self.extra_own_cost = (crop_insurance + misc) * self.acres
            self.expenses["extra"] = self.extra_own_cost
            return self.extra_own_cost

    def labor_cost(self, labor_hours=0, rate_of_pay=0):
        """Calculates cost of labor
        Arguments:
            labor_hours {float} -- number of hours of hired labor
            rate_of_pay {float} -- hourly rate of pay in dollars
            acres {float} -- number of acres labor was hired for
        Returns:
            float -- total cost of labor per acre
        """
        self.total_labor = (labor_hours * rate_of_pay) * self.acres
        self.expenses["labor"] = self.total_labor
        return self.total_labor

    def calc_revenue(self, comm_price):
        """calculates total revenue from yield and commodity price
        Arguments:
            comm_price {float} -- current price of given commodity
            buac {float} -- yield in bushels per acre
            acres {float} -- number of acres in given field or area
        Returns:
            float -- total revenue from given field or area
        """
        calc = (self.buac * self.acres) * comm_price
        self.revenue = round(calc, 2)
        return self.revenue

    def sum_expenses(self):
        """
        Sum all values in expenses list for total expenses and return total expenses.
        """
        self.expense_total = sum(self.expenses.values())
        return self.expense_total

    def calc_profit(self):
        """
        Returns profit: revenue from grain - total expenses
        """
        self.profit = self.revenue - self.expense_total
        return self.profit


def calc_subfield_profit(
    clukey_list,
    county_df,
    year,
    cfs_mgmt,
    sfc_mgmt,
    cc_mgmt,
    rent=False,
    labor=0,
    labor_payrate=0,
):
    df_rows = []
    total_clukeys = len(clukey_list)
    mukey_counter = 0
    clukey_counter = 0
    # get commodity prices
    comm_price_df = pd.read_sql(f"SELECT * from public.hist_comm_prices WHERE year = '{year}';", dbconn)
    corn_price = float(comm_price_df.loc[comm_price_df["commodity"] == "corn", "mrkt_avg"].iloc[0])
    soy_price = float(comm_price_df.loc[comm_price_df["commodity"] == "soybean", "mrkt_avg"].iloc[0])
    # get input costs
    costs = pd.read_sql(f"SELECT * FROM public.crop_prod_costs WHERE year = '{year}'", dbconn)
    corn_seed_price = float(costs.loc[costs["input"] == "corn_seed", "fixed-cost"].iloc[0])
    soy_seed_price = float(costs.loc[costs["input"] == "soy_seed", "fixed-cost"].iloc[0])
    n_price = float(costs.loc[costs["input"] == "nitrogen", "fixed-cost"].iloc[0])
    phos_price = float(costs.loc[costs["input"] == "phosphorous", "fixed-cost"].iloc[0])
    potash_price = float(costs.loc[costs["input"] == "phosphorous", "fixed-cost"].iloc[0])
    fix_chisel = float(costs.loc[costs["input"] == "chisel_plow", "fixed-cost"].iloc[0])
    var_chisel = float(costs.loc[costs["input"] == "chisel_plow", "variable-cost"].iloc[0])
    fix_disk = float(costs.loc[costs["input"] == "disk_field_cultivator", "fixed-cost"].iloc[0])
    var_disk = float(costs.loc[costs["input"] == "disk_field_cultivator", "variable-cost"].iloc[0])
    fix_applicator = float(costs.loc[costs["input"] == "nh3_applicator", "fixed-cost"].iloc[0])
    var_applicator = float(costs.loc[costs["input"] == "nh3_applicator", "variable-cost"].iloc[0])
    fix_cultivator = float(costs.loc[costs["input"] == "field_cultivator", "fixed-cost"].iloc[0])
    var_cultivator = float(costs.loc[costs["input"] == "field_cultivator", "variable-cost"].iloc[0])
    fix_planter = float(costs.loc[costs["input"] == "planter", "fixed-cost"].iloc[0])
    var_planter = float(costs.loc[costs["input"] == "planter", "variable-cost"].iloc[0])
    fix_sprayer = float(costs.loc[costs["input"] == "sprayer", "fixed-cost"].iloc[0])
    var_sprayer = float(costs.loc[costs["input"] == "sprayer", "variable-cost"].iloc[0])
    fix_corn_combine = float(costs.loc[costs["input"] == "combine_corn", "fixed-cost"].iloc[0])
    var_corn_combine = float(costs.loc[costs["input"] == "combine_corn", "variable-cost"].iloc[0])
    fix_soy_combine = float(costs.loc[costs["input"] == "combine_soybeans", "fixed-cost"].iloc[0])
    var_soy_combine = float(costs.loc[costs["input"] == "combine_soybeans", "variable-cost"].iloc[0])
    fix_wagon = float(costs.loc[costs["input"] == "grain_cart", "fixed-cost"].iloc[0])
    var_wagon = float(costs.loc[costs["input"] == "grain_cart", "variable-cost"].iloc[0])
    fix_hauling = float(costs.loc[costs["input"] == "haul_grain", "fixed-cost"].iloc[0])
    var_hauling = float(costs.loc[costs["input"] == "haul_grain", "variable-cost"].iloc[0])
    fix_drying = float(costs.loc[costs["input"] == "dry_grain", "fixed-cost"].iloc[0])
    var_drying = float(costs.loc[costs["input"] == "dry_grain", "variable-cost"].iloc[0])
    fix_handle = float(costs.loc[costs["input"] == "auger_store_grain", "fixed-cost"].iloc[0])
    var_handle = float(costs.loc[costs["input"] == "auger_store_grain", "variable-cost"].iloc[0])
    soy_herb_cost = float(
        costs.loc[
            (costs["crop"] == "soy") & (costs["input"] == "herbicide"),
            "fixed-cost",
        ].iloc[0]
    )
    corn_herb_cost = float(
        costs.loc[
            (costs["crop"] == "corn") & (costs["input"] == "herbicide"),
            "fixed-cost",
        ].iloc[0]
    )
    insect_cost = float(costs.loc[costs["input"] == "insecticide", "fixed-cost"].iloc[0])
    corn_crop_insurance = float(
        costs.loc[
            (costs["crop"] == "corn") & (costs["input"] == "crop_insurance"),
            "variable-cost",
        ].iloc[0]
    )
    soy_crop_insurance = float(
        costs.loc[
            (costs["crop"] == "soy") & (costs["input"] == "crop_insurance"),
            "variable-cost",
        ].iloc[0]
    )
    rent_cost = float(costs.loc[costs["input"] == "rent", "fixed-cost"].iloc[0])
    misc_cost = float(costs.loc[costs["input"] == "miscellaneous", "variable-cost"].iloc[0])
    for i in clukey_list:
        try:
            print(f"Getting data for clukey {i}")
            clukey_counter += 1
            rot_df = pd.read_sql(
                f"SELECT * FROM raccoon.raccoon_rots WHERE clukey = {i};",
                dbconn,
            )
            clukey_df = county_df.loc[county_df["clukey"] == i].reset_index(drop=True)
            rotation = get_rotation(rot_df, "crop")
            for i in clukey_df.index:
                try:
                    state = clukey_df.loc[i, "state"]
                    fips = clukey_df.loc[i, "fips"]
                    huc8 = clukey_df.loc[i, "huc8"]
                    county = clukey_df.loc[i, "county"]
                    geom = clukey_df.loc[i, "wkb_geometry"]
                    mukey = clukey_df.loc[i, "mukey"]
                    musym = clukey_df.loc[i, "musym"]
                    try:
                        mukey_summary = pd.read_sql(
                            f"SELECT * FROM raccoon.apsim_output_summary WHERE county = '{county}' AND mukey = {mukey} AND rotation = '{rotation}';",
                            dbconn,
                        )
                        if mukey_summary.empty:
                            continue
                    except Exception:
                        traceback.print_exc()
                        continue
                    acreage = float(clukey_df.loc[i, "acres"])
                    no3_loss = float((mukey_summary.iloc[0]["leach_no3"] / 2.471) * acreage)
                    clukey = clukey_df.loc[i, "clukey"]
                    if rotation == "cc":
                        current_crop = "corn"
                        buac = float(mukey_summary.iloc[0]["corn_buac"])
                        n_lbs = float(mukey_summary.iloc[0]["fertiliser"]) * 0.892
                        # calculate how much phos and potash to add based on yield
                        phos_lbs = buac * 0.37
                        potash_lbs = buac * 0.37
                        # plant density is in m2 in apsim -- 10000 sq meters in hectare, 2.47 acres in hectare -- seeding rate = plant density * 10000 / 2.47
                        sowing_density = (int(cc_mgmt["sowing_density"]) * 10000) / 2.47
                        cc_budget = Budget(rotation, current_crop, buac, acreage, year)
                        fert_cost = cc_budget.fert_cost(
                            n_lbs,
                            n_price,
                            phos_lbs,
                            phos_price,
                            potash_lbs,
                            potash_price,
                        )
                        seed_cost = cc_budget.seed_cost(sowing_density, corn_seed_price)
                        preharvest_machinery_cost = cc_budget.preharvest_machinery_cost(
                            fix_chisel=fix_chisel,
                            var_chisel=var_chisel,
                            fix_disk=fix_disk,
                            var_disk=var_disk,
                            fix_applicator=fix_applicator,
                            var_applicator=var_applicator,
                            fix_planter=fix_planter,
                            var_planter=var_planter,
                            fix_sprayer=fix_sprayer,
                            var_sprayer=var_sprayer,
                        )
                        harvest_machinery_cost = cc_budget.harvest_machinery_cost(
                            fix_corn_combine,
                            var_corn_combine,
                            fix_wagon,
                            var_wagon,
                        )
                        processing_cost = cc_budget.processing_cost(
                            fix_hauling,
                            var_hauling,
                            fix_drying,
                            var_drying,
                            fix_handle,
                            var_handle,
                        )
                        chemicals_cost = cc_budget.chemicals_cost(corn_herb_cost, insect_cost)
                        extra_costs = cc_budget.extra_costs(misc_cost, corn_crop_insurance)
                        labor_cost = cc_budget.labor_cost()
                        revenue = cc_budget.calc_revenue(corn_price)
                        expenses = cc_budget.sum_expenses()
                        profit = cc_budget.calc_profit()
                        df_rows.append(
                            (
                                state,
                                huc8,
                                fips,
                                county,
                                clukey,
                                mukey,
                                musym,
                                acreage,
                                rotation,
                                current_crop,
                                buac,
                                no3_loss,
                                n_lbs,
                                phos_lbs,
                                potash_lbs,
                                sowing_density,
                                fert_cost,
                                seed_cost,
                                preharvest_machinery_cost,
                                harvest_machinery_cost,
                                processing_cost,
                                chemicals_cost,
                                extra_costs,
                                labor_cost,
                                revenue,
                                expenses,
                                profit,
                                geom,
                            )
                        )
                    elif rotation == "cfs":
                        current_crop = "corn"
                        buac = float(mukey_summary.iloc[0]["corn_buac"])
                        n_lbs = float(mukey_summary.iloc[0]["fertiliser"]) * 0.892
                        # calculate how much phos and potash to add based on yield
                        phos_lbs = buac * 0.375
                        potash_lbs = buac * 0.3
                        sowing_density = (int(cfs_mgmt["sowing_density"]) * 10000) / 2.47
                        cfs_budget = Budget(rotation, current_crop, buac, acreage, year)
                        fert_cost = cfs_budget.fert_cost(
                            n_lbs,
                            n_price,
                            phos_lbs,
                            phos_price,
                            potash_lbs,
                            potash_price,
                        )
                        seed_cost = cfs_budget.seed_cost(sowing_density, corn_seed_price)
                        preharvest_machinery_cost = cfs_budget.preharvest_machinery_cost(
                            fix_chisel=fix_chisel,
                            var_chisel=var_chisel,
                            fix_disk=fix_disk,
                            var_disk=var_disk,
                            fix_applicator=fix_applicator,
                            var_applicator=var_applicator,
                            fix_planter=fix_planter,
                            var_planter=var_planter,
                            fix_sprayer=fix_sprayer,
                            var_sprayer=var_sprayer,
                        )
                        harvest_machinery_cost = cfs_budget.harvest_machinery_cost(
                            fix_corn_combine,
                            var_corn_combine,
                            fix_wagon,
                            var_wagon,
                        )
                        processing_cost = cfs_budget.processing_cost(
                            fix_hauling,
                            var_hauling,
                            fix_drying,
                            var_drying,
                            fix_handle,
                            var_handle,
                        )
                        chemicals_cost = cfs_budget.chemicals_cost(corn_herb_cost)
                        extra_costs = cfs_budget.extra_costs(misc_cost, corn_crop_insurance)
                        labor_cost = cfs_budget.labor_cost()
                        revenue = cfs_budget.calc_revenue(corn_price)
                        expenses = cfs_budget.sum_expenses()
                        profit = cfs_budget.calc_profit()
                        df_rows.append(
                            (
                                state,
                                huc8,
                                fips,
                                county,
                                clukey,
                                mukey,
                                musym,
                                acreage,
                                rotation,
                                current_crop,
                                buac,
                                no3_loss,
                                n_lbs,
                                phos_lbs,
                                potash_lbs,
                                sowing_density,
                                fert_cost,
                                seed_cost,
                                preharvest_machinery_cost,
                                harvest_machinery_cost,
                                processing_cost,
                                chemicals_cost,
                                extra_costs,
                                labor_cost,
                                revenue,
                                expenses,
                                profit,
                                geom,
                            )
                        )
                    elif rotation == "sfc":
                        current_crop = "soybean"
                        buac = float(mukey_summary.iloc[0]["soy_buac"])
                        # calculate how much phos and potash to add based on yield
                        phos_lbs = buac * 0.8
                        potash_lbs = buac * 1.51
                        n_lbs = 0
                        sowing_density = (int(sfc_mgmt["sowing_density"]) * 10000) / 2.47
                        spray_fix = fix_sprayer * 2
                        spray_var = var_sprayer * 2
                        sfc_budget = Budget(rotation, current_crop, buac, acreage, year)
                        fert_cost = sfc_budget.fert_cost(
                            n_lbs,
                            n_price,
                            phos_lbs,
                            phos_price,
                            potash_lbs,
                            potash_price,
                        )
                        seed_cost = sfc_budget.seed_cost(sowing_density, soy_seed_price)
                        preharvest_machinery_cost = sfc_budget.preharvest_machinery_cost(
                            fix_chisel=fix_chisel,
                            var_chisel=var_chisel,
                            fix_disk=fix_disk,
                            var_disk=var_disk,
                            fix_applicator=fix_applicator,
                            var_applicator=var_applicator,
                            fix_planter=fix_planter,
                            var_planter=var_planter,
                            fix_sprayer=spray_fix,
                            var_sprayer=spray_var,
                        )
                        harvest_machinery_cost = sfc_budget.harvest_machinery_cost(
                            fix_soy_combine,
                            var_soy_combine,
                            fix_wagon,
                            var_wagon,
                        )
                        processing_cost = sfc_budget.processing_cost(
                            fix_hauling,
                            var_hauling,
                            fix_drying,
                            var_drying,
                            fix_handle,
                            var_handle,
                        )
                        chemicals_cost = sfc_budget.chemicals_cost(soy_herb_cost)
                        extra_costs = sfc_budget.extra_costs(misc_cost, soy_crop_insurance)
                        labor_cost = sfc_budget.labor_cost()
                        revenue = sfc_budget.calc_revenue(soy_price)
                        expenses = sfc_budget.sum_expenses()
                        profit = sfc_budget.calc_profit()
                        df_rows.append(
                            (
                                state,
                                huc8,
                                fips,
                                county,
                                clukey,
                                mukey,
                                musym,
                                acreage,
                                rotation,
                                current_crop,
                                buac,
                                no3_loss,
                                n_lbs,
                                phos_lbs,
                                potash_lbs,
                                sowing_density,
                                fert_cost,
                                seed_cost,
                                preharvest_machinery_cost,
                                harvest_machinery_cost,
                                processing_cost,
                                chemicals_cost,
                                extra_costs,
                                labor_cost,
                                revenue,
                                expenses,
                                profit,
                                geom,
                            )
                        )
                    else:
                        print("Not a corn or soybean rotation.")
                        continue
                    mukey_counter += 1
                    if mukey_counter % 50 == 0:
                        print(f"Finished with {mukey_counter} mukeys")
                    if clukey_counter == total_clukeys:
                        print("All done")
                except Exception:
                    traceback.print_exc()
                    print(f"failed on mukey {mukey}")
                    mukey_counter += 1
                    if mukey_counter % 50 == 0:
                        print(f"Finished with {mukey_counter} mukeys")
                    if clukey_counter == total_clukeys:
                        print("All done")
                    continue
        except Exception:
            traceback.print_exc()
            continue
    return gpd.GeoDataFrame(
        df_rows,
        # return pd.DataFrame(df_rows,
        columns=(
            "state",
            "huc8",
            "fips",
            "county",
            "clukey",
            "mukey",
            "musym",
            "acreage",
            "rotation",
            "crop",
            "buac",
            "no3_loss",
            "n_lbs",
            "phos_lbs",
            "potash_lbs",
            "sowing_density",
            "fert_cost",
            "seed_cost",
            "preharv_machinery",
            "harv_machinery",
            "processing",
            "chemicals",
            "extra_costs",
            "labor_cost",
            "revenue",
            "expenses",
            "profit",
            "wkb_geometry",
        ),
        geometry="wkb_geometry",
    )


# %%
if __name__ == "__main__":
    pass
