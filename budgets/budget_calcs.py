"""
Created as part of ISU C-CHANGE Foresite system on 13 Jan 2020

@author: Matt Nowatzke
@email: mnowatz@iastate.edu
"""
import pandas as pd
import database as db

def get_prod_costs(dbconn, schema, table, year):
    pass
class Budget:
    """
    Calculates profitability for rotation, management, and acres.
    """
    #Get basic field info
    def __init__(self, rotation, current_crop, buac, acres=1, year=2019):
        self.rotation = rotation
        self.current_crop = current_crop
        self.buac = buac
        self.acres = acres
        self.expenses = {'fert':0, 'seed':0, 'preharv_mach':0, 'harv_mach':0, 'processing':0, 'chemicals':0, 'extra':0, 'labor':0}
        self.year = year

    def fert_cost(self, n_lbs=0, n_price=0, phos_lbs=0, phos_price=0, potash_lbs=0, potash_price=0):
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
        self.expenses['fert']= self.total_fert_cost
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
        if self.current_crop == 'corn':
            self.seed_cost_acre = ((seed_rate/1000) * seed_price) * self.acres
        elif self.current_crop == 'soybean':
            self.seed_cost_acre = ((seed_rate/140000) * seed_price) * self.acres
        self.expenses['seed']= self.seed_cost_acre
        return self.seed_cost_acre

    def preharvest_machinery_cost(self, fix_chisel=0, var_chisel=0, fix_disk=0, var_disk=0, fix_applicator=0, var_applicator=0, fix_cultivator=0, var_cultivator=0, fix_planter=0, var_planter=0, fix_sprayer=0, var_sprayer=0):
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
        self.expenses['preharv_mach']= self.total_preharvest
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
        self.expenses['harv_mach'] = self.total_harvest_machinery
        return self.total_harvest_machinery

    def processing_cost(self, fix_hauling, var_hauling, fix_drying, var_drying, fix_handling, var_handling):
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
        self.expenses['processing'] = self.total_processing
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
        self.expenses['chemicals'] = self.total_chemical
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
            self.expenses['extra'] = self.extra_rent_cost
            return self.extra_rent_cost
        else:
            self.extra_own_cost = (crop_insurance + misc) * self.acres
            self.expenses['extra'] = self.extra_own_cost
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
        self.expenses['labor'] = self.total_labor
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

# #%%
# columns = [
#     'management_sample_id',
#     'fertilizer',
#     'seed',
#     'preharv_machinery',
#     'harvest_machinery',
#     'processing',
#     'chemicals',
#     'extra',
#     'labor',
#     'revenue',
#     'expenses',
#     'profit'
#     ]
# output_df = pd.DataFrame(columns=columns)


# def main():
#     maize=Budget("cfs", "maize", 200, 100)
#     maize.fert_cost(180, 40, 30, .38, .41, .31)
#     maize.seed_cost(30000, 3.19)
#     maize.preharvest_machinery_cost(3.9, 3.6, 4.6, 3.4, 4.3, 4.4, 2.7, 2.6, 4.8, 5.9, 2.0, 2.2)
#     maize.harvest_machinery_cost(13.10, 6.7, 6.3, 3.0)
#     maize.processing_cost(0.044, 0.038, 0.05, 0.17, 0.02, 0.02)
#     maize.chemicals_cost(48.36, 15.16)
#     maize.extra_costs(9.5, 219, rent=True)
#     maize.labor_cost(2, 14.25)
    #print(maize.calc_revenue(3.71))
    #print(maize.sum_expenses())
    #print(maize.calc_profit())
    #print(maize.expenses)
    
#%%
if __name__ == "__main__":
    pass
